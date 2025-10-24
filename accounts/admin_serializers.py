"""
Enterprise-level serializers for admin user management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AuditLog, SupplierRequest, OTP
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users in admin panel
    """
    has_address = serializers.ReadOnlyField()
    total_orders = serializers.SerializerMethodField()
    last_login_display = serializers.SerializerMethodField()
    account_age_days = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'contact', 'role',
            'is_active', 'is_staff', 'is_superuser', 'email_verified',
            'date_joined', 'last_login_display', 'has_address',
            'medixmall_mode', 'is_on_duty', 'total_orders', 'account_age_days'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_total_orders(self, obj):
        """Get total orders for user"""
        try:
            from orders.models import Order
            return Order.objects.filter(user=obj).count()
        except Exception:
            return 0
    
    def get_last_login_display(self, obj):
        """Get human-readable last login"""
        if not obj.last_login:
            return "Never"
        
        now = timezone.now()
        diff = now - obj.last_login
        
        if diff.days > 365:
            return f"{diff.days // 365} year(s) ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month(s) ago"
        elif diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour(s) ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute(s) ago"
        else:
            return "Just now"
    
    def get_account_age_days(self, obj):
        """Get account age in days"""
        if not obj.date_joined:
            return 0
        return (timezone.now() - obj.date_joined).days


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual user (admin view)
    """
    has_address = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    recent_orders = serializers.SerializerMethodField()
    account_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'contact', 'role',
            'is_active', 'is_staff', 'is_superuser', 'email_verified',
            'date_joined', 'last_login', 'has_address', 'full_address',
            'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'medixmall_mode', 'is_on_duty',
            'profile_pic', 'total_orders', 'total_spent', 'recent_orders',
            'account_stats'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_total_orders(self, obj):
        """Get total orders count"""
        try:
            from orders.models import Order
            return Order.objects.filter(user=obj).count()
        except Exception:
            return 0
    
    def get_total_spent(self, obj):
        """Get total amount spent"""
        try:
            from orders.models import Order
            from django.db.models import Sum
            total = Order.objects.filter(
                user=obj,
                status__in=['delivered', 'completed']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            return float(total)
        except Exception:
            return 0.0
    
    def get_recent_orders(self, obj):
        """Get recent orders"""
        try:
            from orders.models import Order
            orders = Order.objects.filter(user=obj).order_by('-created_at')[:5]
            return [{
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat() if order.created_at else None
            } for order in orders]
        except Exception:
            return []
    
    def get_account_stats(self, obj):
        """Get account statistics"""
        try:
            from orders.models import Order
            from cart.models import Cart, CartItem
            
            orders = Order.objects.filter(user=obj)
            cart = Cart.objects.filter(user=obj).first()
            
            stats = {
                'account_age_days': (timezone.now() - obj.date_joined).days if obj.date_joined else 0,
                'email_verified': obj.email_verified,
                'total_orders': orders.count(),
                'pending_orders': orders.filter(status='pending').count(),
                'completed_orders': orders.filter(status__in=['delivered', 'completed']).count(),
                'cancelled_orders': orders.filter(status='cancelled').count(),
                'cart_items': CartItem.objects.filter(cart=cart).count() if cart else 0,
                'wishlist_items': 0  # Add if wishlist exists
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting account stats: {str(e)}")
            return {}


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users from admin panel
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    send_credentials_email = serializers.BooleanField(default=True, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'contact', 'role', 'password', 'password2',
            'is_active', 'is_staff', 'email_verified', 'send_credentials_email'
        ]
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate role
        if data.get('role') not in ['user', 'supplier', 'admin', 'rx_verifier']:
            raise serializers.ValidationError({"role": "Invalid role."})
        
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        send_email = validated_data.pop('send_credentials_email', True)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Send credentials email if requested
        if send_email:
            self._send_credentials_email(user, password)
        
        # Log action
        request = self.context.get('request')
        if request and request.user:
            AuditLog.log_action(
                user=request.user,
                action='register',
                resource=f'User:{user.id}',
                details={
                    'created_user_email': user.email,
                    'created_user_role': user.role,
                    'admin': request.user.email
                },
                success=True
            )
        
        return user
    
    def _send_credentials_email(self, user, password):
        """Send account credentials to user"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            if user.role == 'rx_verifier':
                user.send_rx_verifier_credentials(password)
            else:
                subject = f'Your {user.get_role_display()} Account - MedixMall'
                message = f"""
Hi {user.full_name},

An administrator has created an account for you on MedixMall.

Your login credentials:
Email: {user.email}
Password: {password}
Role: {user.get_role_display()}

Please change your password after first login for security.

Login URL: https://backend.okpuja.in/api/accounts/login/

Best regards,
MedixMall Team
                """
                
                send_mail(
                    subject, message,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=True
                )
                logger.info(f"Credentials email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send credentials email: {str(e)}")


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating users from admin panel
    """
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'contact', 'is_active', 'is_staff',
            'email_verified', 'address_line_1', 'address_line_2',
            'city', 'state', 'postal_code', 'country', 'medixmall_mode'
        ]
    
    def update(self, instance, validated_data):
        # Log changes
        request = self.context.get('request')
        changes = {}
        
        for field, value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != value:
                changes[field] = {'old': old_value, 'new': value}
                setattr(instance, field, value)
        
        instance.save()
        
        # Log audit
        if request and request.user and changes:
            AuditLog.log_action(
                user=request.user,
                action='profile_update',
                resource=f'User:{instance.id}',
                details={
                    'target_user': instance.email,
                    'changes': changes,
                    'admin': request.user.email
                },
                success=True
            )
        
        return instance


class AdminUserRoleChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user role
    """
    role = serializers.ChoiceField(
        choices=User.USER_ROLES,
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_role(self, value):
        """Validate role change"""
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User context required.")
        
        # Cannot change own role
        request = self.context.get('request')
        if request and request.user and request.user.id == user.id:
            raise serializers.ValidationError("Cannot change your own role.")
        
        return value
    
    def save(self):
        """Apply role change"""
        user = self.context.get('user')
        request = self.context.get('request')
        
        old_role = user.role
        new_role = self.validated_data['role']
        reason = self.validated_data.get('reason', '')
        
        user.role = new_role
        user.save()
        
        # Log action
        if request and request.user:
            AuditLog.log_action(
                user=request.user,
                action='role_change',
                resource=f'User:{user.id}',
                details={
                    'target_user': user.email,
                    'old_role': old_role,
                    'new_role': new_role,
                    'reason': reason,
                    'admin': request.user.email
                },
                success=True
            )
        
        return user


class AdminUserStatusChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user account status
    """
    is_active = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate status change"""
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User context required.")
        
        # Cannot deactivate own account
        request = self.context.get('request')
        if request and request.user and request.user.id == user.id:
            if not data['is_active']:
                raise serializers.ValidationError("Cannot deactivate your own account.")
        
        return data
    
    def save(self):
        """Apply status change"""
        user = self.context.get('user')
        request = self.context.get('request')
        
        old_status = user.is_active
        new_status = self.validated_data['is_active']
        reason = self.validated_data.get('reason', '')
        
        user.is_active = new_status
        user.save()
        
        # Log action
        if request and request.user:
            AuditLog.log_action(
                user=request.user,
                action='account_status_change',
                resource=f'User:{user.id}',
                details={
                    'target_user': user.email,
                    'old_status': 'active' if old_status else 'inactive',
                    'new_status': 'active' if new_status else 'inactive',
                    'reason': reason,
                    'admin': request.user.email
                },
                success=True
            )
        
        return user


class AdminBulkUserActionSerializer(serializers.Serializer):
    """
    Serializer for bulk user operations
    """
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete', 'verify_email'],
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_user_ids(self, value):
        """Validate user IDs"""
        if not value:
            raise serializers.ValidationError("At least one user ID required.")
        
        # Check if users exist
        existing_count = User.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError("Some user IDs are invalid.")
        
        # Cannot include self
        request = self.context.get('request')
        if request and request.user and request.user.id in value:
            raise serializers.ValidationError("Cannot perform bulk action on your own account.")
        
        return value
    
    def save(self):
        """Execute bulk action"""
        user_ids = self.validated_data['user_ids']
        action = self.validated_data['action']
        reason = self.validated_data.get('reason', '')
        request = self.context.get('request')
        
        users = User.objects.filter(id__in=user_ids)
        affected_count = 0
        errors = []
        
        for user in users:
            try:
                if action == 'activate':
                    user.is_active = True
                    user.save()
                    affected_count += 1
                
                elif action == 'deactivate':
                    user.is_active = False
                    user.save()
                    affected_count += 1
                
                elif action == 'verify_email':
                    user.email_verified = True
                    user.save()
                    affected_count += 1
                
                elif action == 'delete':
                    # Soft delete or mark for deletion
                    user.is_active = False
                    user.save()
                    affected_count += 1
                
                # Log individual action
                if request and request.user:
                    AuditLog.log_action(
                        user=request.user,
                        action=f'bulk_{action}',
                        resource=f'User:{user.id}',
                        details={
                            'target_user': user.email,
                            'action': action,
                            'reason': reason,
                            'admin': request.user.email
                        },
                        success=True
                    )
            
            except Exception as e:
                errors.append({'user_id': user.id, 'error': str(e)})
                logger.error(f"Bulk action error for user {user.id}: {str(e)}")
        
        return {
            'affected_count': affected_count,
            'total_count': len(user_ids),
            'errors': errors
        }


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for audit logs
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'user_name', 'action', 'action_display',
            'resource', 'details', 'ip_address', 'user_agent', 'timestamp',
            'success', 'error_message', 'time_ago'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_time_ago(self, obj):
        """Get human-readable time difference"""
        now = timezone.now()
        diff = now - obj.timestamp
        
        if diff.days > 365:
            return f"{diff.days // 365} year(s) ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month(s) ago"
        elif diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour(s) ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute(s) ago"
        else:
            return "Just now"


class UserStatisticsSerializer(serializers.Serializer):
    """
    Serializer for user statistics
    """
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    unverified_users = serializers.IntegerField()
    users_by_role = serializers.DictField()
    new_users_today = serializers.IntegerField()
    new_users_this_week = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    growth_rate = serializers.DictField()


class AdminRXVerifierCreateSerializer(serializers.Serializer):
    """
    Serializer for creating RX Verifier accounts
    """
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(required=True, max_length=100)
    contact = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)
    send_credentials_email = serializers.BooleanField(default=True)
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        
        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})
        
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        send_email = validated_data.pop('send_credentials_email', True)
        
        # Create RX Verifier user
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            contact=validated_data['contact'],
            role='rx_verifier'
        )
        user.set_password(password)
        user.email_verified = True  # Auto-verify admin-created accounts
        user.is_active = True
        user.save()
        
        # Send credentials email
        if send_email:
            user.send_rx_verifier_credentials(password)
        
        # Log action
        request = self.context.get('request')
        if request and request.user:
            AuditLog.log_action(
                user=request.user,
                action='register',
                resource=f'User:{user.id}',
                details={
                    'created_rx_verifier': user.email,
                    'admin': request.user.email
                },
                success=True
            )
        
        return user
