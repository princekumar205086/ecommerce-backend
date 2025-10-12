"""
COD Confirmation Test and Fix
Tests the /api/payments/confirm-cod/ endpoint to identify and fix the issue
"""

import requests
import json

# Configuration
BASE_URL = 'http://localhost:8000/api'
TEST_EMAIL = 'user@example.com'
TEST_PASSWORD = 'User@123'

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
ENDC = '\033[0m'

def log_success(msg):
    print(f"{GREEN}✓ {msg}{ENDC}")

def log_error(msg):
    print(f"{RED}✗ {msg}{ENDC}")

def log_info(msg):
    print(f"{BLUE}ℹ {msg}{ENDC}")

def log_section(msg):
    print(f"\n{BOLD}{BLUE}{'='*60}{ENDC}")
    print(f"{BOLD}{BLUE}{msg}{ENDC}")
    print(f"{BOLD}{BLUE}{'='*60}{ENDC}")

def test_cod_flow():
    """Test complete COD flow including confirmation"""
    
    log_section("🚛 COD PAYMENT FLOW TEST")
    
    # Step 1: Authentication
    log_info("Step 1: User Authentication")
    auth_response = requests.post(f"{BASE_URL}/token/", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if auth_response.status_code != 200:
        log_error("Authentication failed")
        return False
    
    token = auth_response.json()['access']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    log_success("✅ Authentication successful")
    
    # Step 2: Setup cart
    log_info("Step 2: Cart Setup")
    requests.delete(f"{BASE_URL}/cart/clear/", headers=headers)
    
    # Get test product
    products_response = requests.get(f"{BASE_URL}/products/products/?search=Omega", headers=headers)
    products = products_response.json()['results']
    product = products[0]
    
    # Add to cart
    cart_payload = {"product_id": product['id'], "quantity": 1}
    if product.get('variants'):
        cart_payload["variant_id"] = product['variants'][0]['id']
    
    requests.post(f"{BASE_URL}/cart/add/", json=cart_payload, headers=headers)
    cart_response = requests.get(f"{BASE_URL}/cart/", headers=headers)
    cart_data = cart_response.json()
    
    log_success(f"✅ Cart setup complete - Total: ₹{cart_data['total_price']}")
    
    # Step 3: Create COD payment
    log_info("Step 3: Creating COD Payment")
    
    shipping_address = {
        "full_name": "John Doe",
        "phone": "9876543210",
        "address_line_1": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "country": "India"
    }
    
    payment_payload = {
        "cart_id": cart_data['id'],
        "payment_method": "cod",
        "shipping_address": shipping_address,
        "coupon_code": "MEDIXMALL10",
        "currency": "INR",
        "cod_notes": "Please call before delivery"
    }
    
    payment_response = requests.post(f"{BASE_URL}/payments/create-from-cart/", 
                                   json=payment_payload, headers=headers)
    
    if payment_response.status_code != 200:
        log_error(f"COD payment creation failed: {payment_response.text}")
        return False
    
    payment_data = payment_response.json()
    payment_id = payment_data['payment_id']
    
    log_success(f"✅ COD payment created - ID: {payment_id}")
    log_info(f"   - Amount: ₹{payment_data['amount']}")
    log_info(f"   - Next Step: {payment_data.get('next_step', 'N/A')}")
    
    # Step 4: Get payment details to check method
    log_info("Step 4: Checking Payment Details")
    payment_detail_response = requests.get(f"{BASE_URL}/payments/{payment_id}/", headers=headers)
    
    if payment_detail_response.status_code == 200:
        payment_details = payment_detail_response.json()
        log_info(f"   - Payment Method in DB: {payment_details.get('payment_method')}")
        log_info(f"   - Payment Status: {payment_details.get('status')}")
    else:
        log_warning("Could not fetch payment details")
    
    # Step 5: Test COD confirmation
    log_info("Step 5: Testing COD Confirmation")
    
    cod_confirm_payload = {
        "payment_id": payment_id,
        "cod_notes": "Updated COD notes - confirmed"
    }
    
    confirm_response = requests.post(f"{BASE_URL}/payments/confirm-cod/", 
                                   json=cod_confirm_payload, headers=headers)
    
    log_info(f"COD Confirmation Response Status: {confirm_response.status_code}")
    log_info(f"COD Confirmation Response: {confirm_response.text}")
    
    if confirm_response.status_code == 200:
        confirm_data = confirm_response.json()
        log_success("✅ COD confirmation successful!")
        
        if confirm_data.get('order_created'):
            log_success(f"✅ Order created: #{confirm_data['order']['order_number']}")
            log_info(f"   - Order ID: {confirm_data['order']['id']}")
            log_info(f"   - Order Status: {confirm_data['order']['status']}")
            log_info(f"   - Payment Status: {confirm_data['order']['payment_status']}")
            log_info(f"   - Order Total: ₹{confirm_data['order']['total']}")
        
        return True
    else:
        log_error(f"❌ COD confirmation failed")
        try:
            error_data = confirm_response.json()
            log_error(f"   Error: {error_data}")
            
            # Check if it's the specific error we're fixing
            if 'payment_id' in error_data and 'Payment is not COD' in str(error_data['payment_id']):
                log_error("🐛 IDENTIFIED BUG: Payment method validation failing")
                log_info("   This means the payment_method field is not being set correctly")
                return False
        except:
            log_error(f"   Raw error: {confirm_response.text}")
        
        return False

if __name__ == "__main__":
    print(f"{BOLD}COD CONFIRMATION ENDPOINT TEST{ENDC}")
    print(f"{BOLD}================================{ENDC}")
    
    try:
        success = test_cod_flow()
        
        if success:
            log_section("🎉 COD FLOW TEST SUCCESSFUL!")
            log_success("✅ COD payment creation working")
            log_success("✅ COD confirmation working")
            log_success("✅ Order creation from COD working")
            log_success("🚀 COD system fully operational!")
        else:
            log_section("❌ COD FLOW TEST FAILED")
            log_error("Issues found in COD confirmation process")
            log_info("Check the error details above and fix the implementation")
            
    except Exception as e:
        log_error(f"💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()