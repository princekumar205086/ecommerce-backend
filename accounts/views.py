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
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from cart.models import Cart, CartItem
from .models import User, OTP, PasswordResetToken
from .serializers import (
    UserRegisterSerializer, UserLoginSerializer, UserSerializer, 
    UserAddressSerializer, UpdateAddressSerializer, MedixMallModeSerializer,
    OTPVerificationSerializer, OTPRequestSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer, ResendVerificationSerializer,
    ChangePasswordSerializer
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
                user = serializer.save()
                user.role = role
                user.save()

                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'message': 'Registration successful. Please check your email for verification.',
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
        responses={
            200: "Email verified successfully",
            400: "Invalid or expired token",
        },
        operation_description="Verify email using verification token"
    )
    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)
            
            # Check if token is expired (24 hours)
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timezone.timedelta(hours=24)
                if timezone.now() > expiry_time:
                    return Response({
                        'error': 'Verification link has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify email
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save()
            
            return Response({
                'message': 'Email verified successfully. You can now log in.'
            })
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid verification token.'
            }, status=status.HTTP_400_BAD_REQUEST)


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
            user.send_verification_email()
            
            return Response({
                'message': 'Verification email sent successfully.'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                otp.send_email_otp()
                return Response({
                    'message': 'OTP sent to email successfully.',
                    'otp_id': otp.id  # For testing purposes
                })
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
            200: "Password reset email sent",
            400: "Invalid email",
        },
        operation_description="Request password reset"
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate password reset token
            reset_token = PasswordResetToken.generate_for_user(user)
            reset_token.send_reset_email()
            
            return Response({
                'message': 'Password reset email sent successfully.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: "Password reset successful",
            400: "Invalid token or passwords don't match",
        },
        operation_description="Confirm password reset with token"
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            reset_token = serializer.validated_data['reset_token']
            new_password = serializer.validated_data['new_password']
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
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
