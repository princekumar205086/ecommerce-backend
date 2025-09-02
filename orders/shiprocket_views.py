"""
ShipRocket Integration Views
Handles ShipRocket API interactions for order management
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal

from .models import Order
from shipping.models import Shipment
from shiprocket_service import shiprocket_api
from ecommerce.permissions import IsAdmin, IsSupplierOrAdmin


class ShipRocketServiceabilityView(APIView):
    """Check serviceability for delivery to a pincode"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pickup_pincode = request.data.get('pickup_pincode', '110001')
        delivery_pincode = request.data.get('delivery_pincode')
        weight = float(request.data.get('weight', 1.0))
        cod = request.data.get('cod', False)
        
        if not delivery_pincode:
            return Response(
                {'error': 'delivery_pincode is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = shiprocket_api.check_serviceability(
            pickup_pincode=pickup_pincode,
            delivery_pincode=delivery_pincode,
            weight=weight,
            cod=bool(cod)
        )
        
        return Response(result)


class ShipRocketRatesView(APIView):
    """Get shipping rates for different couriers"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pickup_pincode = request.data.get('pickup_pincode', '110001')
        delivery_pincode = request.data.get('delivery_pincode')
        weight = float(request.data.get('weight', 1.0))
        dimensions = request.data.get('dimensions', {
            'length': 10, 'breadth': 10, 'height': 5
        })
        
        if not delivery_pincode:
            return Response(
                {'error': 'delivery_pincode is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = shiprocket_api.get_shipping_rates(
            pickup_pincode=pickup_pincode,
            delivery_pincode=delivery_pincode,
            weight=weight,
            dimensions=dimensions
        )
        
        return Response(result)


class CreateShipRocketOrderView(APIView):
    """Create a ShipRocket order from an existing order"""
    permission_classes = [IsAdmin]
    
    def post(self, request):
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if shipment already exists
        try:
            shipment = Shipment.objects.get(order_id=order.order_number)
            return Response(
                {'error': 'ShipRocket order already exists', 'shipment_id': shipment.id},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Shipment.DoesNotExist:
            pass
        
        # Prepare ShipRocket order data
        shipping_address = order.shipping_address
        billing_address = order.billing_address
        
        shiprocket_data = {
            'order_id': order.order_number,
            'order_date': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'customer_name': shipping_address.get('name', order.user.full_name),
            'customer_email': order.user.email,
            'customer_phone': shipping_address.get('phone', order.user.contact),
            'billing_address': billing_address.get('address_line_1', ''),
            'billing_city': billing_address.get('city', ''),
            'billing_state': billing_address.get('state', ''),
            'billing_pincode': billing_address.get('postal_code', ''),
            'shipping_address': shipping_address.get('address_line_1', ''),
            'shipping_city': shipping_address.get('city', ''),
            'shipping_state': shipping_address.get('state', ''),
            'shipping_pincode': shipping_address.get('postal_code', ''),
            'payment_method': 'COD' if order.payment_method == 'cod' else 'Prepaid',
            'sub_total': float(order.subtotal),
            'shipping_charges': float(order.shipping_charge),
            'total_discount': float(order.discount + order.coupon_discount),
            'total_weight': 1.0,  # Default weight
            'items': []
        }
        
        # Add order items
        for item in order.items.all():
            shiprocket_data['items'].append({
                'name': item.product.name,
                'sku': item.product.sku or f'PROD{item.product.id}',
                'units': item.quantity,
                'selling_price': float(item.price),
                'discount': 0,
                'tax': 0,
                'hsn': 0
            })
        
        # Create ShipRocket order
        result = shiprocket_api.create_order(shiprocket_data)
        
        if result['success']:
            # Create shipment record
            with transaction.atomic():
                shipment = Shipment.objects.create(
                    order_id=order.order_number,
                    user=order.user,
                    shiprocket_order_id=result.get('order_id'),
                    shiprocket_shipment_id=result.get('shipment_id'),
                    customer_name=shiprocket_data['customer_name'],
                    customer_email=shiprocket_data['customer_email'],
                    customer_phone=shiprocket_data['customer_phone'],
                    pickup_address='Default Pickup Location',
                    pickup_pincode='110001',
                    delivery_address=shiprocket_data['shipping_address'],
                    delivery_city=shiprocket_data['shipping_city'],
                    delivery_state=shiprocket_data['shipping_state'],
                    delivery_pincode=shiprocket_data['shipping_pincode'],
                    weight=Decimal(str(shiprocket_data['total_weight'])),
                    length=Decimal('10'),
                    breadth=Decimal('10'),
                    height=Decimal('5'),
                    cod_amount=order.total if order.payment_method == 'cod' else Decimal('0'),
                    total_amount=order.total,
                    payment_method=shiprocket_data['payment_method'],
                    items_data=shiprocket_data['items'],
                    shiprocket_response=result.get('data', {})
                )
                
                # Update order with ShipRocket info
                order.shipping_partner = 'Shiprocket'
                order.notes = order.notes + f"\\nShipRocket order created: {result.get('order_id')}"
                order.save()
            
            return Response({
                'success': True,
                'message': 'ShipRocket order created successfully',
                'shiprocket_order_id': result.get('order_id'),
                'shiprocket_shipment_id': result.get('shipment_id'),
                'shipment_id': shipment.id
            })
        else:
            return Response({
                'success': False,
                'error': result.get('message', 'Failed to create ShipRocket order'),
                'details': result
            }, status=status.HTTP_400_BAD_REQUEST)


class TrackShipmentView(APIView):
    """Track a shipment using ShipRocket"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response(
                {'error': 'Shipment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if request.user.role not in ['admin', 'supplier'] and shipment.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not shipment.shiprocket_shipment_id:
            return Response(
                {'error': 'ShipRocket shipment ID not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get tracking info from ShipRocket
        result = shiprocket_api.track_shipment(shipment.shiprocket_shipment_id)
        
        if result['success']:
            # Update shipment with latest tracking data
            shipment.tracking_data = result['tracking_data']
            shipment.save()
            
            return Response({
                'success': True,
                'shipment': {
                    'id': shipment.id,
                    'order_id': shipment.order_id,
                    'status': shipment.status,
                    'awb_code': shipment.awb_code,
                    'courier_name': shipment.courier_name,
                    'tracking_url': shipment.get_tracking_url()
                },
                'tracking_data': result['tracking_data']
            })
        else:
            return Response({
                'success': False,
                'error': result.get('message', 'Failed to track shipment')
            }, status=status.HTTP_400_BAD_REQUEST)


class GenerateInvoiceView(APIView):
    """Generate invoice for orders using ShipRocket"""
    permission_classes = [IsAdmin]
    
    def post(self, request):
        order_ids = request.data.get('order_ids', [])
        
        if not order_ids:
            return Response(
                {'error': 'order_ids list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get ShipRocket order IDs
        shiprocket_order_ids = []
        for order_id in order_ids:
            try:
                order = Order.objects.get(id=order_id)
                shipment = Shipment.objects.get(order_id=order.order_number)
                if shipment.shiprocket_order_id:
                    shiprocket_order_ids.append(shipment.shiprocket_order_id)
            except (Order.DoesNotExist, Shipment.DoesNotExist):
                continue
        
        if not shiprocket_order_ids:
            return Response(
                {'error': 'No valid ShipRocket orders found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate invoice
        result = shiprocket_api.get_invoice(shiprocket_order_ids)
        
        return Response(result)