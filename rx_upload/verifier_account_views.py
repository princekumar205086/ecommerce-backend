# API Views for Verifier Account Management

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import logging

from .verifier_management import VerifierAccountManager, VerifierAccountCreationSerializer
from .models import VerifierWorkload

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminOnlyPermission(permissions.BasePermission):
    """Permission class that only allows admin users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )


class CreateVerifierAccountView(APIView):
    """API endpoint for creating verifier accounts by admin"""
    
    permission_classes = [AdminOnlyPermission]
    
    def post(self, request):
        """Create a new verifier account"""
        try:
            # Validate and create account
            result = VerifierAccountManager.create_verifier_account(
                admin_user=request.user,
                account_data=request.data
            )
            
            if result['success']:
                response_data = {
                    'success': True,
                    'message': result['message'],
                    'verifier_id': result['verifier'].id,
                    'verifier_email': result['verifier'].email,
                    'verifier_name': result['verifier'].full_name,
                    'workload_id': result['workload'].id,
                    'email_sent': result['email_sent'],
                }
                
                # Include credentials if email wasn't sent
                if not result['email_sent'] and result.get('login_credentials'):
                    response_data['login_credentials'] = result['login_credentials']
                    response_data['warning'] = 'Email notification failed. Please provide credentials manually.'
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': result['message'],
                    'errors': result['errors']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except PermissionError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error creating verifier account: {e}")
            return Response({
                'success': False,
                'message': 'Internal server error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifierAccountListView(APIView):
    """API endpoint for listing verifier accounts"""
    
    permission_classes = [AdminOnlyPermission]
    
    def get(self, request):
        """Get list of all verifier accounts"""
        try:
            verifiers = User.objects.filter(role='rx_verifier').select_related('workload_stats')
            
            verifier_list = []
            for verifier in verifiers:
                try:
                    workload = VerifierWorkload.objects.get(verifier=verifier)
                    workload_data = {
                        'max_daily_capacity': workload.max_daily_capacity,
                        'current_daily_count': workload.current_daily_count,
                        'is_available': workload.is_available,
                        'approval_rate': workload.approval_rate,
                        'total_verified': workload.total_verified,
                    }
                except VerifierWorkload.DoesNotExist:
                    workload_data = None
                
                verifier_list.append({
                    'id': verifier.id,
                    'email': verifier.email,
                    'full_name': verifier.full_name,
                    'phone_number': getattr(verifier, 'phone_number', ''),
                    'specialization': getattr(verifier, 'specialization', ''),
                    'department': getattr(verifier, 'department', ''),
                    'is_active': verifier.is_active,
                    'date_joined': verifier.date_joined.isoformat(),
                    'last_login': verifier.last_login.isoformat() if verifier.last_login else None,
                    'workload': workload_data,
                })
            
            # Get account statistics
            stats = VerifierAccountManager.get_verifier_account_stats()
            
            return Response({
                'success': True,
                'verifiers': verifier_list,
                'statistics': stats,
                'total_count': len(verifier_list)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching verifier accounts: {e}")
            return Response({
                'success': False,
                'message': 'Failed to fetch verifier accounts'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendCredentialReminderView(APIView):
    """API endpoint for sending credential reminders"""
    
    permission_classes = [AdminOnlyPermission]
    
    def post(self, request):
        """Send credential reminder to verifier"""
        try:
            verifier_email = request.data.get('verifier_email')
            
            if not verifier_email:
                return Response({
                    'success': False,
                    'message': 'Verifier email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = VerifierAccountManager.send_credential_reminder(
                verifier_email=verifier_email,
                admin_user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': result['message'],
                    'new_password': result.get('new_password')  # Include for admin reference
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except PermissionError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Error sending credential reminder: {e}")
            return Response({
                'success': False,
                'message': 'Failed to send credential reminder'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifierAccountDetailView(APIView):
    """API endpoint for individual verifier account details"""
    
    permission_classes = [AdminOnlyPermission]
    
    def get(self, request, verifier_id):
        """Get detailed information about a specific verifier"""
        try:
            verifier = User.objects.get(id=verifier_id, role='rx_verifier')
            
            # Get workload information
            try:
                workload = VerifierWorkload.objects.get(verifier=verifier)
                workload_data = {
                    'id': workload.id,
                    'max_daily_capacity': workload.max_daily_capacity,
                    'current_daily_count': workload.current_daily_count,
                    'pending_count': workload.pending_count,
                    'in_review_count': workload.in_review_count,
                    'total_verified': workload.total_verified,
                    'total_approved': workload.total_approved,
                    'total_rejected': workload.total_rejected,
                    'approval_rate': workload.approval_rate,
                    'average_processing_time': float(workload.average_processing_time),
                    'is_available': workload.is_available,
                    'can_accept_more': workload.can_accept_more,
                }
            except VerifierWorkload.DoesNotExist:
                workload_data = None
            
            # Get recent activity
            from .models import VerificationActivity
            recent_activities = VerificationActivity.objects.filter(
                verifier=verifier
            ).order_by('-timestamp')[:10]
            
            activities_data = [{
                'id': activity.id,
                'activity_type': activity.activity_type,
                'prescription_id': activity.prescription.id if activity.prescription else None,
                'timestamp': activity.timestamp.isoformat(),
                'details': activity.details,
            } for activity in recent_activities]
            
            return Response({
                'success': True,
                'verifier': {
                    'id': verifier.id,
                    'email': verifier.email,
                    'full_name': verifier.full_name,
                    'phone_number': getattr(verifier, 'phone_number', ''),
                    'specialization': getattr(verifier, 'specialization', ''),
                    'department': getattr(verifier, 'department', ''),
                    'license_number': getattr(verifier, 'license_number', ''),
                    'is_active': verifier.is_active,
                    'email_verified': verifier.email_verified,
                    'date_joined': verifier.date_joined.isoformat(),
                    'last_login': verifier.last_login.isoformat() if verifier.last_login else None,
                },
                'workload': workload_data,
                'recent_activities': activities_data,
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Verifier not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching verifier details: {e}")
            return Response({
                'success': False,
                'message': 'Failed to fetch verifier details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, verifier_id):
        """Update verifier account information"""
        try:
            verifier = User.objects.get(id=verifier_id, role='rx_verifier')
            
            # Update allowed fields
            allowed_fields = [
                'full_name', 'phone_number', 'specialization', 
                'department', 'license_number', 'is_active'
            ]
            
            updated_fields = []
            for field in allowed_fields:
                if field in request.data:
                    setattr(verifier, field, request.data[field])
                    updated_fields.append(field)
            
            verifier.save()
            
            # Update workload if provided
            if 'workload' in request.data:
                try:
                    workload = VerifierWorkload.objects.get(verifier=verifier)
                    workload_data = request.data['workload']
                    
                    if 'max_daily_capacity' in workload_data:
                        workload.max_daily_capacity = workload_data['max_daily_capacity']
                    if 'is_available' in workload_data:
                        workload.is_available = workload_data['is_available']
                    
                    workload.save()
                    updated_fields.append('workload')
                    
                except VerifierWorkload.DoesNotExist:
                    pass
            
            logger.info(f"Verifier {verifier.email} updated by admin {request.user.email}")
            
            return Response({
                'success': True,
                'message': f'Verifier account updated successfully',
                'updated_fields': updated_fields
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Verifier not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating verifier: {e}")
            return Response({
                'success': False,
                'message': 'Failed to update verifier account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifierAccountStatsView(APIView):
    """API endpoint for verifier account statistics"""
    
    permission_classes = [AdminOnlyPermission]
    
    def get(self, request):
        """Get comprehensive verifier account statistics"""
        try:
            stats = VerifierAccountManager.get_verifier_account_stats()
            
            # Add more detailed statistics
            from django.db.models import Avg, Sum, Count
            from .models import PrescriptionUpload
            
            # Performance statistics
            performance_stats = VerifierWorkload.objects.aggregate(
                avg_approval_rate=Avg('approval_rate'),
                avg_processing_time=Avg('average_processing_time'),
                total_verifications=Sum('total_verified'),
                avg_daily_capacity=Avg('max_daily_capacity'),
            )
            
            # Recent activity statistics
            from datetime import timedelta
            from django.utils import timezone
            
            last_30_days = timezone.now() - timedelta(days=30)
            recent_verifications = PrescriptionUpload.objects.filter(
                verification_date__gte=last_30_days
            ).count()
            
            return Response({
                'success': True,
                'account_statistics': stats,
                'performance_statistics': {
                    'average_approval_rate': round(performance_stats['avg_approval_rate'] or 0, 2),
                    'average_processing_time_hours': round(
                        float(performance_stats['avg_processing_time'] or 0), 2
                    ),
                    'total_verifications_all_time': performance_stats['total_verifications'] or 0,
                    'average_daily_capacity': round(performance_stats['avg_daily_capacity'] or 0, 1),
                    'recent_verifications_30_days': recent_verifications,
                },
                'timestamp': timezone.now().isoformat(),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching verifier statistics: {e}")
            return Response({
                'success': False,
                'message': 'Failed to fetch verifier statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Utility functions for testing and debugging
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def test_verifier_email_notification(request):
    """Test endpoint for verifier email notifications"""
    try:
        test_data = {
            'email': 'test.verifier@example.com',
            'full_name': 'Test Verifier',
            'specialization': 'General Medicine',
            'department': 'Internal Medicine',
            'max_daily_capacity': 25,
            'send_welcome_email': True,
        }
        
        # Update with request data if provided
        test_data.update(request.data)
        
        serializer = VerifierAccountCreationSerializer(data=test_data)
        
        if serializer.is_valid():
            # Just validate and create the email content without actually creating user
            from django.utils import timezone
            
            context = {
                'user': type('User', (), {
                    'email': test_data['email'],
                    'full_name': test_data['full_name']
                })(),
                'full_name': test_data['full_name'],
                'email': test_data['email'],
                'temporary_password': 'TestPass123!',
                'login_url': 'https://example.com/login',
                'system_name': 'RX Verification System',
                'support_email': 'support@example.com',
                'creation_date': timezone.now().strftime('%B %d, %Y'),
                'specialization': test_data.get('specialization', ''),
                'department': test_data.get('department', ''),
                'max_daily_capacity': test_data.get('max_daily_capacity', 20),
                'platform_features': [
                    'Prescription verification and approval',
                    'Real-time workload management',
                    'Performance analytics and reporting',
                ],
                'security_guidelines': [
                    'Change your password immediately after first login',
                    'Use strong, unique passwords',
                ],
                'next_steps': [
                    'Log in using your temporary credentials',
                    'Complete your profile setup',
                ]
            }
            
            html_content = serializer._render_welcome_email_html(context)
            text_content = serializer._render_welcome_email_text(context)
            
            return Response({
                'success': True,
                'message': 'Email templates generated successfully',
                'html_preview': html_content[:500] + '...' if len(html_content) > 500 else html_content,
                'text_preview': text_content[:500] + '...' if len(text_content) > 500 else text_content,
                'full_html_length': len(html_content),
                'full_text_length': len(text_content),
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error testing email notification: {e}")
        return Response({
            'success': False,
            'message': f'Email test failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)