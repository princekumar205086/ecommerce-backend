# rx_upload/views.py
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .models import PrescriptionUpload, VerificationActivity, VerifierWorkload, PrescriptionMedication
from .optimizations import RXSystemOptimizer, RXDatabaseOptimizer
from .order_integration import PrescriptionOrderManager
from .serializers import (
    PrescriptionUploadSerializer, 
    PrescriptionVerificationSerializer,
    VerificationActivitySerializer,
    VerifierWorkloadSerializer,
    PrescriptionMedicationSerializer,
    RXVerifierLoginSerializer
)
from ecommerce.permissions import (
    IsRXVerifier, 
    IsRXVerifierOrAdmin, 
    IsOwnerOrRXVerifierOrAdmin,
    CanVerifyPrescription
)

User = get_user_model()


class PrescriptionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ========================
# RX VERIFIER AUTHENTICATION VIEWS
# ========================

@api_view(['POST'])
@permission_classes([])
def rx_verifier_login(request):
    """
    RX Verifier specific login endpoint
    POST /api/rx-upload/auth/login/
    """
    serializer = RXVerifierLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid input data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    # Authenticate user
    user = authenticate(request, username=email, password=password)
    
    if not user:
        return Response({
            'success': False,
            'message': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user is RX verifier
    if user.role != 'rx_verifier':
        return Response({
            'success': False,
            'message': 'Access denied. RX Verifier privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if not user.is_active:
        return Response({
            'success': False,
            'message': 'Account is inactive. Please contact administrator.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Login user
    login(request, user)
    
    # Get or create workload stats
    workload, created = VerifierWorkload.objects.get_or_create(
        verifier=user,
        defaults={'is_available': True, 'max_daily_capacity': 50}
    )
    
    # Update workload
    workload.update_workload()
    
    return Response({
        'success': True,
        'message': f'Welcome back, {user.full_name}!',
        'data': {
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'last_login': user.last_login
            },
            'workload': {
                'pending_count': workload.pending_count,
                'in_review_count': workload.in_review_count,
                'total_verified': workload.total_verified,
                'approval_rate': workload.approval_rate,
                'is_available': workload.is_available,
                'can_accept_more': workload.can_accept_more
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsRXVerifier])
def rx_verifier_logout(request):
    """
    RX Verifier logout endpoint
    POST /api/rx-upload/auth/logout/
    """
    logout(request)
    return Response({
        'success': True,
        'message': 'Logged out successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsRXVerifier])
def rx_verifier_profile(request):
    """
    Get RX Verifier profile and workload information
    GET /api/rx-upload/auth/profile/
    """
    user = request.user
    workload = get_object_or_404(VerifierWorkload, verifier=user)
    workload.update_workload()
    
    return Response({
        'success': True,
        'data': {
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'contact': user.contact,
                'role': user.role,
                'date_joined': user.date_joined,
                'last_login': user.last_login
            },
            'workload': VerifierWorkloadSerializer(workload).data
        }
    }, status=status.HTTP_200_OK)


# ========================
# PRESCRIPTION UPLOAD VIEWS
# ========================

class PrescriptionUploadListCreateView(generics.ListCreateAPIView):
    """
    List all prescriptions or create new prescription
    GET/POST /api/rx-upload/prescriptions/
    """
    serializer_class = PrescriptionUploadSerializer
    pagination_class = PrescriptionPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verification_status', 'is_urgent', 'priority_level', 'verified_by']
    search_fields = ['prescription_number', 'patient_name', 'doctor_name', 'hospital_clinic']
    ordering_fields = ['uploaded_at', 'verification_date', 'priority_level']
    ordering = ['-uploaded_at']
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            # Customers can upload prescriptions
            self.permission_classes = [IsAuthenticated]
        else:
            # Everyone can list (but queryset is filtered by user type)
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        
        # Get filters from request
        filters = {}
        for param in ['verification_status', 'is_urgent', 'verified_by', 'assigned_to_me']:
            value = self.request.query_params.get(param)
            if value:
                filters[param] = value
        
        # Use optimized query method
        return RXDatabaseOptimizer.get_optimized_prescription_list(user, filters)
    
    def perform_create(self, serializer):
        # Set customer to current user
        serializer.save(customer=self.request.user)


class PrescriptionUploadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific prescription
    GET/PUT/DELETE /api/rx-upload/prescriptions/{id}/
    """
    serializer_class = PrescriptionUploadSerializer
    permission_classes = [IsOwnerOrRXVerifierOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['rx_verifier', 'admin']:
            return PrescriptionUpload.objects.all()
        else:
            return PrescriptionUpload.objects.filter(customer=user)


# ========================
# PRESCRIPTION VERIFICATION VIEWS
# ========================

@api_view(['POST'])
@permission_classes([CanVerifyPrescription])
def assign_prescription(request, prescription_id):
    """
    Assign prescription to current verifier
    POST /api/rx-upload/prescriptions/{id}/assign/
    """
    prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
    
    if not prescription.can_be_verified:
        return Response({
            'success': False,
            'message': 'Prescription cannot be assigned in current status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check verifier workload
    workload = get_object_or_404(VerifierWorkload, verifier=request.user)
    if not workload.can_accept_more:
        return Response({
            'success': False,
            'message': 'You have reached maximum workload capacity'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = prescription.assign_to_verifier(request.user)
    
    if success:
        # Create activity log
        VerificationActivity.objects.create(
            prescription=prescription,
            verifier=request.user,
            action='assigned',
            description=f'Prescription assigned to {request.user.full_name}'
        )
        
        # Update workload
        workload.update_workload()
        
        return Response({
            'success': True,
            'message': message,
            'data': PrescriptionUploadSerializer(prescription).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([CanVerifyPrescription])
def approve_prescription(request, prescription_id):
    """
    Approve prescription
    POST /api/rx-upload/prescriptions/{id}/approve/
    Body: { "notes": "Optional verification notes" }
    """
    prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
    notes = request.data.get('notes', '')
    
    success, message = prescription.approve_prescription(request.user, notes)
    
    if success:
        # Create activity log
        VerificationActivity.objects.create(
            prescription=prescription,
            verifier=request.user,
            action='approved',
            description=f'Prescription approved by {request.user.full_name}'
        )
        
        # Update verifier workload
        workload = get_object_or_404(VerifierWorkload, verifier=request.user)
        workload.update_workload()
        
        return Response({
            'success': True,
            'message': message,
            'data': PrescriptionUploadSerializer(prescription).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([CanVerifyPrescription])
def reject_prescription(request, prescription_id):
    """
    Reject prescription
    POST /api/rx-upload/prescriptions/{id}/reject/
    Body: { "notes": "Required rejection reason" }
    """
    prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
    notes = request.data.get('notes', '')
    
    if not notes:
        return Response({
            'success': False,
            'message': 'Rejection reason is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = prescription.reject_prescription(request.user, notes)
    
    if success:
        # Create activity log
        VerificationActivity.objects.create(
            prescription=prescription,
            verifier=request.user,
            action='rejected',
            description=f'Prescription rejected by {request.user.full_name}: {notes[:100]}'
        )
        
        # Update verifier workload
        workload = get_object_or_404(VerifierWorkload, verifier=request.user)
        workload.update_workload()
        
        return Response({
            'success': True,
            'message': message,
            'data': PrescriptionUploadSerializer(prescription).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([CanVerifyPrescription])
def request_clarification(request, prescription_id):
    """
    Request clarification from customer
    POST /api/rx-upload/prescriptions/{id}/clarification/
    Body: { "message": "Clarification request message" }
    """
    prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
    message = request.data.get('message', '')
    
    if not message:
        return Response({
            'success': False,
            'message': 'Clarification message is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, response_message = prescription.request_clarification(request.user, message)
    
    if success:
        # Create activity log
        VerificationActivity.objects.create(
            prescription=prescription,
            verifier=request.user,
            action='clarification_requested',
            description=f'Clarification requested by {request.user.full_name}'
        )
        
        return Response({
            'success': True,
            'message': response_message,
            'data': PrescriptionUploadSerializer(prescription).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': response_message
        }, status=status.HTTP_400_BAD_REQUEST)


# ========================
# DASHBOARD AND ANALYTICS VIEWS
# ========================

@api_view(['GET'])
@permission_classes([IsRXVerifierOrAdmin])
def verification_dashboard(request):
    """
    Get verification dashboard data with caching optimization
    GET /api/rx-upload/dashboard/
    """
    user = request.user
    
    # Use cached dashboard stats for better performance
    dashboard_stats = RXSystemOptimizer.get_cached_dashboard_stats(
        user_role=user.role,
        verifier_id=user.id if user.role == 'rx_verifier' else None
    )
    
    # Recent activity
    if user.role == 'rx_verifier':
        recent_activities = VerificationActivity.objects.filter(
            verifier=user
        ).select_related('prescription', 'verifier').order_by('-timestamp')[:10]
    else:
        recent_activities = VerificationActivity.objects.select_related(
            'prescription', 'verifier'
        ).order_by('-timestamp')[:10]
    
    # Performance metrics for verifier
    if user.role == 'rx_verifier':
        performance = RXSystemOptimizer.get_cached_workload_stats(user.id)
    else:
        # Admin gets system-wide analytics
        performance = RXSystemOptimizer.get_prescription_analytics()
    
    return Response({
        'success': True,
        'data': {
            'counts': dashboard_stats['counts'],
            'recent_activities': VerificationActivitySerializer(recent_activities, many=True).data,
            'performance': performance,
            'system_health': RXSystemOptimizer.get_system_health_status(),
            'last_updated': dashboard_stats.get('last_updated')
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsRXVerifierOrAdmin])
def pending_prescriptions(request):
    """
    Get pending prescriptions for assignment
    GET /api/rx-upload/pending/
    """
    # Get unassigned pending prescriptions
    queryset = PrescriptionUpload.objects.filter(
        verification_status='pending'
    ).order_by('-is_urgent', '-priority_level', 'uploaded_at')
    
    # Pagination
    paginator = PrescriptionPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = PrescriptionUploadSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    
    serializer = PrescriptionUploadSerializer(queryset, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    }, status=status.HTTP_200_OK)


# ========================
# WORKLOAD MANAGEMENT VIEWS
# ========================

@api_view(['GET'])
@permission_classes([IsRXVerifierOrAdmin])
def verifier_workloads(request):
    """
    Get all verifier workloads (admin only)
    GET /api/rx-upload/workloads/
    """
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    workloads = VerifierWorkload.objects.select_related('verifier').all()
    
    # Update all workloads
    for workload in workloads:
        workload.update_workload()
    
    return Response({
        'success': True,
        'data': VerifierWorkloadSerializer(workloads, many=True).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsRXVerifier])
def update_availability(request):
    """
    Update verifier availability status
    POST /api/rx-upload/availability/
    Body: { "is_available": true/false }
    """
    workload = get_object_or_404(VerifierWorkload, verifier=request.user)
    is_available = request.data.get('is_available')
    
    if is_available is None:
        return Response({
            'success': False,
            'message': 'is_available field is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle string values properly
    if isinstance(is_available, str):
        is_available_bool = is_available.lower() in ['true', '1', 'yes']
    else:
        is_available_bool = bool(is_available)
    
    workload.is_available = is_available_bool
    workload.save()
    
    return Response({
        'success': True,
        'message': f'Availability updated to {"available" if workload.is_available else "unavailable"}',
        'data': VerifierWorkloadSerializer(workload).data
    }, status=status.HTTP_200_OK)


# ========================
# ORDER INTEGRATION VIEWS
# ========================

@api_view(['POST'])
@permission_classes([IsRXVerifierOrAdmin])
def create_order_from_prescription(request, prescription_id):
    """
    Create order from approved prescription
    POST /api/rx-upload/prescriptions/{id}/create-order/
    Body: {
        "medications": [
            {"medication_name": "Medicine Name", "product_id": 123, "quantity": 2},
            ...
        ],
        "notes": "Additional notes"
    }
    """
    medications_data = request.data.get('medications', [])
    notes = request.data.get('notes', '')
    
    success, message, order = PrescriptionOrderManager.create_order_from_prescription(
        prescription_id=prescription_id,
        medications_data=medications_data,
        notes=notes
    )
    
    if success:
        from orders.serializers import OrderSerializer
        return Response({
            'success': True,
            'message': message,
            'data': {
                'order': OrderSerializer(order).data,
                'order_id': order.id,
                'order_number': order.order_number
            }
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_prescription_orders(request, prescription_id):
    """
    Get all orders related to a prescription
    GET /api/rx-upload/prescriptions/{id}/orders/
    """
    # Check permissions
    prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
    
    if request.user.role not in ['admin', 'rx_verifier'] and prescription.customer != request.user:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    orders = PrescriptionOrderManager.get_prescription_orders(prescription_id)
    
    from orders.serializers import OrderSerializer
    return Response({
        'success': True,
        'data': {
            'prescription_number': prescription.prescription_number,
            'orders': OrderSerializer(orders, many=True).data
        }
    }, status=status.HTTP_200_OK)
