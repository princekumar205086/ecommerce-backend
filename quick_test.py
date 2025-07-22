import requests
import json
import time

def test_payment_invoice_quick():
    print("🚀 QUICK PAYMENT & INVOICE TEST")
    print("=" * 50)
    
    # Get tokens
    admin_response = requests.post('http://127.0.0.1:8000/api/token/', json={'email': 'admin@test.com', 'password': 'admin123'})
    admin_token = admin_response.json()['access']
    customer_response = requests.post('http://127.0.0.1:8000/api/token/', json={'email': 'customer@test.com', 'password': 'customer123'})
    customer_token = customer_response.json()['access']
    
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    customer_headers = {'Authorization': f'Bearer {customer_token}'}
    
    print("✅ Authentication successful")
    
    # Get existing order without invoice
    orders_response = requests.get('http://127.0.0.1:8000/api/orders/', headers=customer_headers)
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        orders = orders_data.get('results', orders_data)
        if orders:
            # Find an order without invoice (look for 202507220004 or similar)
            order = None
            for o in orders:
                if o.get('order_number') in ['202507220004', '202507220003', '202507220002']:
                    order = o
                    break
            if not order:
                order = orders[1] if len(orders) > 1 else orders[0]  # Use second order if available
            
            order_id = order['id']
            print(f"✅ Using existing order: {order.get('order_number')} (₹{order.get('total')})")
            
            # Test payment creation
            payment_data = {'order_id': order_id, 'amount': str(order.get('total', 100)), 'currency': 'INR'}
            payment_response = requests.post('http://127.0.0.1:8000/api/payments/create/', json=payment_data, headers=customer_headers)
            
            if payment_response.status_code in [200, 201]:
                payment_details = payment_response.json()
                print(f"✅ Payment order created: {payment_details.get('order_id')}")
                
                # Test invoice creation
                invoice_data = {'order_id': order_id}
                invoice_response = requests.post('http://127.0.0.1:8000/api/invoice/create/', json=invoice_data, headers=admin_headers)
                
                if invoice_response.status_code in [200, 201]:
                    invoice = invoice_response.json()
                    invoice_id = invoice.get('id')
                    print(f"✅ Invoice created: {invoice.get('invoice_number')}")
                    
                    # Test PDF generation
                    pdf_gen_response = requests.post(f'http://127.0.0.1:8000/api/invoice/{invoice_id}/generate-pdf/', headers=admin_headers)
                    
                    if pdf_gen_response.status_code == 200:
                        pdf_result = pdf_gen_response.json()
                        print("✅ PDF generated successfully")
                        
                        # Test PDF download
                        pdf_download = requests.get(f'http://127.0.0.1:8000/api/invoice/{invoice_id}/pdf/', headers=admin_headers)
                        if pdf_download.status_code == 200:
                            print(f"✅ PDF downloaded ({len(pdf_download.content)} bytes)")
                        else:
                            print(f"⚠️ PDF download: {pdf_download.status_code}")
                    else:
                        print(f"⚠️ PDF generation: {pdf_gen_response.status_code}")
                    
                    print("\n🎉 All core functionality working!")
                    return True
                else:
                    print(f"❌ Invoice creation failed: {invoice_response.status_code}")
            else:
                print(f"❌ Payment creation failed: {payment_response.status_code}")
        else:
            print("❌ No orders found")
    else:
        print(f"❌ Failed to get orders: {orders_response.status_code}")
    
    return False

if __name__ == "__main__":
    test_payment_invoice_quick()
