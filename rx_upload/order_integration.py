# rx_upload/order_integration.py
"""
Order Integration Module for RX Prescriptions
Enterprise-grade order creation from approved prescriptions
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from products.models import Product
from invoice.models import Invoice
from .models import PrescriptionUpload, VerificationActivity

User = get_user_model()
logger = logging.getLogger(__name__)


class PrescriptionOrderManager:
    """
    Manages order creation from approved prescriptions
    Handles product matching, order creation, and notifications
    """
    
    @staticmethod
    @transaction.atomic
    def create_order_from_prescription(prescription_id, medications_data=None, notes=""):
        """
        Create an order from an approved prescription
        
        Args:
            prescription_id (UUID): Prescription ID
            medications_data (list): List of medications with product mappings
                [{'medication_name': str, 'product_id': int, 'quantity': int}, ...]
            notes (str): Additional order notes
            
        Returns:
            tuple: (success: bool, message: str, order: Order or None)
        """
        try:
            # Get prescription
            prescription = PrescriptionUpload.objects.select_related('customer').get(id=prescription_id)
            
            # Validate prescription status
            if prescription.verification_status != 'approved':
                return False, "Only approved prescriptions can be converted to orders", None
            
            # Check if customer has address
            if not prescription.customer.has_address:
                return False, "Customer address is required to create order", None
            
            # Parse medications if not provided
            if not medications_data:
                medications_data = PrescriptionOrderManager._extract_medications_from_prescription(prescription)
            
            if not medications_data:
                return False, "No medications found in prescription", None
            
            # Create order
            order = Order.objects.create(
                user=prescription.customer,
                status='pending',
                payment_status='pending',
                payment_method='cod',  # Default to COD for prescription orders
                shipping_address=PrescriptionOrderManager._get_customer_address(prescription.customer),
                billing_address=PrescriptionOrderManager._get_customer_address(prescription.customer),
                notes=f"Prescription Order - {prescription.prescription_number}\n{notes}"
            )
            
            # Add order items
            total_items = 0
            for med_data in medications_data:
                product_id = med_data.get('product_id')
                quantity = med_data.get('quantity', 1)
                
                try:
                    # Use actual Product model fields: 'is_publish' indicates published products
                    product = Product.objects.get(id=product_id, is_publish=True)

                    # Check stock
                    if product.stock < quantity:
                        logger.warning(f"Insufficient stock for product {product.name}")
                        continue

                    # Create order item: prefer product.price else fallback to mrp
                    item_price = getattr(product, 'price', None) or getattr(product, 'mrp', None) or Decimal('0.00')
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=item_price
                    )

                    # Reduce stock
                    product.stock -= quantity
                    product.save()

                    total_items += 1

                except Product.DoesNotExist:
                    logger.warning(f"Product {product_id} not found or not published")
                    continue
            
            if total_items == 0:
                order.delete()
                return False, "No valid products found to create order", None
            
            # Calculate order totals
            order.calculate_totals()
            order.save()
            
            # Link prescription to order (store in notes or create relation)
            prescription.customer_notes = f"Order created: {order.order_number}"
            prescription.save()
            
            # Create verification activity
            VerificationActivity.objects.create(
                prescription=prescription,
                verifier=prescription.verified_by,
                action='created',
                description=f'Order {order.order_number} created from prescription'
            )
            
            # Generate invoice using Invoice.create_from_order
            try:
                invoice = Invoice.create_from_order(order)

                # Create invoice line items from order items
                for item in order.items.select_related('product').all():
                    invoice.line_items.create(
                        product_name=item.product.name,
                        product_description=(getattr(item.product, 'description', '') or '')[:1000],
                        quantity=item.quantity,
                        unit_price=item.price,
                        tax_rate=Decimal('10.00'),
                        discount=Decimal('0.00'),
                        total_price=item.total_price
                    )

                invoice.save()

                # Generate PDF (returns bytes or None)
                pdf_bytes = None
                try:
                    pdf_bytes = invoice.generate_pdf()
                except Exception as e:
                    logger.warning(f"Failed to generate invoice PDF: {e}")

            except Exception as e:
                logger.warning(f"Failed to generate invoice: {e}")
                invoice = None

            # Send notification email (attach invoice if available)
            PrescriptionOrderManager._send_order_confirmation_email(
                order,
                prescription,
                invoice
            )
            
            logger.info(f"✅ Order {order.order_number} created from prescription {prescription.prescription_number}")
            
            return True, f"Order {order.order_number} created successfully", order
            
        except PrescriptionUpload.DoesNotExist:
            logger.error(f"Prescription {prescription_id} not found")
            return False, "Prescription not found", None
            
        except Exception as e:
            logger.error(f"Error creating order from prescription: {str(e)}")
            return False, f"Failed to create order: {str(e)}", None
    
    @staticmethod
    def _extract_medications_from_prescription(prescription):
        """
        Extract medication data from prescription
        This is a placeholder - in production, you might use ML/OCR
        """
        medications = []
        
        # Check if prescription has medication relationships
        if hasattr(prescription, 'medications') and prescription.medications.exists():
            for med in prescription.medications.all():
                # Try to find matching product
                product = PrescriptionOrderManager._find_matching_product(med.medication_name)
                if product:
                    medications.append({
                        'medication_name': med.medication_name,
                        'product_id': product.id,
                        'quantity': med.quantity or 1
                    })
        
        # Fallback: parse medications_prescribed field
        elif prescription.medications_prescribed:
            import re
            med_lines = prescription.medications_prescribed.strip().split('\n')
            for line in med_lines:
                med_name = line.strip()
                if med_name:
                    product = PrescriptionOrderManager._find_matching_product(med_name)
                    if product:
                        medications.append({
                            'medication_name': med_name,
                            'product_id': product.id,
                            'quantity': 1
                        })
        
        return medications
    
    @staticmethod
    def _find_matching_product(medication_name):
        """
        Find product matching medication name
        Uses fuzzy matching for better results
        """
        from django.db.models import Q
        
        # Clean medication name
        clean_name = medication_name.lower().strip()
        
        # Try exact match first using published products
        product = Product.objects.filter(
            Q(name__iexact=clean_name),
            is_publish=True
        ).first()
        
        if product:
            return product
        
        # Try contains match
        product = Product.objects.filter(
            Q(name__icontains=clean_name),
            is_publish=True
        ).first()
        
        return product
    
    @staticmethod
    def _get_customer_address(customer):
        """Get customer address as JSON"""
        return {
            'full_name': customer.full_name,
            'address_line_1': customer.address_line_1 or '',
            'address_line_2': customer.address_line_2 or '',
            'city': customer.city or '',
            'state': customer.state or '',
            'postal_code': customer.postal_code or '',
            'country': customer.country or 'India',
            'phone': customer.contact or ''
        }
    
    @staticmethod
    def _generate_invoice(order, prescription):
        """Generate invoice for the order"""
        try:
            invoice = Invoice.objects.create(
                order=order,
                user=order.user,
                subtotal=order.subtotal,
                tax=order.tax,
                discount=order.discount,
                total=order.total,
                notes=f"Prescription: {prescription.prescription_number}"
            )
            
            logger.info(f"✅ Invoice {invoice.invoice_number} generated for order {order.order_number}")
            return invoice
            
        except Exception as e:
            logger.error(f"Failed to generate invoice: {str(e)}")
            return None
    
    @staticmethod
    def _send_order_confirmation_email(order, prescription, invoice=None):
        """
        Send order confirmation email with invoice attachment
        Enterprise-grade HTML email with professional styling
        """
        try:
            customer = order.user
            
            # Prepare email context
            context = {
                'customer_name': customer.full_name,
                'order_number': order.order_number,
                'prescription_number': prescription.prescription_number,
                'order_date': order.created_at,
                'order_total': order.total,
                'payment_method': order.get_payment_method_display(),
                'shipping_address': order.shipping_address,
                'order_items': order.items.select_related('product').all(),
                'invoice_number': invoice.invoice_number if invoice else None,
                'verified_by': prescription.verified_by.full_name if prescription.verified_by else 'Medical Team'
            }
            
            # HTML content
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }}
        .container {{ max-width: 650px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%); color: #ffffff; padding: 30px 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: bold; }}
        .header p {{ margin: 10px 0 0; font-size: 16px; opacity: 0.9; }}
        .content {{ padding: 30px 25px; }}
        .success-badge {{ background-color: #10b981; color: white; padding: 12px 20px; border-radius: 6px; text-align: center; margin-bottom: 25px; font-size: 18px; font-weight: bold; }}
        .info-box {{ background-color: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }}
        .info-box strong {{ color: #1e40af; }}
        .order-details {{ background-color: #f9fafb; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .order-details h3 {{ color: #2c5282; margin-top: 0; margin-bottom: 15px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
        .order-item {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #e5e7eb; }}
        .order-item:last-child {{ border-bottom: none; }}
        .order-item strong {{ color: #1f2937; }}
        .total-row {{ display: flex; justify-content: space-between; padding: 15px 0; font-size: 18px; font-weight: bold; color: #10b981; border-top: 2px solid #2c5282; margin-top: 10px; }}
        .shipping-info {{ background-color: #fffbeb; border: 1px solid #fbbf24; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .shipping-info h4 {{ color: #92400e; margin-top: 0; }}
        .btn {{ display: inline-block; background-color: #2c5282; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin: 15px 0; font-weight: bold; text-align: center; }}
        .btn:hover {{ background-color: #1e3a5f; }}
        .footer {{ background-color: #f9fafb; padding: 25px; text-align: center; border-top: 1px solid #e5e7eb; color: #6b7280; }}
        .footer a {{ color: #2c5282; text-decoration: none; font-weight: 500; }}
        .prescription-badge {{ background-color: #e0f2fe; color: #075985; padding: 6px 12px; border-radius: 4px; font-size: 14px; font-weight: 600; display: inline-block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Order Confirmed!</h1>
            <p>Your prescription order has been successfully placed</p>
        </div>
        
        <div class="content">
            <div class="success-badge">
                ✅ Your RX Order is Confirmed & Will be Delivered Soon!
            </div>
            
            <p>Dear <strong>{customer.full_name}</strong>,</p>
            
            <p>Thank you for ordering with MedixMall! Your prescription has been verified by our medical team, and your order is being prepared for delivery.</p>
            
            <div class="info-box">
                <strong>Order Number:</strong> #{order.order_number}<br>
                <strong>Prescription Number:</strong> <span class="prescription-badge">{prescription.prescription_number}</span><br>
                <strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y at %I:%M %p')}<br>
                {f'<strong>Invoice Number:</strong> {invoice.invoice_number}<br>' if invoice else ''}
                <strong>Verified by:</strong> Dr. {context['verified_by']}
            </div>
            
            <div class="order-details">
                <h3>📦 Order Items</h3>
"""
            
            # Add order items
            for item in context['order_items']:
                html_content += f"""
                <div class="order-item">
                    <div>
                        <strong>{item.product.name}</strong><br>
                        <span style="color: #6b7280; font-size: 14px;">Quantity: {item.quantity}</span>
                    </div>
                    <div style="text-align: right;">
                        <strong>₹{item.total_price}</strong>
                    </div>
                </div>
"""
            
            html_content += f"""
                <div class="total-row">
                    <span>Total Amount:</span>
                    <span>₹{order.total}</span>
                </div>
            </div>
            
            <div class="shipping-info">
                <h4>🚚 Delivery Address</h4>
                <p style="margin: 5px 0;">
                    {order.shipping_address.get('address_line_1', '')}<br>
                    {order.shipping_address.get('address_line_2', '')}<br>
                    {order.shipping_address.get('city', '')}, {order.shipping_address.get('state', '')} {order.shipping_address.get('postal_code', '')}<br>
                    {order.shipping_address.get('country', 'India')}
                </p>
            </div>
            
            <div style="text-align: center; margin: 25px 0;">
                <a href="https://backend.okpuja.in/api/orders/{order.id}/" class="btn">Track Your Order</a>
            </div>
            
            <div class="info-box" style="background-color: #fef3c7; border-left-color: #f59e0b;">
                <strong>💡 What's Next?</strong><br>
                • Your order is being processed<br>
                • You'll receive a tracking number once shipped<br>
                • Expected delivery: 3-5 business days<br>
                • Payment method: {order.get_payment_method_display()}
            </div>
            
            <p style="margin-top: 25px;">If you have any questions about your order, please don't hesitate to contact our support team.</p>
        </div>
        
        <div class="footer">
            <p><strong>Need Help?</strong></p>
            <p>
                📧 Email: <a href="mailto:support@medixmall.com">support@medixmall.com</a><br>
                📞 Phone: +91 8002-8002-80<br>
                💬 Live Chat: <a href="https://backend.okpuja.in">backend.okpuja.in</a>
            </p>
            <p style="margin-top: 20px; font-size: 14px;">
                Thank you for choosing MedixMall!<br>
                <a href="https://backend.okpuja.in">Visit our website</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
            
            # Plain text version
            plain_message = f"""
