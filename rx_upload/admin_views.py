"""
RX Upload Admin Views - Enterprise Level
Comprehensive admin management system for prescription verification
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, ExpressionWrapper, DurationField
from django.db import transaction
from datetime import datetime, timedelta
import logging

from .models import PrescriptionUpload, VerifierWorkload, VerificationActivity, VerifierProfile
from .serializers import (
    PrescriptionUploadSerializer,
    VerifierWorkloadSerializer,
    VerificationActivitySerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ========================
# ADMIN DASHBOARD & ANALYTICS
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    """
    Comprehensive admin dashboard with system-wide analytics
    GET /api/rx-upload/admin/dashboard/
    """
    try:
        # Prescription statistics
        total_prescriptions = PrescriptionUpload.objects.count()
        pending_prescriptions = PrescriptionUpload.objects.filter(verification_status='pending').count()
        in_review_prescriptions = PrescriptionUpload.objects.filter(verification_status='in_review').count()
        approved_prescriptions = PrescriptionUpload.objects.filter(verification_status='approved').count()
        rejected_prescriptions = PrescriptionUpload.objects.filter(verification_status='rejected').count()
        clarification_needed = PrescriptionUpload.objects.filter(verification_status='clarification_needed').count()
        
        # Urgent prescriptions
        urgent_prescriptions = PrescriptionUpload.objects.filter(
            is_urgent=True,
            verification_status__in=['pending', 'in_review']
        ).count()
        
        # Overdue prescriptions (pending > 24 hours)
        overdue_threshold = timezone.now() - timedelta(hours=24)
        overdue_prescriptions = PrescriptionUpload.objects.filter(
            verification_status__in=['pending', 'in_review'],
            uploaded_at__lt=overdue_threshold
        ).count()
        
        # Verifier statistics
        total_verifiers = User.objects.filter(role='rx_verifier', is_active=True).count()
        available_verifiers = VerifierWorkload.objects.filter(is_available=True).count()
        
        # Calculate average processing time
        completed = PrescriptionUpload.objects.filter(
            verification_status__in=['approved', 'rejected']
        ).exclude(verification_date__isnull=True)
        
        if completed.exists():
            avg_time = completed.annotate(
                processing_duration=ExpressionWrapper(
                    F('verification_date') - F('uploaded_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('processing_duration'))['avg']
            
            avg_hours = avg_time.total_seconds() / 3600 if avg_time else 0
        else:
            avg_hours = 0
        
        # Today's statistics
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_uploaded = PrescriptionUpload.objects.filter(uploaded_at__gte=today_start).count()
        today_verified = PrescriptionUpload.objects.filter(verification_date__gte=today_start).count()
        
        # Week's statistics
        week_start = timezone.now() - timedelta(days=7)
        week_uploaded = PrescriptionUpload.objects.filter(uploaded_at__gte=week_start).count()
        week_verified = PrescriptionUpload.objects.filter(verification_date__gte=week_start).count()
        
        # Approval rate
        total_verified = approved_prescriptions + rejected_prescriptions
        approval_rate = (approved_prescriptions / total_verified * 100) if total_verified > 0 else 0
        
        # Recent activities
        recent_activities = VerificationActivity.objects.select_related(
            'prescription', 'verifier'
        ).order_by('-timestamp')[:20]
        
        return Response({
            'success': True,
            'data': {
                'overview': {
                    'total_prescriptions': total_prescriptions,
                    'pending': pending_prescriptions,
                    'in_review': in_review_prescriptions,
                    'approved': approved_prescriptions,
                    'rejected': rejected_prescriptions,
                    'clarification_needed': clarification_needed,
                    'urgent': urgent_prescriptions,
                    'overdue': overdue_prescriptions,
                },
                'verifiers': {
                    'total': total_verifiers,
                    'available': available_verifiers,
                    'offline': total_verifiers - available_verifiers,
                },
                'performance': {
                    'average_processing_time_hours': round(avg_hours, 2),
                    'approval_rate': round(approval_rate, 2),
                },
                'today': {
                    'uploaded': today_uploaded,
                    'verified': today_verified,
                },
                'this_week': {
                    'uploaded': week_uploaded,
                    'verified': week_verified,
                },
                'recent_activities': VerificationActivitySerializer(recent_activities, many=True).data
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to load dashboard: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================
# ADMIN PRESCRIPTION MANAGEMENT
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_list_prescriptions(request):
    """
    List all prescriptions with advanced filtering
    GET /api/rx-upload/admin/prescriptions/
    Query params: status, verifier_id, urgent, overdue, date_from, date_to, search
    """
    try:
        queryset = PrescriptionUpload.objects.select_related(
            'customer', 'verified_by'
        ).prefetch_related('medications', 'activities')
        
        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(verification_status=status_filter)
        
        verifier_id = request.query_params.get('verifier_id')
        if verifier_id:
            queryset = queryset.filter(verified_by_id=verifier_id)
        
        urgent_only = request.query_params.get('urgent')
        if urgent_only == 'true':
            queryset = queryset.filter(is_urgent=True)
        
        overdue_only = request.query_params.get('overdue')
        if overdue_only == 'true':
            overdue_threshold = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(
                verification_status__in=['pending', 'in_review'],
                uploaded_at__lt=overdue_threshold
            )
        
        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(uploaded_at__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(uploaded_at__lte=date_to)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(prescription_number__icontains=search) |
                Q(patient_name__icontains=search) |
                Q(customer__full_name__icontains=search) |
                Q(customer__email__icontains=search)
            )
        
        # Ordering
        ordering = request.query_params.get('ordering', '-uploaded_at')
        queryset = queryset.order_by(ordering)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        prescriptions = queryset[start:end]
        
        serializer = PrescriptionUploadSerializer(prescriptions, many=True)
        
        return Response({
            'success': True,
            'data': {
                'results': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size,
                }
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin list prescriptions error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to fetch prescriptions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_assign_prescription(request, prescription_id):
    """
    Assign prescription to a specific verifier (Admin only)
    POST /api/rx-upload/admin/prescriptions/{id}/assign/
    Body: { "verifier_id": 123, "priority_level": 3, "is_urgent": false }
    """
    try:
        prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
        verifier_id = request.data.get('verifier_id')
        
        if not verifier_id:
            return Response({
                'success': False,
                'message': 'Verifier ID is required',
                'errors': {'verifier_id': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get verifier
        try:
            verifier = User.objects.get(id=verifier_id, role='rx_verifier', is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid verifier ID or verifier not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check verifier workload
        workload, created = VerifierWorkload.objects.get_or_create(
            verifier=verifier,
            defaults={'is_available': True, 'max_daily_capacity': 50}
        )
        
        if not workload.can_accept_more and not request.data.get('force_assign'):
            return Response({
                'success': False,
                'message': f'Verifier {verifier.full_name} is at capacity. Use force_assign=true to override.',
                'data': {
                    'current_workload': workload.in_review_count,
                    'daily_capacity': workload.max_daily_capacity,
                    'can_accept_more': workload.can_accept_more
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update prescription
        with transaction.atomic():
            prescription.verified_by = verifier
            prescription.verification_status = 'in_review'
            
            # Update priority if provided
            if 'priority_level' in request.data:
                prescription.priority_level = request.data['priority_level']
            
            if 'is_urgent' in request.data:
                prescription.is_urgent = request.data['is_urgent']
            
            prescription.save()
            
            # Create activity log
            VerificationActivity.objects.create(
                prescription=prescription,
                verifier=request.user,  # Admin who assigned
                action='assigned',
                description=f'Admin {request.user.full_name} assigned to {verifier.full_name}'
            )
            
            # Update workload
            workload.update_workload()
        
        return Response({
            'success': True,
            'message': f'Prescription assigned to {verifier.full_name}',
            'data': PrescriptionUploadSerializer(prescription).data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin assign prescription error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to assign prescription: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_reassign_prescription(request, prescription_id):
    """
    Reassign prescription to different verifier
    POST /api/rx-upload/admin/prescriptions/{id}/reassign/
    Body: { "verifier_id": 124, "reason": "Workload balancing" }
    """
    try:
        prescription = get_object_or_404(PrescriptionUpload, id=prescription_id)
        new_verifier_id = request.data.get('verifier_id')
        reason = request.data.get('reason', 'Administrative reassignment')
        
        if not new_verifier_id:
            return Response({
                'success': False,
                'message': 'Verifier ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_verifier = User.objects.get(id=new_verifier_id, role='rx_verifier', is_active=True)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid verifier ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_verifier = prescription.verified_by
        
        with transaction.atomic():
            prescription.verified_by = new_verifier
            prescription.save()
            
            # Create activity log
            VerificationActivity.objects.create(
                prescription=prescription,
                verifier=request.user,
                action='assigned',
                description=f'Reassigned from {old_verifier.full_name if old_verifier else "Unassigned"} to {new_verifier.full_name}. Reason: {reason}'
            )
            
            # Update both verifiers' workload
            if old_verifier:
                old_workload, _ = VerifierWorkload.objects.get_or_create(verifier=old_verifier)
                old_workload.update_workload()
            
            new_workload, _ = VerifierWorkload.objects.get_or_create(verifier=new_verifier)
            new_workload.update_workload()
        
        return Response({
            'success': True,
            'message': f'Prescription reassigned to {new_verifier.full_name}',
            'data': PrescriptionUploadSerializer(prescription).data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin reassign error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to reassign: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_bulk_assign(request):
    """
    Bulk assign prescriptions using auto-balancing algorithm
    POST /api/rx-upload/admin/prescriptions/bulk-assign/
    Body: { 
        "prescription_ids": [uuid1, uuid2, ...],
        "strategy": "balanced" | "fastest" | "round_robin"
    }
    """
    try:
        prescription_ids = request.data.get('prescription_ids', [])
        strategy = request.data.get('strategy', 'balanced')
        
        if not prescription_ids:
            return Response({
                'success': False,
                'message': 'No prescription IDs provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get available verifiers
        verifiers = User.objects.filter(
            role='rx_verifier',
            is_active=True,
            workload_stats__is_available=True
        ).select_related('workload_stats').order_by('workload_stats__in_review_count')
        
        if not verifiers.exists():
            return Response({
                'success': False,
                'message': 'No available verifiers found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get prescriptions
        prescriptions = PrescriptionUpload.objects.filter(
            id__in=prescription_ids,
            verification_status='pending'
        )
        
        if not prescriptions.exists():
            return Response({
                'success': False,
                'message': 'No pending prescriptions found with provided IDs'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        assigned_count = 0
        assignments = []
        
        with transaction.atomic():
            for i, prescription in enumerate(prescriptions):
                # Select verifier based on strategy
                if strategy == 'balanced':
                    # Assign to verifier with lowest current workload
                    verifier = verifiers[0]
                    # Re-sort after each assignment
                    verifiers = User.objects.filter(
                        role='rx_verifier',
                        is_active=True,
                        workload_stats__is_available=True
                    ).select_related('workload_stats').order_by('workload_stats__in_review_count')
                
                elif strategy == 'round_robin':
                    # Round-robin assignment
                    verifier = verifiers[i % len(verifiers)]
                
                elif strategy == 'fastest':
                    # Assign to verifier with best average processing time
                    verifier = verifiers.order_by('workload_stats__average_processing_time').first()
                
                else:
                    verifier = verifiers[0]
                
                # Assign
                prescription.verified_by = verifier
                prescription.verification_status = 'in_review'
                prescription.save()
                
                # Log activity
                VerificationActivity.objects.create(
                    prescription=prescription,
                    verifier=request.user,
                    action='assigned',
                    description=f'Bulk assigned to {verifier.full_name} using {strategy} strategy'
                )
                
                assigned_count += 1
                assignments.append({
                    'prescription_id': str(prescription.id),
                    'prescription_number': prescription.prescription_number,
                    'verifier_id': verifier.id,
                    'verifier_name': verifier.full_name
                })
                
                # Update workload
                workload, _ = VerifierWorkload.objects.get_or_create(verifier=verifier)
                workload.update_workload()
        
        return Response({
            'success': True,
            'message': f'Successfully assigned {assigned_count} prescriptions',
            'data': {
                'assigned_count': assigned_count,
                'strategy_used': strategy,
                'assignments': assignments
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Bulk assign error: {e}")
        return Response({
            'success': False,
            'message': f'Bulk assignment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================
# ADMIN VERIFIER MANAGEMENT
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_list_verifiers(request):
    """
    List all verifiers with their workload and performance
    GET /api/rx-upload/admin/verifiers/
    """
    try:
        verifiers = User.objects.filter(role='rx_verifier').select_related(
            'workload_stats'
        ).order_by('-is_active', 'full_name')
        
        verifier_data = []
        for verifier in verifiers:
            workload, _ = VerifierWorkload.objects.get_or_create(
                verifier=verifier,
                defaults={'is_available': True, 'max_daily_capacity': 50}
            )
            workload.update_workload()
            
            verifier_data.append({
                'id': verifier.id,
                'email': verifier.email,
                'full_name': verifier.full_name,
                'contact': verifier.contact,
                'is_active': verifier.is_active,
                'date_joined': verifier.date_joined,
                'workload': VerifierWorkloadSerializer(workload).data
            })
        
        return Response({
            'success': True,
            'data': verifier_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin list verifiers error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to fetch verifiers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_update_verifier_status(request, verifier_id):
    """
    Update verifier status and settings
    POST /api/rx-upload/admin/verifiers/{id}/update-status/
    Body: { 
        "is_active": true, 
        "is_available": true,
        "max_daily_capacity": 50
    }
    """
    try:
        verifier = get_object_or_404(User, id=verifier_id, role='rx_verifier')
        
        # Update user status
        if 'is_active' in request.data:
            verifier.is_active = request.data['is_active']
            verifier.save()
        
        # Update workload settings
        workload, _ = VerifierWorkload.objects.get_or_create(verifier=verifier)
        
        if 'is_available' in request.data:
            workload.is_available = request.data['is_available']
        
        if 'max_daily_capacity' in request.data:
            workload.max_daily_capacity = request.data['max_daily_capacity']
        
        workload.save()
        workload.update_workload()
        
        return Response({
            'success': True,
            'message': f'Verifier {verifier.full_name} updated successfully',
            'data': {
                'verifier': {
                    'id': verifier.id,
                    'full_name': verifier.full_name,
                    'is_active': verifier.is_active
                },
                'workload': VerifierWorkloadSerializer(workload).data
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin update verifier error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to update verifier: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================
# ADMIN REPORTS & ANALYTICS
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_performance_report(request):
    """
    Generate comprehensive performance report
    GET /api/rx-upload/admin/reports/performance/
    Query params: date_from, date_to, verifier_id
    """
    try:
        # Date range
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        verifier_id = request.query_params.get('verifier_id')
        
        queryset = PrescriptionUpload.objects.all()
        
        if date_from:
            queryset = queryset.filter(uploaded_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(uploaded_at__lte=date_to)
        if verifier_id:
            queryset = queryset.filter(verified_by_id=verifier_id)
        
        # Overall statistics
        total = queryset.count()
        approved = queryset.filter(verification_status='approved').count()
        rejected = queryset.filter(verification_status='rejected').count()
        pending = queryset.filter(verification_status='pending').count()
        in_review = queryset.filter(verification_status='in_review').count()
        
        # Performance metrics
        verified = queryset.filter(verification_status__in=['approved', 'rejected'])
        
        if verified.exists():
            avg_time = verified.annotate(
                processing_duration=ExpressionWrapper(
                    F('verification_date') - F('uploaded_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('processing_duration'))['avg']
            
            avg_hours = avg_time.total_seconds() / 3600 if avg_time else 0
        else:
            avg_hours = 0
        
        # Verifier-wise breakdown
        verifier_stats = []
        if not verifier_id:
            verifiers = User.objects.filter(role='rx_verifier')
            for v in verifiers:
                v_prescriptions = queryset.filter(verified_by=v)
                v_approved = v_prescriptions.filter(verification_status='approved').count()
                v_rejected = v_prescriptions.filter(verification_status='rejected').count()
                v_total = v_approved + v_rejected
                
                verifier_stats.append({
                    'verifier_id': v.id,
                    'verifier_name': v.full_name,
                    'total_verified': v_total,
                    'approved': v_approved,
                    'rejected': v_rejected,
                    'approval_rate': (v_approved / v_total * 100) if v_total > 0 else 0
                })
        
        return Response({
            'success': True,
            'data': {
                'date_range': {
                    'from': date_from,
                    'to': date_to
                },
                'overall': {
                    'total_prescriptions': total,
                    'approved': approved,
                    'rejected': rejected,
                    'pending': pending,
                    'in_review': in_review,
                    'approval_rate': (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0,
                    'average_processing_hours': round(avg_hours, 2)
                },
                'verifier_breakdown': verifier_stats
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Admin performance report error: {e}")
        return Response({
            'success': False,
            'message': f'Failed to generate report: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
