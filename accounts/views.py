from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from .models import User
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserSerializer

# Common Swagger components
AUTH_HEADER_PARAMETER = openapi.Parameter(
    'Authorization',
    openapi.IN_HEADER,
    description="Bearer <access_token>",
    type=openapi.TYPE_STRING,
    required=True
)

USER_RESPONSE_EXAMPLE = {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "contact": "1234567890",
    "role": "user"
}

TOKEN_RESPONSE = {
    "refresh": "refresh_token_example",
    "access": "access_token_example"
}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                examples={
                    "application/json": {
                        "user": USER_RESPONSE_EXAMPLE,
                        **TOKEN_RESPONSE
                    }
                },
            ),
            400: "Invalid input",
        },
        operation_description="Register a new user account"
    )
    def post(self, request, role=None):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if role:
            user.role = role
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "user": USER_RESPONSE_EXAMPLE,
                        **TOKEN_RESPONSE
                    }
                },
            ),
            400: "Invalid credentials",
        },
        operation_description="Authenticate user and get access token"
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        responses={
            200: openapi.Response(
                description="User profile retrieved successfully",
                examples={"application/json": USER_RESPONSE_EXAMPLE},
            ),
            401: "Unauthorized",
        },
        operation_description="Get current user profile information"
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserListView(ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(
        security=[{'Bearer': []}],  # Critical for Swagger UI auth
        manual_parameters=[
            AUTH_HEADER_PARAMETER,
            openapi.Parameter(
                'role',
                openapi.IN_QUERY,
                description="Filter by role (user or supplier)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of users",
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [USER_RESPONSE_EXAMPLE]
                    }
                },
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={"application/json": {"detail": "Authentication credentials were not provided."}},
            ),
            403: openapi.Response(
                description="Forbidden",
                examples={"application/json": {"detail": "You do not have permission to perform this action."}},
            ),
        },
        operation_description="List all users (Admin only)"
    )
    def get(self, request, *args, **kwargs):
        """Handle GET request with JWT authentication"""
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')

        if role in ['user', 'supplier']:
            return queryset.filter(role=role)
        return queryset
