"""
Authentication and permission mixins for views
"""
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status


class AdminRequiredMixin:
    """
    Mixin to require admin authentication for views
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().dispatch(request, *args, **kwargs)


class AuthenticatedRequiredMixin:
    """
    Mixin to require user authentication for views
    """
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return super().dispatch(request, *args, **kwargs)