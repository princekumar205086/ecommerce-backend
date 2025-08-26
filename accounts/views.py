from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView

from cart.models import Cart, CartItem
from .models import User
from .serializers import UserRegisterSerializer, UserLoginSerializer, UserSerializer, UserAddressSerializer, UpdateAddressSerializer

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
        operation_description="Register a new user account. Role can be 'user' or 'supplier'."
    )
    def post(self, request, role=None):
        # Set default role to 'user' if not provided
        if not role:
            role = 'user'
        
        # Validate role - only allow 'user' and 'supplier'
        if role not in ['user', 'supplier']:
            return Response(
                {"error": "Invalid role. Only 'user' and 'supplier' are allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            user.role = role
            user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        # Sync guest cart to user's cart
        sync_guest_cart_to_user(request, user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


# Function to sync guest cart to user's cart
def sync_guest_cart_to_user(request, user):
    session_cart = request.session.get('guest_cart')
    if session_cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        for item in session_cart:
            product_id = item['product_id']
            quantity = item['quantity']
            obj, created = CartItem.objects.get_or_create(cart=cart, product_id=product_id)
            if not created:
                obj.quantity += quantity
                obj.save()
        del request.session['guest_cart']
        request.session.modified = True

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


class UserAddressView(APIView):
    """View for getting and updating user address"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        responses={
            200: openapi.Response(
                description="User address retrieved successfully",
                examples={
                    "application/json": {
                        "id": 1,
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "contact": "1234567890",
                        "address_line_1": "123 Main Street",
                        "address_line_2": "Apt 4B",
                        "city": "Mumbai",
                        "state": "Maharashtra",
                        "postal_code": "400001",
                        "country": "India",
                        "has_address": True,
                        "full_address": "123 Main Street, Apt 4B, Mumbai, Maharashtra 400001, India"
                    }
                },
            ),
            401: "Unauthorized",
        },
        operation_description="Get current user address information"
    )
    def get(self, request):
        serializer = UserAddressSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        request_body=UpdateAddressSerializer,
        responses={
            200: openapi.Response(
                description="Address updated successfully",
                examples={
                    "application/json": {
                        "message": "Address updated successfully",
                        "address": {
                            "address_line_1": "123 Main Street",
                            "address_line_2": "Apt 4B",
                            "city": "Mumbai",
                            "state": "Maharashtra",
                            "postal_code": "400001",
                            "country": "India",
                            "has_address": True,
                            "full_address": "123 Main Street, Apt 4B, Mumbai, Maharashtra 400001, India"
                        }
                    }
                },
            ),
            400: "Invalid input",
            401: "Unauthorized",
        },
        operation_description="Update user address for future checkout use"
    )
    def put(self, request):
        serializer = UpdateAddressSerializer(data=request.data)
        if serializer.is_valid():
            # Update user address
            user = request.user
            for field, value in serializer.validated_data.items():
                setattr(user, field, value)
            user.save()
            
            # Return updated address
            address_serializer = UserAddressSerializer(user)
            return Response({
                'message': 'Address updated successfully',
                'address': address_serializer.data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        responses={
            200: openapi.Response(
                description="Address deleted successfully",
                examples={
                    "application/json": {
                        "message": "Address deleted successfully"
                    }
                },
            ),
            401: "Unauthorized",
        },
        operation_description="Delete user saved address"
    )
    def delete(self, request):
        user = request.user
        user.address_line_1 = None
        user.address_line_2 = None
        user.city = None
        user.state = None
        user.postal_code = None
        user.country = 'India'  # Reset to default
        user.save()
        
        return Response({
            'message': 'Address deleted successfully'
        })


class SaveAddressFromCheckoutView(APIView):
    """Save address from checkout flow"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'shipping_address': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'full_name': openapi.Schema(type=openapi.TYPE_STRING, description="Full name"),
                        'address_line_1': openapi.Schema(type=openapi.TYPE_STRING, description="Address line 1"),
                        'address_line_2': openapi.Schema(type=openapi.TYPE_STRING, description="Address line 2"),
                        'city': openapi.Schema(type=openapi.TYPE_STRING, description="City"),
                        'state': openapi.Schema(type=openapi.TYPE_STRING, description="State"),
                        'postal_code': openapi.Schema(type=openapi.TYPE_STRING, description="Postal code"),
                        'country': openapi.Schema(type=openapi.TYPE_STRING, description="Country"),
                    },
                    required=['full_name', 'address_line_1', 'city', 'state', 'postal_code', 'country']
                )
            },
            required=['shipping_address']
        ),
        responses={
            200: openapi.Response(
                description="Address saved successfully",
                examples={
                    "application/json": {
                        "message": "Address saved successfully for future use",
                        "address": {
                            "address_line_1": "123 Main Street",
                            "address_line_2": "Apt 4B",
                            "city": "Mumbai",
                            "state": "Maharashtra",
                            "postal_code": "400001",
                            "country": "India",
                            "has_address": True
                        }
                    }
                },
            ),
            400: "Invalid input",
            401: "Unauthorized",
        },
        operation_description="Save address from checkout for future use"
    )
    def post(self, request):
        shipping_address = request.data.get('shipping_address')
        if not shipping_address:
            return Response({
                'error': 'shipping_address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate address has required fields
        required_fields = ['full_name', 'address_line_1', 'city', 'state', 'postal_code', 'country']
        missing_fields = [field for field in required_fields if not shipping_address.get(field)]
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update user address
        user = request.user
        user.full_name = shipping_address.get('full_name', user.full_name)
        user.address_line_1 = shipping_address.get('address_line_1')
        user.address_line_2 = shipping_address.get('address_line_2', '')
        user.city = shipping_address.get('city')
        user.state = shipping_address.get('state')
        user.postal_code = shipping_address.get('postal_code')
        user.country = shipping_address.get('country', 'India')
        user.save()
        
        return Response({
            'message': 'Address saved successfully for future use',
            'address': {
                'address_line_1': user.address_line_1,
                'address_line_2': user.address_line_2,
                'city': user.city,
                'state': user.state,
                'postal_code': user.postal_code,
                'country': user.country,
                'has_address': user.has_address
            }
        })


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
