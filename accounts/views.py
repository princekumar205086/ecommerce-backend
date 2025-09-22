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
from .models import User, OTP, PasswordResetToken
from .serializers import (
    UserRegisterSerializer, UserLoginSerializer, UserSerializer, 
    UserAddressSerializer, UpdateAddressSerializer, MedixMallModeSerializer,
    OTPVerificationSerializer, OTPRequestSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer, ResendVerificationSerializer,
    ChangePasswordSerializer, OTPLoginRequestSerializer, OTPLoginVerifySerializer, 
    LoginChoiceSerializer
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
            403: "Email not verified",
        },
        operation_description="Authenticate user and get access token. Email must be verified."
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Check if email is verified
        if not user.email_verified:
            return Response({
                'error': 'Email not verified. Please verify your email before logging in.',
                'email_verified': False
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
                    'channel': channel
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
