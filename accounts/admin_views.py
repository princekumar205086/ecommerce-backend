"""
Enterprise-level admin views for user management
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import timedelta
import logging
import csv
from django.http import HttpResponse

from ecommerce.permissions import IsAdmin, IsAdminOrReadOnly
from .models import AuditLog, SupplierRequest
from .admin_serializers import (
    AdminUserListSerializer, AdminUserDetailSerializer,
    AdminUserCreateSerializer, AdminUserUpdateSerializer,
    AdminUserRoleChangeSerializer, AdminUserStatusChangeSerializer,
    AdminBulkUserActionSerializer, AuditLogSerializer,
    UserStatisticsSerializer, AdminRXVerifierCreateSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


# Common Swagger Parameters
AUTH_HEADER = openapi.Parameter(
    'Authorization',
    openapi.IN_HEADER,
    description="Bearer <access_token>",
    type=openapi.TYPE_STRING,
    required=True
)


class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for admin views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminUserListView(generics.ListAPIView):
    """
    List all users with advanced filtering and search (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    serializer_class = AdminUserListSerializer
    pagination_class = StandardResultsPagination
    
    @swagger_auto_schema(
        operation_description="List all users with filtering, search, and pagination (Admin only)",
        operation_summary="List All Users (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[
            AUTH_HEADER,
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by role (user/supplier/admin/rx_verifier)", type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('email_verified', openapi.IN_QUERY, description="Filter by email verification (true/false)", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by email, name, or contact", type=openapi.TYPE_STRING),
            openapi.Parameter('date_joined_from', openapi.IN_QUERY, description="Filter by registration date from (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_joined_to', openapi.IN_QUERY, description="Filter by registration date to (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field (e.g., -date_joined, email)", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response('Success', AdminUserListSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Role filter
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Active status filter
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Email verified filter
        email_verified = self.request.query_params.get('email_verified')
        if email_verified is not None:
            queryset = queryset.filter(email_verified=email_verified.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(full_name__icontains=search) |
                Q(contact__icontains=search)
            )
        
        # Date range filter
        date_from = self.request.query_params.get('date_joined_from')
        date_to = self.request.query_params.get('date_joined_to')
        
        if date_from:
            queryset = queryset.filter(date_joined__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_joined__lte=date_to)
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-date_joined')
        queryset = queryset.order_by(ordering)
        
        return queryset


class AdminUserDetailView(generics.RetrieveAPIView):
    """
    Get detailed user information (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    serializer_class = AdminUserDetailSerializer
    queryset = User.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_description="Get detailed information about a specific user (Admin only)",
        operation_summary="Get User Details (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        responses={
            200: openapi.Response('Success', AdminUserDetailSerializer),
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required',
            404: 'User not found'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminUserCreateView(generics.CreateAPIView):
    """
    Create new user account (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    serializer_class = AdminUserCreateSerializer
    
    @swagger_auto_schema(
        operation_description="Create a new user account from admin panel",
        operation_summary="Create User (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        request_body=AdminUserCreateSerializer,
        responses={
            201: openapi.Response('User created successfully', AdminUserDetailSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return detailed user info
        detail_serializer = AdminUserDetailSerializer(user)
        return Response(
            {
                'message': 'User created successfully',
                'user': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class AdminUserUpdateView(generics.UpdateAPIView):
    """
    Update user information (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    serializer_class = AdminUserUpdateSerializer
    queryset = User.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_description="Update user information (Admin only)",
        operation_summary="Update User (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        request_body=AdminUserUpdateSerializer,
        responses={
            200: openapi.Response('User updated successfully', AdminUserDetailSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required',
            404: 'User not found'
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        serializer.save()


class AdminUserDeleteView(generics.DestroyAPIView):
    """
    Delete user account (Admin only - Soft delete)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    lookup_field = 'id'
    
    @swagger_auto_schema(
        operation_description="Soft delete user account (deactivate) - Admin only",
        operation_summary="Delete User (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        responses={
            200: 'User deleted successfully',
            401: 'Unauthorized',
            403: 'Forbidden - Admin access required or cannot delete yourself',
            404: 'User not found'
        }
    )
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Cannot delete yourself
        if user.id == request.user.id:
            return Response(
                {'error': 'Cannot delete your own account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        user.is_active = False
        user.save()
        
        # Log action
        AuditLog.log_action(
            user=request.user,
            action='account_deletion',
            resource=f'User:{user.id}',
            details={
                'deleted_user': user.email,
                'admin': request.user.email
            },
            success=True
        )
        
        return Response(
            {'message': f'User {user.email} has been deactivated'},
            status=status.HTTP_200_OK
        )


class AdminUserRoleChangeView(APIView):
    """
    Change user role (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Change user's role (Admin only)",
        operation_summary="Change User Role (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        request_body=AdminUserRoleChangeSerializer,
        responses={
            200: openapi.Response('Role changed successfully', AdminUserDetailSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'User not found'
        }
    )
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AdminUserRoleChangeSerializer(
            data=request.data,
            context={'user': user, 'request': request}
        )
        
        if serializer.is_valid():
            updated_user = serializer.save()
            detail_serializer = AdminUserDetailSerializer(updated_user)
            
            return Response({
                'message': f'User role changed to {updated_user.role} successfully',
                'user': detail_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserStatusChangeView(APIView):
    """
    Activate/Deactivate user account (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Activate or deactivate user account (Admin only)",
        operation_summary="Change User Status (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        request_body=AdminUserStatusChangeSerializer,
        responses={
            200: openapi.Response('Status changed successfully', AdminUserDetailSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'User not found'
        }
    )
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AdminUserStatusChangeSerializer(
            data=request.data,
            context={'user': user, 'request': request}
        )
        
        if serializer.is_valid():
            updated_user = serializer.save()
            detail_serializer = AdminUserDetailSerializer(updated_user)
            
            status_text = 'activated' if updated_user.is_active else 'deactivated'
            
            return Response({
                'message': f'User account {status_text} successfully',
                'user': detail_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBulkUserActionView(APIView):
    """
    Perform bulk actions on multiple users (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Perform bulk actions on multiple users (activate/deactivate/verify_email) - Admin only",
        operation_summary="Bulk User Actions (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        request_body=AdminBulkUserActionSerializer,
        responses={
            200: openapi.Response(
                'Bulk action completed',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'affected_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                    }
                )
            ),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def post(self, request):
        serializer = AdminBulkUserActionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            
            return Response({
                'message': f'Bulk action completed. {result["affected_count"]} out of {result["total_count"]} users affected.',
                **result
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserStatisticsView(APIView):
    """
    Get user statistics and analytics (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Get comprehensive user statistics and analytics (Admin only)",
        operation_summary="User Statistics (Admin)",
        tags=['Admin - Analytics'],
        manual_parameters=[AUTH_HEADER],
        responses={
            200: openapi.Response('Success', UserStatisticsSerializer),
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def get(self, request):
        # Calculate statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        verified_users = User.objects.filter(email_verified=True).count()
        unverified_users = total_users - verified_users
        
        # Users by role
        users_by_role = {}
        for role, _ in User.USER_ROLES:
            users_by_role[role] = User.objects.filter(role=role).count()
        
        # New users
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        new_users_today = User.objects.filter(date_joined__date=today).count()
        new_users_this_week = User.objects.filter(date_joined__date__gte=week_ago).count()
        new_users_this_month = User.objects.filter(date_joined__date__gte=month_ago).count()
        
        # Growth rate
        previous_month = month_ago - timedelta(days=30)
        users_previous_month = User.objects.filter(
            date_joined__date__gte=previous_month,
            date_joined__date__lt=month_ago
        ).count()
        
        if users_previous_month > 0:
            growth_rate_percent = ((new_users_this_month - users_previous_month) / users_previous_month) * 100
        else:
            growth_rate_percent = 100.0 if new_users_this_month > 0 else 0.0
        
        statistics = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'verified_users': verified_users,
            'unverified_users': unverified_users,
            'users_by_role': users_by_role,
            'new_users_today': new_users_today,
            'new_users_this_week': new_users_this_week,
            'new_users_this_month': new_users_this_month,
            'growth_rate': {
                'current_month': new_users_this_month,
                'previous_month': users_previous_month,
                'percentage': round(growth_rate_percent, 2)
            }
        }
        
        serializer = UserStatisticsSerializer(statistics)
        return Response(serializer.data)


class AdminAuditLogListView(generics.ListAPIView):
    """
    List audit logs (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    serializer_class = AuditLogSerializer
    pagination_class = StandardResultsPagination
    
    @swagger_auto_schema(
        operation_description="List all audit logs with filtering (Admin only)",
        operation_summary="List Audit Logs (Admin)",
        tags=['Admin - Audit & Security'],
        manual_parameters=[
            AUTH_HEADER,
            openapi.Parameter('user_id', openapi.IN_QUERY, description="Filter by user ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('action', openapi.IN_QUERY, description="Filter by action type", type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter from date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter to date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('success', openapi.IN_QUERY, description="Filter by success status (true/false)", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response('Success', AuditLogSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # User filter
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Action filter
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        # Success filter
        success = self.request.query_params.get('success')
        if success is not None:
            queryset = queryset.filter(success=success.lower() == 'true')
        
        return queryset.order_by('-timestamp')


class AdminUserExportView(APIView):
    """
    Export users to CSV (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Export users to CSV file (Admin only)",
        operation_summary="Export Users CSV (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[
            AUTH_HEADER,
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by role", type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: 'CSV file',
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def get(self, request):
        # Get filtered queryset
        queryset = User.objects.all()
        
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Email', 'Full Name', 'Contact', 'Role',
            'Active', 'Email Verified', 'Date Joined', 'Last Login'
        ])
        
        for user in queryset:
            writer.writerow([
                user.id,
                user.email,
                user.full_name,
                user.contact,
                user.role,
                user.is_active,
                user.email_verified,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
            ])
        
        # Log export action
        AuditLog.log_action(
            user=request.user,
            action='data_export',
            resource='Users',
            details={
                'export_count': queryset.count(),
                'filters': {
                    'role': role,
                    'is_active': is_active
                }
            },
            success=True
        )
        
        return response


class AdminRXVerifierCreateView(APIView):
    """
    Create RX Verifier account (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Create a new RX Verifier account with automatic credential email (Admin only)",
        operation_summary="Create RX Verifier (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[AUTH_HEADER],
        request_body=AdminRXVerifierCreateSerializer,
        responses={
            201: openapi.Response('RX Verifier created successfully', AdminUserDetailSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def post(self, request):
        serializer = AdminRXVerifierCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            detail_serializer = AdminUserDetailSerializer(user)
            
            return Response({
                'message': 'RX Verifier account created successfully. Credentials have been sent via email.',
                'user': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserSearchView(APIView):
    """
    Advanced user search (Admin only)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    
    @swagger_auto_schema(
        operation_description="Advanced search for users (Admin only)",
        operation_summary="Search Users (Admin)",
        tags=['Admin - User Management'],
        manual_parameters=[
            AUTH_HEADER,
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING, required=True),
        ],
        responses={
            200: openapi.Response('Success', AdminUserListSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    )
    def get(self, request):
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Search query required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Search across multiple fields
        users = User.objects.filter(
            Q(email__icontains=query) |
            Q(full_name__icontains=query) |
            Q(contact__icontains=query)
        )[:20]  # Limit to 20 results
        
        serializer = AdminUserListSerializer(users, many=True)
        return Response({
            'count': users.count(),
            'results': serializer.data
        })
