# rx_upload/customer_views.py
"""
Customer-facing views for prescription upload flow
Aligned with frontend requirements from screenshots
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import PrescriptionUpload, PrescriptionMedication
from .serializers import PrescriptionUploadSerializer


# Sample delivery addresses structure (in production, this would come from user profile or a separate Address app)
def get_user_addresses(user):
    """
    Get user's saved delivery addresses
    In production, integrate with your existing address management system
    """
    # For now, return a sample address structure
    # You can extend this to fetch from your database or user profile
    return [
        {
            'id': 1,
            'type': 'home',
            'full_name': user.full_name,
            'phone': user.contact or '1234567890',
            'address_line_1': 'Rohini, Sector 5',
            'address_line_2': '',
            'city': 'Purnia',
            'state': 'Bihar',
            'postal_code': '854301',
            'country': 'India',
            'is_default': True,
            'formatted_address': 'Rohini, Sector 5, Purnia, Bihar - 854301'
        }
    ]


# ========================
# CUSTOMER PRESCRIPTION ORDER FLOW
# ========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_prescription(request):
    """
    Step 1: Upload prescription file(s)
    POST /api/rx-upload/customer/upload/
    
    Request:
    - multipart/form-data with file field
    - Supports: JPEG, PNG, PDF (max 10MB)
    
    Response:
    {
        "success": true,
        "message": "Prescription uploaded successfully",
        "data": {
            "prescription_id": "uuid",
            "prescription_number": "RX20250105...",
            "prescription_image": "https://imagekit.io/...",
            "original_filename": "prescription.jpg",
            "uploaded_at": "2025-01-05T10:00:00Z"
        }
    }
    """
    try:
        # Check if file is provided
        if 'prescription_file' not in request.FILES:
            return Response({
                'success': False,
                'message': 'Please upload a prescription file',
                'errors': {'prescription_file': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare data for serializer
        data = {
            'prescription_file': request.FILES['prescription_file'],
            'customer': request.user.id,
            'verification_status': 'pending'
        }
        
        # Create prescription
        serializer = PrescriptionUploadSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            prescription = serializer.save(customer=request.user)
            
            return Response({
                'success': True,
                'message': 'Prescription uploaded successfully',
                'data': {
                    'prescription_id': str(prescription.id),
                    'prescription_number': prescription.prescription_number,
                    'prescription_image': prescription.prescription_image,
                    'original_filename': prescription.original_filename,
                    'file_size': prescription.file_size,
                    'uploaded_at': prescription.uploaded_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': 'Failed to upload prescription',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Upload failed: {str(e)}',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_patient_information(request, prescription_id):
    """
    Step 2: Add patient information
    POST /api/rx-upload/customer/{prescription_id}/patient-info/
    
    Request Body:
    {
        "patient_name": "John Doe",
        "customer_phone": "1234567890",
        "patient_age": 30,
        "patient_gender": "male",
        "email": "patient@example.com (optional)",
        "date_of_birth": "dd-mm-yyyy (optional)",
        "emergency_contact": "9876543210 (optional)"
    }
    
    Response:
    {
        "success": true,
        "message": "Patient information saved successfully",
        "data": {...}
    }
    """
    try:
        prescription = get_object_or_404(
            PrescriptionUpload, 
            id=prescription_id, 
            customer=request.user
        )
        
        # Validate required fields
        patient_name = request.data.get('patient_name', '').strip()
        customer_phone = request.data.get('customer_phone', '').strip()
        
        if not patient_name:
            return Response({
                'success': False,
                'message': 'Patient name is required',
                'errors': {'patient_name': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not customer_phone:
            return Response({
                'success': False,
                'message': 'Phone number is required',
                'errors': {'customer_phone': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate phone number (10 digits)
        if not customer_phone.isdigit() or len(customer_phone) != 10:
            return Response({
                'success': False,
                'message': 'Please enter a valid 10-digit mobile number',
                'errors': {'customer_phone': ['Enter a valid 10-digit mobile number.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update prescription with patient information
        prescription.patient_name = patient_name
        prescription.customer_phone = customer_phone
        prescription.patient_age = request.data.get('patient_age')
        prescription.patient_gender = request.data.get('patient_gender')
        prescription.alternative_contact = request.data.get('emergency_contact')
        prescription.customer_notes = request.data.get('customer_notes', '')
        
        prescription.save()
        
        return Response({
            'success': True,
            'message': 'Patient information saved successfully',
            'data': {
                'prescription_id': str(prescription.id),
                'patient_name': prescription.patient_name,
                'customer_phone': prescription.customer_phone,
                'patient_age': prescription.patient_age,
                'patient_gender': prescription.patient_gender,
                'alternative_contact': prescription.alternative_contact
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to save patient information: {str(e)}',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_delivery_addresses(request):
    """
    Step 3: Get user's delivery addresses
    GET /api/rx-upload/customer/addresses/
    
    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "type": "home",
                "full_name": "Admin User",
                "phone": "1234567890",
                "address_line_1": "Rohini, Sector 5",
                "address_line_2": "",
                "city": "Purnia",
                "state": "Bihar",
                "postal_code": "854301",
                "country": "India",
                "is_default": true,
                "formatted_address": "Rohini, Sector 5, Purnia, Bihar - 854301"
            }
        ]
    }
    """
    try:
        # Get addresses using helper function
        addresses = get_user_addresses(request.user)
        
        return Response({
            'success': True,
            'data': addresses
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to fetch addresses: {str(e)}',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_delivery_options(request):
    """
    Get delivery options and pricing
    GET /api/rx-upload/customer/delivery-options/
    
    Response:
    {
        "success": true,
        "data": {
            "options": [
                {
                    "id": "express",
                    "name": "Express Delivery",
                    "description": "Get your medicines within 2-4 hours",
                    "price": 99.00,
                    "estimated_delivery": "2-4 hours"
                },
                {
                    "id": "standard",
                    "name": "Standard Delivery",
                    "description": "Get your medicines within 24 hours",
                    "price": 49.00,
                    "estimated_delivery": "24 hours"
                },
                {
                    "id": "free",
                    "name": "Free Delivery",
                    "description": "Get your medicines within 2-3 days",
                    "price": 0.00,
                    "estimated_delivery": "2-3 days"
                }
            ]
        }
    }
    """
    return Response({
        'success': True,
        'data': {
            'options': [
                {
                    'id': 'express',
                    'name': 'Express Delivery',
                    'description': 'Get your medicines within 2-4 hours',
                    'price': 99.00,
                    'estimated_delivery': '2-4 hours',
                    'icon': 'flash'
                },
                {
                    'id': 'standard',
                    'name': 'Standard Delivery',
                    'description': 'Get your medicines within 24 hours',
                    'price': 49.00,
                    'estimated_delivery': '24 hours',
                    'icon': 'truck'
                },
                {
                    'id': 'free',
                    'name': 'Free Delivery',
                    'description': 'Get your medicines within 2-3 days',
                    'price': 0.00,
                    'estimated_delivery': '2-3 days',
                    'icon': 'gift'
                }
            ]
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_prescription_order(request, prescription_id):
    """
    Step 4: Submit complete prescription order
    POST /api/rx-upload/customer/{prescription_id}/submit/
    
    Request Body:
    {
        "delivery_address_id": 1,
        "delivery_option": "express|standard|free",
        "payment_method": "cod|online",
        "customer_notes": "Optional notes"
    }
    
    Response:
    {
        "success": true,
        "message": "Prescription order submitted successfully",
        "data": {
            "order_id": "RX20250105...",
            "prescription_id": "uuid",
            "delivery_charge": 99.00,
            "status": "pending_verification",
            "estimated_delivery": "2-4 hours",
            "message": "Your prescription is being verified by our pharmacist. You will be contacted once verification is complete."
        }
    }
    """
    try:
        prescription = get_object_or_404(
            PrescriptionUpload, 
            id=prescription_id, 
            customer=request.user
        )
        
        # Validate required fields
        delivery_address_id = request.data.get('delivery_address_id')
        delivery_option = request.data.get('delivery_option')
        
        if not delivery_address_id:
            return Response({
                'success': False,
                'message': 'Please select a delivery address',
                'errors': {'delivery_address_id': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not delivery_option:
            return Response({
                'success': False,
                'message': 'Please select a delivery option',
                'errors': {'delivery_option': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate delivery option
        valid_options = ['express', 'standard', 'free']
        if delivery_option not in valid_options:
            return Response({
                'success': False,
                'message': 'Invalid delivery option',
                'errors': {'delivery_option': ['Choose from: express, standard, free']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate address - simple validation that ID exists in user's addresses
        user_addresses = get_user_addresses(request.user)
        address_found = None
        for addr in user_addresses:
            if addr['id'] == delivery_address_id:
                address_found = addr
                break
        
        if not address_found:
            return Response({
                'success': False,
                'message': 'Invalid delivery address',
                'errors': {'delivery_address_id': ['Address not found.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate delivery charge
        delivery_charges = {
            'express': Decimal('99.00'),
            'standard': Decimal('49.00'),
            'free': Decimal('0.00')
        }
        delivery_charge = delivery_charges[delivery_option]
        
        # Get estimated delivery time
        delivery_times = {
            'express': '2-4 hours',
            'standard': '24 hours',
            'free': '2-3 days'
        }
        estimated_delivery = delivery_times[delivery_option]
        
        # Store order information in prescription's customer_notes as JSON
        import json
        order_details = {
            'delivery_address_id': delivery_address_id,
            'delivery_address': address_found,
            'delivery_option': delivery_option,
            'delivery_charge': str(delivery_charge),
            'estimated_delivery': estimated_delivery,
            'payment_method': request.data.get('payment_method', 'cod'),
            'submitted_at': timezone.now().isoformat()
        }
        
        # Update prescription
        existing_notes = prescription.customer_notes or ''
        prescription.customer_notes = json.dumps(order_details)
        prescription.verification_status = 'pending'
        prescription.priority_level = 3 if delivery_option == 'express' else 2
        prescription.is_urgent = delivery_option == 'express'
        prescription.save()
        
        return Response({
            'success': True,
            'message': 'Prescription order submitted successfully',
            'data': {
                'order_id': prescription.prescription_number,
                'prescription_id': str(prescription.id),
                'delivery_charge': float(delivery_charge),
                'estimated_delivery': estimated_delivery,
                'status': 'pending_verification',
                'message': 'Your prescription is being verified by our pharmacist. You will be contacted once verification is complete.',
                'contact_info': {
                    'phone': prescription.customer_phone,
                    'email': request.user.email
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to submit order: {str(e)}',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_order_summary(request, prescription_id):
    """
    Get order summary for review before submission
    GET /api/rx-upload/customer/{prescription_id}/summary/
    
    Response:
    {
        "success": true,
        "data": {
            "prescription_files": 1,
            "patient": "John Doe",
            "delivery_address": "home address",
            "delivery_option": "Not selected",
            "prescription_image": "https://...",
            "can_submit": false,
            "missing_fields": ["delivery_address", "delivery_option"]
        }
    }
    """
    try:
        prescription = get_object_or_404(
            PrescriptionUpload, 
            id=prescription_id, 
            customer=request.user
        )
        
        # Check what's completed
        has_prescription = bool(prescription.prescription_image)
        has_patient_info = bool(prescription.patient_name and prescription.customer_phone)
        
        # Parse order details if exists
        delivery_info = None
        if prescription.customer_notes:
            try:
                import json
                order_details = json.loads(prescription.customer_notes)
                if 'delivery_address' in order_details:
                    addr = order_details['delivery_address']
                    delivery_info = f"{addr['address_line_1']}, {addr['city']}, {addr['state']}"
            except:
                pass
        
        # Determine missing fields
        missing_fields = []
        if not has_prescription:
            missing_fields.append('prescription_file')
        if not has_patient_info:
            missing_fields.append('patient_information')
        if not delivery_info:
            missing_fields.append('delivery_address')
        
        can_submit = len(missing_fields) == 0
        
        return Response({
            'success': True,
            'data': {
                'prescription_id': str(prescription.id),
                'prescription_number': prescription.prescription_number,
                'prescription_files': 1 if has_prescription else 0,
                'prescription_image': prescription.prescription_image,
                'patient': prescription.patient_name if has_patient_info else 'Not specified',
                'patient_phone': prescription.customer_phone if has_patient_info else None,
                'delivery_address': delivery_info if delivery_info else 'Not selected',
                'verification_status': prescription.verification_status,
                'can_submit': can_submit,
                'missing_fields': missing_fields,
                'uploaded_at': prescription.uploaded_at.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to fetch order summary: {str(e)}',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_prescriptions(request):
    """
    Get customer's prescription order history
    GET /api/rx-upload/customer/my-prescriptions/
    
    Response:
    {
        "success": true,
        "data": [
            {
                "prescription_id": "uuid",
                "prescription_number": "RX...",
                "patient_name": "John Doe",
                "verification_status": "pending",
                "uploaded_at": "2025-01-05T10:00:00Z",
                "prescription_image": "https://..."
            }
        ]
    }
    """
    try:
        prescriptions = PrescriptionUpload.objects.filter(
            customer=request.user
        ).order_by('-uploaded_at')
        
        prescriptions_data = []
        for rx in prescriptions:
            prescriptions_data.append({
                'prescription_id': str(rx.id),
                'prescription_number': rx.prescription_number,
                'patient_name': rx.patient_name or 'Not specified',
                'verification_status': rx.verification_status,
                'verification_status_display': dict(PrescriptionUpload.VERIFICATION_STATUS).get(rx.verification_status),
                'uploaded_at': rx.uploaded_at.isoformat(),
                'prescription_image': rx.prescription_image,
                'is_urgent': rx.is_urgent
            })
        
        return Response({
            'success': True,
            'data': prescriptions_data,
            'count': len(prescriptions_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to fetch prescriptions: {str(e)}',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