🎉 Order Confirmed! Your RX Order Will be Delivered Soon

Dear {customer.full_name},

Thank you for ordering with MedixMall! Your prescription has been verified by our medical team, and your order is being prepared for delivery.

Order Details:
- Order Number: #{order.order_number}
- Prescription Number: {prescription.prescription_number}
- Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}
{f'- Invoice Number: {invoice.invoice_number}' if invoice else ''}
- Verified by: Dr. {context['verified_by']}

Order Items:
"""
            
            for item in context['order_items']:
                plain_message += f"• {item.product.name} (Qty: {item.quantity}) - ₹{item.total_price}\n"
            
            plain_message += f"""
Total Amount: ₹{order.total}

Delivery Address:
{order.shipping_address.get('address_line_1', '')}
{order.shipping_address.get('address_line_2', '')}
{order.shipping_address.get('city', '')}, {order.shipping_address.get('state', '')} {order.shipping_address.get('postal_code', '')}
{order.shipping_address.get('country', 'India')}

What's Next?
• Your order is being processed
• You'll receive a tracking number once shipped
• Expected delivery: 3-5 business days
• Payment method: {order.get_payment_method_display()}

Track Your Order: https://backend.okpuja.in/api/orders/{order.id}/

Need Help?
Email: support@medixmall.com
Phone: +91 8002-8002-80

