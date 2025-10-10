from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.db import transaction

from cart.models import Cart, CartItem
from .models import User, OTP, PasswordResetToken, SupplierRequest
from .serializers import (
    UserRegisterSerializer, UserLoginSerializer, UserSerializer, 
    UserAddressSerializer, UpdateAddressSerializer, MedixMallModeSerializer,
    OTPVerificationSerializer, OTPRequestSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer, ResendVerificationSerializer,
    ChangePasswordSerializer, OTPLoginRequestSerializer, OTPLoginVerifySerializer, 
    LoginChoiceSerializer, EmailCheckSerializer
)

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
    "role": "user",
    "email_verified": True
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
                description="User registered successfully. Email verification sent.",
                examples={
                    "application/json": {
                        "user": USER_RESPONSE_EXAMPLE,
                        "message": "Registration successful. Please check your email for verification.",
                        **TOKEN_RESPONSE
                    }
                },
            ),
            400: "Invalid input",
        },
        operation_description="Register a new user account. Role can be 'user' or 'supplier'. Email verification will be sent."
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
            with transaction.atomic():
                print(f"🚀 Starting registration for email: {request.data.get('email')}")
                
                user = serializer.save()
                print(f"✅ User created via serializer: {user.email}")
                
                user.role = role
                user.save()
                print(f"🔧 User role set to: {role}")

                # NOTE: Welcome email moved to OTP verification success
                # Users should only get welcomed AFTER they verify their email

                # Send OTP-based email verification
                try:
                    print(f"📧 Sending verification OTP to: {user.email}")
                    verification_success, verification_message = user.send_verification_email()
                    if verification_success:
                        print(f"✅ Verification OTP sent to {user.email}")
                    else:
                        print(f"⚠️ Verification OTP failed: {verification_message}")
                except Exception as e:
                    print(f"⚠️ Verification OTP exception: {str(e)}")

                print(f"🎯 Registration completed for: {user.email}")
                
                # Don't provide tokens until email is verified
                return Response({
                    'user': UserSerializer(user).data,
                    'message': 'Registration successful! Please check your email for verification OTP.',
                }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailCheckView(APIView):
    """
    Check if an email address is already registered
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=EmailCheckSerializer,
        responses={
            200: openapi.Response(
                description="Email check result",
                examples={
                    "application/json": {
                        "email": "user@example.com",
                        "is_registered": True,
                        "message": "Email is already registered"
                    }
                },
            ),
            400: "Invalid input",
        },
        operation_description="Check if an email address is already registered in the system. Returns true if email exists, false otherwise."
    )
    def post(self, request):
        serializer = EmailCheckSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if user exists with this email (case insensitive)
            user_exists = User.objects.filter(email__iexact=email).exists()
            
            return Response({
                'email': email,
                'is_registered': user_exists,
                'message': 'Email is already registered' if user_exists else 'Email is available'
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
                'contact': openapi.Schema(type=openapi.TYPE_STRING, description='Contact number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Password'),
            },
            required=['password'],
            description="Provide either email or contact number with password"
        ),
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
            403: "Email not verified",
        },
        operation_description="Authenticate user with email/contact and password. Email must be verified."
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Check if email is verified - if not, send OTP for verification
        if not user.email_verified:
            try:
                print(f"📧 User {user.email} attempting login with unverified email - sending OTP")
                verification_success, verification_message = user.send_verification_email()
                if verification_success:
                    return Response({
                        'error': 'Email not verified. We\'ve sent a verification OTP to your email.',
                        'email_verified': False,
                        'otp_sent': True,
                        'message': 'Please verify your email with the OTP we just sent before logging in.'
                    }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        'error': 'Email not verified. Please verify your email before logging in.',
                        'email_verified': False,
                        'otp_sent': False,
                        'message': 'Failed to send OTP. Please try again or contact support.'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                print(f"⚠️ Failed to send OTP during login: {str(e)}")
                return Response({
                    'error': 'Email not verified. Please verify your email before logging in.',
                    'email_verified': False,
                    'otp_sent': False,
                    'message': 'Failed to send verification OTP. Please try again later.'
                }, status=status.HTTP_403_FORBIDDEN)

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
            201: openapi.Response(
                description="Address created successfully",
                examples={
                    "application/json": {
                        "message": "Address created successfully",
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
        operation_description="Create/Save a new address for the user"
    )
    def post(self, request):
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
                'message': 'Address created successfully',
                'address': address_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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


class MedixMallModeToggleView(APIView):
    """
    Toggle MedixMall mode for both authenticated and anonymous users
    - Authenticated users: Saves to user profile
    - Anonymous users: Saves to session
    When enabled, user only sees medicine products throughout the platform
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]  # Allow both authenticated and anonymous users

    def get_medixmall_mode(self, request):
        """Get MedixMall mode from user profile or session"""
        if request.user.is_authenticated:
            return request.user.medixmall_mode
        else:
            return request.session.get('medixmall_mode', False)

    def set_medixmall_mode(self, request, mode):
        """Set MedixMall mode in user profile or session"""
        if request.user.is_authenticated:
            request.user.medixmall_mode = mode
            request.user.save()
        else:
            request.session['medixmall_mode'] = mode

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="MedixMall mode status retrieved successfully",
                examples={
                    "application/json": {
                        "medixmall_mode": True,
                        "message": "MedixMall mode is currently enabled (authenticated user)",
                        "user_type": "authenticated",
                        "storage_type": "profile"
                    }
                },
            ),
        },
        operation_description="Get current MedixMall mode status. Works for both authenticated and anonymous users.",
        operation_summary="Get MedixMall Mode Status",
        tags=['User Profile']
    )
    def get(self, request):
        """Get current MedixMall mode status"""
        mode = self.get_medixmall_mode(request)
        user_type = "authenticated" if request.user.is_authenticated else "anonymous"
        storage_type = "profile" if request.user.is_authenticated else "session"
        
        response_data = {
            'medixmall_mode': mode,
            'message': f"MedixMall mode is currently {'enabled' if mode else 'disabled'} ({user_type} user)",
            'user_type': user_type,
            'storage_type': storage_type
        }
        response = Response(response_data)
        response['X-MedixMall-Mode'] = 'true' if mode else 'false'
        return response

    @swagger_auto_schema(
        request_body=MedixMallModeSerializer,
        responses={
            200: openapi.Response(
                description="MedixMall mode updated successfully",
                examples={
                    "application/json": {
                        "medixmall_mode": True,
                        "message": "MedixMall mode enabled successfully. You will now only see medicine products.",
                        "user_type": "authenticated",
                        "storage_type": "profile"
                    }
                },
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={"application/json": {"medixmall_mode": ["This field is required."]}},
            ),
        },
        operation_description="Toggle MedixMall mode. Works for both authenticated and anonymous users. Authenticated users save to profile, anonymous users save to session.",
        operation_summary="Toggle MedixMall Mode",
        tags=['User Profile']
    )
    def put(self, request):
        """Toggle MedixMall mode"""
        serializer = MedixMallModeSerializer(data=request.data)
        if serializer.is_valid():
            mode = serializer.validated_data['medixmall_mode']
            self.set_medixmall_mode(request, mode)
            
            user_type = "authenticated" if request.user.is_authenticated else "anonymous"
            storage_type = "profile" if request.user.is_authenticated else "session"
            
            message = (
                f"MedixMall mode enabled successfully ({user_type} user). You will now only see medicine products."
                if mode else
                f"MedixMall mode disabled successfully ({user_type} user). You can now see all products."
            )
            
            response_data = {
                'medixmall_mode': mode,
                'message': message,
                'user_type': user_type,
                'storage_type': storage_type
            }
            response = Response(response_data)
            response['X-MedixMall-Mode'] = 'true' if mode else 'false'
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist')
            },
            required=['refresh_token']
        ),
        responses={
            205: "Logout successful",
            400: "Invalid refresh token",
            401: "Unauthorized",
        },
        operation_description="Logout user and blacklist refresh token"
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view that returns user data along with tokens"""
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                examples={
                    "application/json": {
                        "access": "new_access_token",
                        "refresh": "new_refresh_token",
                        "user": USER_RESPONSE_EXAMPLE
                    }
                },
            ),
            401: "Invalid refresh token",
        },
        operation_description="Refresh access token using refresh token. Returns new tokens and user data."
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user from the refresh token
            try:
                refresh_token = request.data.get('refresh')
                token = RefreshToken(refresh_token)
                user_id = token.payload.get('user_id')
                user = User.objects.get(id=user_id)
                
                # Add user data to response
                response.data['user'] = UserSerializer(user).data
            except (TokenError, User.DoesNotExist):
                pass
        
        return response


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=OTPVerificationSerializer,
        responses={
            200: "Email verified successfully",
            400: "Invalid or expired OTP",
        },
        operation_description="Verify email using OTP code (no links required)"
    )
    def post(self, request):
        try:
            # Handle both frontend format and standard format
            data = request.data.copy()
            
            # Convert frontend format to standard format if needed
            if 'otp' in data and 'otp_code' not in data:
                data['otp_code'] = data['otp']
            
            if 'purpose' in data and 'otp_type' not in data:
                data['otp_type'] = data['purpose']
            
            # If otp_type not provided, default to email_verification
            if 'otp_type' not in data:
                data['otp_type'] = 'email_verification'
            
            serializer = OTPVerificationSerializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            otp_code = serializer.validated_data['otp_code']
            email = serializer.validated_data.get('email')
            
            if not email:
                return Response({
                    'error': 'Email is required for email verification'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found with this email'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Find the OTP
            try:
                otp = OTP.objects.get(
                    user=user,
                    otp_type='email_verification',
                    otp_code=otp_code,
                    is_verified=False
                )
            except OTP.DoesNotExist:
                return Response({
                    'error': 'Invalid OTP code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify OTP
            is_valid, message = otp.verify_otp(otp_code)
            
            if is_valid:
                # Mark email as verified
                user.email_verified = True
                user.save()
                
                # Mark OTP as verified
                otp.is_verified = True
                otp.save()
                
                # Send welcome email NOW that verification is complete
                try:
                    print(f"📧 Sending welcome email to verified user: {user.email}")
                    welcome_success, welcome_message = user.send_welcome_email()
                    if welcome_success:
                        print(f"✅ Welcome email sent to {user.email}")
                    else:
                        print(f"⚠️ Welcome email failed: {welcome_message}")
                except Exception as e:
                    print(f"⚠️ Welcome email exception: {str(e)}")
                
                # Auto-login: Generate JWT tokens for verified user
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'message': 'Email verified successfully! Welcome to MedixMall!',
                    'email_verified': True,
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'welcome_email_sent': True
                })
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': f'Verification failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=ResendVerificationSerializer,
        responses={
            200: "Verification email sent",
            400: "Invalid email or already verified",
        },
        operation_description="Resend email verification"
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Send verification email with error handling
            success, message = user.send_verification_email()
            if success:
                return Response({
                    'message': 'Verification email sent successfully.'
                })
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'otp_type': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['email_verification', 'sms_verification', 'password_reset', 'login_verification'],
                    description='Type of OTP to resend'
                ),
            },
            required=['email', 'otp_type']
        ),
        responses={
            200: "OTP resent successfully",
            400: "Cannot resend OTP yet or invalid input",
            404: "User not found",
        },
        operation_description="Resend OTP after 1 minute cooldown"
    )
    def post(self, request):
        email = request.data.get('email')
        otp_type = request.data.get('otp_type', 'email_verification')
        
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'No user found with this email.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the latest OTP for this user and type
        latest_otp = OTP.objects.filter(
            user=user,
            otp_type=otp_type
        ).order_by('-created_at').first()
        
        if latest_otp:
            can_resend, message = latest_otp.can_resend()
            if not can_resend:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new OTP and send
        otp = OTP.objects.create(
            user=user,
            otp_type=otp_type,
            email=email
        )
        otp.generate_otp()
        
        if otp_type == 'email_verification':
            success, message = user.send_verification_email()
        else:
            success, message = otp.send_email_otp()
        
        if success:
            return Response({
                'message': f'New OTP sent successfully to {email}.',
                'can_resend_after': '1 minute'
            })
        else:
            return Response({
                'error': f'Failed to send OTP: {message}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OTPRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=OTPRequestSerializer,
        responses={
            200: "OTP sent successfully",
            400: "Invalid input",
        },
        operation_description="Request OTP for verification"
    )
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            otp_type = serializer.validated_data['otp_type']
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            
            # Find user by email or phone
            user = None
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response({
                        'error': 'No user found with this email.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif phone:
                try:
                    user = User.objects.get(contact=phone)
                except User.DoesNotExist:
                    return Response({
                        'error': 'No user found with this phone number.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create and send OTP
            otp = OTP.objects.create(
                user=user,
                otp_type=otp_type,
                email=email,
                phone=phone
            )
            otp.generate_otp()
            
            if email:
                success, message = otp.send_email_otp()
                if success:
                    return Response({
                        'message': 'OTP sent to email successfully.',
                        'otp_id': otp.id  # For testing purposes
                    })
                else:
                    return Response({
                        'error': message
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif phone:
                success, message = otp.send_sms_otp()
                if success:
                    return Response({
                        'message': 'OTP sent to phone successfully.',
                        'otp_id': otp.id  # For testing purposes
                    })
                else:
                    return Response({
                        'error': message
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=OTPVerificationSerializer,
        responses={
            200: "OTP verified successfully",
            400: "Invalid or expired OTP",
        },
        operation_description="Verify OTP"
    )
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp_code']
            otp_type = serializer.validated_data['otp_type']
            email = serializer.validated_data.get('email')
            phone = serializer.validated_data.get('phone')
            
            # Find latest OTP
            try:
                otp_query = OTP.objects.filter(
                    otp_type=otp_type,
                    is_verified=False
                )
                
                if email:
                    otp_query = otp_query.filter(email=email)
                elif phone:
                    otp_query = otp_query.filter(phone=phone)
                
                otp = otp_query.latest('created_at')
                
                success, message = otp.verify_otp(otp_code)
                
                if success:
                    # Handle specific OTP types
                    if otp_type == 'email_verification':
                        otp.user.email_verified = True
                        otp.user.save()
                    
                    return Response({
                        'message': message,
                        'verified': True
                    })
                else:
                    return Response({
                        'error': message,
                        'verified': False
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            except OTP.DoesNotExist:
                return Response({
                    'error': 'No valid OTP found.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        responses={
            200: "Password reset OTP sent",
            400: "Invalid email",
        },
        operation_description="Request password reset - sends OTP to email"
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate password reset OTP
            with transaction.atomic():
                # Delete any existing unverified password reset OTPs
                OTP.objects.filter(
                    user=user, 
                    otp_type='password_reset', 
                    is_verified=False
                ).delete()
                
                # Create new password reset OTP
                otp_instance = OTP.objects.create(
                    user=user,
                    otp_type='password_reset'
                )
                
                # Generate the actual OTP code
                otp_instance.generate_otp()
                
                # Send OTP email
                success, message = otp_instance.send_password_reset_email()
                
                if success:
                    return Response({
                        'message': 'Password reset OTP sent successfully to your email.'
                    })
                else:
                    return Response({
                        'error': message
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: "Password reset successful",
            400: "Invalid OTP or passwords don't match",
        },
        operation_description="Confirm password reset with OTP"
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            otp_instance = serializer.validated_data['otp_instance']
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            
            # Reset password
            user.set_password(new_password)
            user.save()
            
            # Mark OTP as verified
            otp_instance.is_verified = True
            otp_instance.verified_at = timezone.now()
            otp_instance.save()
            
            return Response({
                'message': 'Password reset successful. You can now log in with your new password.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[AUTH_HEADER_PARAMETER],
        request_body=ChangePasswordSerializer,
        responses={
            200: "Password changed successfully",
            400: "Invalid current password or passwords don't match",
            401: "Unauthorized",
        },
        operation_description="Change user password"
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            
            # Change password
            user = request.user
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password changed successfully.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPLoginRequestView(APIView):
    """Request OTP for login"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
                'contact': openapi.Schema(type=openapi.TYPE_STRING, description='Contact number'),
            },
            required=[],
            description="Provide either email or contact number"
        ),
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "message": "OTP sent successfully to your email/phone",
                        "otp_id": 123
                    }
                }
            ),
            400: "Invalid input",
            500: "Email/SMS sending failed"
        },
        operation_description="Request OTP for login via email or SMS"
    )
    def post(self, request):
        
        serializer = OTPLoginRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            contact = serializer.validated_data.get('contact')
            
            # Find user by email or contact
            if email:
                user = User.objects.get(email=email)
            else:
                # Handle potential duplicate contacts by getting the first one
                user = User.objects.filter(contact=contact).first()
                if not user:
                    return Response({
                        'error': 'User not found with this contact'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Clean up old unverified OTPs for this user and type
            OTP.objects.filter(
                user=user,
                otp_type='login_verification',
                is_verified=False
            ).delete()
            
            # Create OTP for login
            otp = OTP.objects.create(
                user=user,
                otp_type='login_verification',
                email=user.email,  # Always use email for OTP delivery
                phone=contact if contact else None
            )
            otp.generate_otp()
            
            # Always send OTP via email (even if contact was provided)
            success, message = otp.send_email_otp()
            channel = "email"
            
            if success:
                return Response({
                    'message': f'OTP sent successfully to your {channel} ({user.email})',
                    'otp_id': otp.id,
                    'channel': channel,
                    'email': user.email
                })
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPLoginVerifyView(APIView):
    """Verify OTP and login"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
                'contact': openapi.Schema(type=openapi.TYPE_STRING, description='Contact number'),
                'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description='6-digit OTP code'),
            },
            required=['otp_code'],
            description="Provide either email or contact number with OTP code"
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "user": USER_RESPONSE_EXAMPLE,
                        "message": "Login successful with OTP",
                        **TOKEN_RESPONSE
                    }
                }
            ),
            400: "Invalid OTP or input"
        },
        operation_description="Verify OTP and complete login"
    )
    def post(self, request):
        
        serializer = OTPLoginVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            contact = serializer.validated_data.get('contact')
            otp_code = serializer.validated_data['otp_code']
            
            # Find user by email or contact
            if email:
                user = User.objects.get(email=email)
                otp = OTP.objects.filter(
                    user=user,
                    email=email,
                    otp_type='login_verification',
                    is_verified=False
                ).order_by('-created_at').first()
            else:
                user = User.objects.get(contact=contact)
                otp = OTP.objects.filter(
                    user=user,
                    phone=contact,
                    otp_type='login_verification',
                    is_verified=False
                ).order_by('-created_at').first()
            
            if not otp:
                return Response({
                    'error': 'No valid OTP found. Please request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if otp.verify_otp(otp_code):
                # Mark email as verified since OTP login acts as verification
                if not user.email_verified:
                    user.email_verified = True
                    user.save()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'user': UserSerializer(user).data,
                    'message': 'Login successful with OTP',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            else:
                return Response({
                    'error': 'Invalid OTP or OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginChoiceView(APIView):
    """Unified login endpoint - supports both password and OTP login"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
                'contact': openapi.Schema(type=openapi.TYPE_STRING, description='Contact number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Password (required for password login)'),
                'login_type': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['password', 'otp'],
                    description='Login method: "password" or "otp"'
                ),
            },
            required=['login_type'],
            description="Choose login method and provide appropriate credentials"
        ),
        responses={
            200: openapi.Response(
                description="Login method processed",
                examples={
                    "application/json": {
                        "password_login": {
                            "user": USER_RESPONSE_EXAMPLE,
                            "message": "Login successful",
                            **TOKEN_RESPONSE
                        },
                        "otp_request": {
                            "message": "OTP sent successfully to your email/phone",
                            "otp_id": 123,
                            "channel": "email"
                        }
                    }
                }
            ),
            400: "Invalid input or credentials"
        },
        operation_description="Unified login endpoint - use 'password' for traditional login or 'otp' to request OTP"
    )
    def post(self, request):
        
        serializer = LoginChoiceSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            contact = serializer.validated_data.get('contact')
            password = serializer.validated_data.get('password')
            login_type = serializer.validated_data['login_type']
            
            # Find user by email or contact
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response({
                        'error': 'No account found with this email address'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    user = User.objects.get(contact=contact)
                except User.DoesNotExist:
                    return Response({
                        'error': 'No account found with this contact number'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if login_type == 'password':
                # Password-based login
                if not password:
                    return Response({
                        'error': 'Password is required for password login'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Authenticate user
                auth_user = authenticate(
                    request=request,
                    username=user.email,  # Use email as username
                    password=password
                )
                
                if auth_user:
                    refresh = RefreshToken.for_user(auth_user)
                    return Response({
                        'user': UserSerializer(auth_user).data,
                        'message': 'Login successful',
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    })
                else:
                    return Response({
                        'error': 'Invalid password'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif login_type == 'otp':
                # Clean up any existing OTPs for this user and type
                OTP.objects.filter(
                    user=user,
                    otp_type='login_verification'
                ).delete()
                
                # OTP-based login - send OTP
                otp = OTP.objects.create(
                    user=user,
                    otp_type='login_verification',
                    email=email if email else None,
                    phone=contact if contact else None
                )
                otp.generate_otp()
                
                # Send OTP
                if email:
                    success, message = otp.send_email_otp()
                    channel = "email"
                else:
                    success, message = otp.send_sms_otp()
                    channel = "SMS"
                
                if success:
                    return Response({
                        'message': f'OTP sent successfully to your {channel}',
                        'otp_id': otp.id,
                        'channel': channel,
                        'next_step': 'Use /api/accounts/login/otp/verify/ to complete login'
                    })
                else:
                    return Response({
                        'error': message
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Supplier Duty Management Views
class SupplierDutyStatusView(APIView):
    """
    Get current duty status for suppliers
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current duty status. Only suppliers can access this endpoint.",
        operation_summary="Get Supplier Duty Status",
        tags=['Supplier - Duty Management'],
        manual_parameters=[AUTH_HEADER_PARAMETER],
        responses={
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'is_on_duty': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Current duty status"),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Status message"),
                    }
                )
            ),
            403: openapi.Response('Forbidden - Only suppliers can access'),
        }
    )
    def get(self, request):
        if request.user.role != 'supplier':
            return Response({
                'error': 'Only suppliers can access duty status'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'is_on_duty': request.user.is_on_duty,
            'message': f"You are currently {'ON DUTY' if request.user.is_on_duty else 'OFF DUTY'}. Your products are {'visible' if request.user.is_on_duty else 'hidden'} to customers."
        })


class SupplierDutyToggleView(APIView):
    """
    Toggle supplier duty status (on/off)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Toggle duty status. When OFF, supplier's products won't show in public listings. When ON, products are visible.",
        operation_summary="Toggle Supplier Duty Status",
        tags=['Supplier - Duty Management'],
        manual_parameters=[AUTH_HEADER_PARAMETER],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_on_duty': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, 
                    description="Set duty status: true for ON DUTY, false for OFF DUTY",
                    example=True
                ),
            },
            required=['is_on_duty']
        ),
        responses={
            200: openapi.Response(
                'Success',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'is_on_duty': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="New duty status"),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Status change message"),
                        'products_affected': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of products affected"),
                    }
                )
            ),
            403: openapi.Response('Forbidden - Only suppliers can toggle duty'),
            400: openapi.Response('Bad Request - Invalid data'),
        }
    )
    def post(self, request):
        if request.user.role != 'supplier':
            return Response({
                'error': 'Only suppliers can toggle duty status'
            }, status=status.HTTP_403_FORBIDDEN)
        
        is_on_duty = request.data.get('is_on_duty')
        if is_on_duty is None:
            return Response({
                'error': 'is_on_duty field is required (true/false)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Count supplier's products
        from products.models import Product
        products_count = Product.objects.filter(
            created_by=request.user,
            status='published',
            is_publish=True
        ).count()
        
        # Update duty status
        request.user.is_on_duty = bool(is_on_duty)
        request.user.save()
        
        status_text = "ON DUTY" if is_on_duty else "OFF DUTY"
        visibility_text = "visible to" if is_on_duty else "hidden from"
        
        return Response({
            'is_on_duty': request.user.is_on_duty,
            'message': f"You are now {status_text}. Your {products_count} products are now {visibility_text} customers.",
            'products_affected': products_count
        })


# Supplier Request System Views

class SupplierRequestView(APIView):
    """
    Submit a supplier account request
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Submit a request to become a supplier. Admin approval required.",
        operation_summary="Request Supplier Account",
        tags=['Supplier - Account Request'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                'contact': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'company_name': openapi.Schema(type=openapi.TYPE_STRING),
                'company_address': openapi.Schema(type=openapi.TYPE_STRING),
                'gst_number': openapi.Schema(type=openapi.TYPE_STRING),
                'pan_number': openapi.Schema(type=openapi.TYPE_STRING),
                'business_license': openapi.Schema(type=openapi.TYPE_STRING, description="ImageKit URL"),
                'gst_certificate': openapi.Schema(type=openapi.TYPE_STRING, description="ImageKit URL"),
                'product_categories': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'full_name', 'contact', 'password', 'password2', 'company_name', 'gst_number']
        ),
        responses={
            201: openapi.Response('Request submitted successfully'),
            400: openapi.Response('Bad Request - Invalid data'),
        }
    )
    def post(self, request):
        from .serializers import SupplierRequestSerializer
        
        serializer = SupplierRequestSerializer(data=request.data)
        if serializer.is_valid():
            supplier_request = serializer.save()
            
            # Send notification to admins
            self.notify_admins(supplier_request)
            
            return Response({
                'message': 'Supplier request submitted successfully. You will be notified once reviewed.',
                'request_id': supplier_request.id,
                'status': supplier_request.status
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def notify_admins(self, supplier_request):
        """Notify all admin users about new supplier request"""
        try:
            admin_users = User.objects.filter(role='admin', is_active=True)
            admin_emails = [admin.email for admin in admin_users]
            
            if admin_emails:
                subject = f'New Supplier Request - {supplier_request.company_name}'
                message = f"""
New supplier account request received:

Company: {supplier_request.company_name}
Contact Person: {supplier_request.full_name}
Email: {supplier_request.email}
Contact: {supplier_request.contact}
GST Number: {supplier_request.gst_number}

Please review and take appropriate action in the admin panel.

Best regards,
MedixMall System
                """
                
                send_mail(
                    subject, message,
                    settings.EMAIL_HOST_USER,
                    admin_emails,
                    fail_silently=True
                )
                print(f"✅ Admin notification sent for supplier request: {supplier_request.id}")
        except Exception as e:
            print(f"❌ Failed to send admin notification: {str(e)}")


class SupplierRequestStatusView(APIView):
    """
    Check status of supplier request
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Check the status of a supplier account request",
        operation_summary="Check Supplier Request Status",
        tags=['Supplier - Account Request'],
        manual_parameters=[
            openapi.Parameter('email', openapi.IN_QUERY, description="Email address", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response('Request status retrieved'),
            404: openapi.Response('Request not found'),
        }
    )
    def get(self, request):
        from .serializers import SupplierRequestStatusSerializer
        email = request.query_params.get('email')
        
        if not email:
            return Response({
                'error': 'Email parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            supplier_request = SupplierRequest.objects.get(email=email)
            serializer = SupplierRequestStatusSerializer(supplier_request)
            return Response(serializer.data)
        except SupplierRequest.DoesNotExist:
            return Response({
                'error': 'No supplier request found with this email'
            }, status=status.HTTP_404_NOT_FOUND)


class AdminSupplierRequestListView(APIView):
    """
    Admin view to list all supplier requests
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all supplier account requests (Admin only)",
        operation_summary="List Supplier Requests (Admin)",
        tags=['Admin - Supplier Management'],
        manual_parameters=[
            AUTH_HEADER_PARAMETER,
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING)
        ],
        responses={
            200: openapi.Response('Supplier requests retrieved'),
            403: openapi.Response('Forbidden - Admin access required'),
        }
    )
    def get(self, request):
        if request.user.role != 'admin':
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from .serializers import SupplierRequestDetailSerializer
        
        queryset = SupplierRequest.objects.all()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = SupplierRequestDetailSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'requests': serializer.data
        })


class AdminSupplierRequestActionView(APIView):
    """
    Admin view to approve/reject supplier requests
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Approve, reject, or mark supplier request under review (Admin only)",
        operation_summary="Handle Supplier Request (Admin)",
        tags=['Admin - Supplier Management'],
        manual_parameters=[AUTH_HEADER_PARAMETER],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'reject', 'under_review']),
                'reason': openapi.Schema(type=openapi.TYPE_STRING, description="Required for rejection"),
                'admin_notes': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['action']
        ),
        responses={
            200: openapi.Response('Action completed successfully'),
            400: openapi.Response('Bad Request'),
            403: openapi.Response('Forbidden - Admin access required'),
            404: openapi.Response('Request not found'),
        }
    )
    def post(self, request, request_id):
        if request.user.role != 'admin':
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from .serializers import SupplierRequestActionSerializer
        
        try:
            supplier_request = SupplierRequest.objects.get(id=request_id)
        except SupplierRequest.DoesNotExist:
            return Response({
                'error': 'Supplier request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SupplierRequestActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        admin_notes = serializer.validated_data.get('admin_notes')
        
        if action == 'approve':
            success, message = supplier_request.approve(request.user, admin_notes)
        elif action == 'reject':
            reason = serializer.validated_data['reason']
            success, message = supplier_request.reject(request.user, reason, admin_notes)
        elif action == 'under_review':
            supplier_request.status = 'under_review'
            supplier_request.reviewed_by = request.user
            supplier_request.reviewed_at = timezone.now()
            if admin_notes:
                supplier_request.admin_notes = admin_notes
            supplier_request.save()
            success, message = True, "Request marked as under review"
        
        if success:
            return Response({
                'message': message,
                'status': supplier_request.status
            })
        else:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)


# Google Social Authentication Views

class GoogleAuthView(APIView):
    """
    Google OAuth2 authentication endpoint
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Authenticate or register user using Google OAuth2",
        operation_summary="Google Social Login",
        tags=['Authentication - Social'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id_token': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Google ID token from frontend"
                ),
                'role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['user', 'supplier'],
                    description="User role (defaults to 'user')",
                    default='user'
                ),
            },
            required=['id_token']
        ),
        responses={
            200: openapi.Response(
                'Login successful',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_new_user': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: openapi.Response('Invalid token or authentication failed'),
        }
    )
    def post(self, request):
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        import os
        
        id_token_str = request.data.get('id_token')
        role = request.data.get('role', 'user')  # Default to 'user'
        
        if not id_token_str:
            return Response({
                'error': 'Google ID token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate role
        if role not in ['user', 'supplier']:
            return Response({
                'error': 'Invalid role. Only "user" and "supplier" are allowed.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify the token
            CLIENT_ID = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
            if not CLIENT_ID:
                return Response({
                    'error': 'Google OAuth not configured properly'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                google_requests.Request(), 
                CLIENT_ID
            )
            
            # Extract user information
            email = idinfo.get('email')
            full_name = idinfo.get('name', '')
            google_id = idinfo.get('sub')
            email_verified = idinfo.get('email_verified', False)
            
            if not email:
                return Response({
                    'error': 'Email not provided by Google'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user already exists
            try:
                user = User.objects.get(email=email)
                is_new_user = False
                
                # Update user info if needed
                if not user.full_name and full_name:
                    user.full_name = full_name
                
                # Auto-verify email since it's verified by Google
                if email_verified and not user.email_verified:
                    user.email_verified = True
                
                user.save()
                
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    role=role,
                    email_verified=email_verified  # Trust Google's verification
                )
                is_new_user = True
                
                # Send welcome email for new users
                if is_new_user:
                    try:
                        user.send_welcome_email()
                    except Exception as e:
                        print(f"⚠️ Failed to send welcome email: {str(e)}")
            
            # Sync guest cart to user's cart
            sync_guest_cart_to_user(request, user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'is_new_user': is_new_user,
                'message': f"Welcome {'back' if not is_new_user else 'to MedixMall'}!"
            })
            
        except ValueError as e:
            # Token verification failed
            return Response({
                'error': 'Invalid Google token',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Authentication failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RateLimitStatusView(APIView):
    """
    Rate Limit Status View - Frontend Session Management
    Returns user authentication status and session information
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user session and rate limit status",
        responses={
            200: openapi.Response(
                description="Session status retrieved successfully",
                examples={
                    "application/json": {
                        "authenticated": True,
                        "user": {
                            "id": 28,
                            "email": "user@example.com",
                            "full_name": "User Name",
                            "role": "user",
                            "email_verified": True
                        },
                        "rate_limit": {
                            "remaining": 1000,
                            "reset_time": "2025-10-06T02:00:00Z"
                        },
                        "session_valid": True
                    }
                }
            ),
            401: openapi.Response(
                description="Authentication required",
                examples={
                    "application/json": {
                        "authenticated": False,
                        "error": "Authentication credentials not provided"
                    }
                }
            )
        },
        manual_parameters=[AUTH_HEADER_PARAMETER]
    )
    def get(self, request):
        """Get current session status and rate limit information"""
        try:
            user = request.user
            
            # Calculate rate limit info (mock implementation)
            from django.utils import timezone
            import datetime
            
            reset_time = timezone.now() + datetime.timedelta(hours=1)
            
            return Response({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'contact': user.contact,
                    'role': user.role,
                    'has_address': user.has_address,
                    'medixmall_mode': user.medixmall_mode,
                    'email_verified': user.email_verified
                },
                'rate_limit': {
                    'remaining': 1000,  # Mock remaining requests
                    'reset_time': reset_time.isoformat()
                },
                'session_valid': True,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'authenticated': False,
                'error': str(e),
                'session_valid': False
            }, status=status.HTTP_401_UNAUTHORIZED)
