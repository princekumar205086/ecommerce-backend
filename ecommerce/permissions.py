from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsSupplierOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['supplier', 'admin']


class IsRXVerifier(BasePermission):
    """Permission for RX verifiers"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'rx_verifier'


class IsRXVerifierOrAdmin(BasePermission):
    """Permission for RX verifiers and admins"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['rx_verifier', 'admin']


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user


class IsCreatedByUserOrAdmin(BasePermission):
    """Allow users to edit items they created, or admin to edit any"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in SAFE_METHODS:
            return True
        
        # Admin can edit/delete anything
        if request.user.is_authenticated and request.user.role == 'admin':
            return True
        
        # Users can only edit/delete items they created
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False


class IsSupplierOrAdminForUpdates(BasePermission):
    """Allow suppliers and admins to update, read-only for others"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['supplier', 'admin']
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in SAFE_METHODS:
            return True
        
        # Admin can edit/delete anything
        if request.user.is_authenticated and request.user.role == 'admin':
            return True
        
        # Suppliers can edit their own content
        if request.user.is_authenticated and request.user.role == 'supplier':
            if hasattr(obj, 'created_by'):
                return obj.created_by == request.user
            elif hasattr(obj, 'user'):
                return obj.user == request.user
                
        return False


class IsOwnerOrRXVerifierOrAdmin(BasePermission):
    """Allow object owner, RX verifiers, or admins"""
    def has_object_permission(self, request, view, obj):
        # Check if user is admin or RX verifier
        if request.user.role in ['admin', 'rx_verifier']:
            return True
        
        # Check if user is the owner (for customer accessing their own prescriptions)
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsReviewOwnerOrAdminOrReadOnly(BasePermission):
    """
    Custom permission for product reviews.
    - GET: Anyone (including anonymous users)
    - POST: Authenticated users only
    - PUT/PATCH/DELETE: Only review owner or admin
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions only for review owner or admin
        return (
            obj.user == request.user or 
            (request.user.is_authenticated and request.user.role == 'admin')
        )


class CanVerifyPrescription(BasePermission):
    """Permission to verify prescriptions - only for RX verifiers and admins"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['rx_verifier', 'admin']
    
    def has_object_permission(self, request, view, obj):
        # Only RX verifiers and admins can verify prescriptions
        if request.user.role in ['rx_verifier', 'admin']:
            return True
        return False