Thank you for choosing MedixMall!
Visit our website: https://backend.okpuja.in
"""
            
            # Create email
            email = EmailMultiAlternatives(
                subject=f'✅ Order Confirmed - {order.order_number} | MedixMall',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer.email]
            )
            
            email.attach_alternative(html_content, "text/html")
            
            # Attach invoice PDF if available
            if invoice and hasattr(invoice, 'generate_pdf'):
                try:
                    pdf_content = invoice.generate_pdf()
                    email.attach(f'Invoice_{invoice.invoice_number}.pdf', pdf_content, 'application/pdf')
                except Exception as pdf_error:
                    logger.warning(f"Failed to attach invoice PDF: {str(pdf_error)}")
            
            # Send email
            email.send(fail_silently=False)
            
            logger.info(f"✅ Order confirmation email sent to {customer.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {str(e)}")
            return False
    
    @staticmethod
    def get_prescription_orders(prescription_id):
        """Get all orders related to a prescription"""
        try:
            prescription = PrescriptionUpload.objects.get(id=prescription_id)
            # Parse customer_notes to find order numbers
            orders = Order.objects.filter(
                user=prescription.customer,
                notes__icontains=prescription.prescription_number
            ).order_by('-created_at')
            
            return orders
            
        except PrescriptionUpload.DoesNotExist:
            return Order.objects.none()
