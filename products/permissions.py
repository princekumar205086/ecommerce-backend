from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow admins to edit objects.
    Everyone can read, only admins can write.
    """
    def has_permission(self, request, view):
        if request.method in permissions.READONLY_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'


class IsSupplierOrAdmin(permissions.BasePermission):
    """
    Permission to allow suppliers and admins to create/edit objects.
    Everyone can read, only suppliers and admins can write.
    """
    def has_permission(self, request, view):
        if request.method in permissions.READONLY_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['supplier', 'admin']


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow owners of an object or admins to edit it.
    Everyone can read, only object owners or admins can write.
    """
    def has_permission(self, request, view):
        if request.method in permissions.READONLY_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.READONLY_METHODS:
            return True
        
        # Write permissions only for owner or admin
        return (
            obj.user == request.user or 
            (request.user.is_authenticated and request.user.role == 'admin')
        )


class IsReviewOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission for product reviews.
    - GET: Anyone (including anonymous users)
    - POST: Authenticated users only
    - PUT/PATCH/DELETE: Only review owner or admin
    """
    def has_permission(self, request, view):
        if request.method in permissions.READONLY_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.READONLY_METHODS:
            return True
        
        # Write permissions only for review owner or admin
        return (
            obj.user == request.user or 
            (request.user.is_authenticated and request.user.role == 'admin')
        )