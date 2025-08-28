"""
Shipping API Views
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Shipment, ShippingRate, ShippingEvent, ReturnRequest
from .serializers import (
    ShipmentSerializer, ShippingRateSerializer, 
    CreateShipmentSerializer, TrackingSerializer,
    ReturnRequestSerializer
)
from shiprocket_service import shiprocket_api

logger = logging.getLogger(__name__)

class ShipRocketTestView(APIView):
    """
    Test ShipRocket API connectivity
    """
    permission_classes = [AllowAny]  # For UAT testing
    
    @swagger_auto_schema(
        operation_summary="Test ShipRocket API Connection",
        operation_description="Test the ShipRocket API connectivity and authentication in UAT mode",
        responses={
            200: openapi.Response(
                description="Connection test result",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "ShipRocket API connection successful",
                        "data": "serviceability_data"
                    }
                }
            )
        },
        tags=['Shipping - Testing']
    )
    def get(self, request):
        """Test ShipRocket API connection"""
        try:
            result = shiprocket_api.test_connection()
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"ShipRocket test error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Test failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckServiceabilityView(APIView):
    """
    Check shipping serviceability between pincodes
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Check Shipping Serviceability",
        operation_description="Check if delivery is available between pickup and delivery pincodes",
        manual_parameters=[
            openapi.Parameter('pickup_pincode', openapi.IN_QUERY, description="Pickup pincode", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('delivery_pincode', openapi.IN_QUERY, description="Delivery pincode", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('weight', openapi.IN_QUERY, description="Package weight in kg", type=openapi.TYPE_NUMBER, default=1.0),
            openapi.Parameter('cod', openapi.IN_QUERY, description="COD required", type=openapi.TYPE_BOOLEAN, default=False),
        ],
        responses={
            200: openapi.Response(
                description="Serviceability check result",
                examples={
                    "application/json": {
                        "success": True,
                        "serviceable": True,
                        "couriers": [
                            {
                                "courier_company_id": "1",
                                "courier_name": "Bluedart",
                                "freight_charge": 89.0,
                                "cod_charge": 25.0,
                                "total_charge": 114.0,
                                "delivery_days": "2-3 days"
                            }
                        ],
                        "message": "Serviceability check completed"
                    }
                }
            )
        },
        tags=['Shipping - Serviceability']
    )
    def get(self, request):
        """Check serviceability between pincodes"""
        pickup_pincode = request.query_params.get('pickup_pincode')
        delivery_pincode = request.query_params.get('delivery_pincode')
        weight = float(request.query_params.get('weight', 1.0))
        cod = request.query_params.get('cod', 'false').lower() == 'true'
        
        if not pickup_pincode or not delivery_pincode:
            return Response({
                'success': False,
                'message': 'pickup_pincode and delivery_pincode are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = shiprocket_api.check_serviceability(
                pickup_pincode, delivery_pincode, weight, cod
            )
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Serviceability check error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Serviceability check failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ShippingRatesView(APIView):
    """
    Get shipping rates for delivery
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Get Shipping Rates",
        operation_description="Get shipping rates from different courier partners",
        manual_parameters=[
            openapi.Parameter('pickup_pincode', openapi.IN_QUERY, description="Pickup pincode", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('delivery_pincode', openapi.IN_QUERY, description="Delivery pincode", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('weight', openapi.IN_QUERY, description="Package weight in kg", type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter('length', openapi.IN_QUERY, description="Package length in cm", type=openapi.TYPE_NUMBER, default=10),
            openapi.Parameter('breadth', openapi.IN_QUERY, description="Package breadth in cm", type=openapi.TYPE_NUMBER, default=10),
            openapi.Parameter('height', openapi.IN_QUERY, description="Package height in cm", type=openapi.TYPE_NUMBER, default=5),
        ],
        responses={
            200: openapi.Response(
                description="Shipping rates",
                examples={
                    "application/json": {
                        "success": True,
                        "rates": [
                            {
                                "courier_name": "Bluedart",
                                "freight_charge": 89.0,
                                "total_charge": 114.0,
                                "delivery_days": "2-3 days"
                            }
                        ],
                        "cheapest": {
                            "courier_name": "Delhivery",
                            "freight_charge": 75.0,
                            "total_charge": 100.0
                        },
                        "message": "Shipping rates retrieved successfully"
                    }
                }
            )
        },
        tags=['Shipping - Rates']
    )
    def get(self, request):
        """Get shipping rates"""
        pickup_pincode = request.query_params.get('pickup_pincode')
        delivery_pincode = request.query_params.get('delivery_pincode')
        weight = request.query_params.get('weight')
        length = float(request.query_params.get('length', 10))
        breadth = float(request.query_params.get('breadth', 10))
        height = float(request.query_params.get('height', 5))
        
        if not all([pickup_pincode, delivery_pincode, weight]):
            return Response({
                'success': False,
                'message': 'pickup_pincode, delivery_pincode, and weight are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            weight = float(weight)
            dimensions = {'length': length, 'breadth': breadth, 'height': height}
            
            result = shiprocket_api.get_shipping_rates(
                pickup_pincode, delivery_pincode, weight, dimensions
            )
            return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Shipping rates error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Rate calculation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateShipmentView(APIView):
    """
    Create a new shipment
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Create Shipment",
        operation_description="Create a new shipment order with ShipRocket",
        request_body=CreateShipmentSerializer,
        responses={
            201: openapi.Response(
                description="Shipment created successfully",
                schema=ShipmentSerializer,
                examples={
                    "application/json": {
                        "success": True,
                        "shipment": {
                            "id": 1,
                            "order_id": "ORD001",
                            "awb_code": "SR123456789",
                            "status": "confirmed"
                        },
                        "message": "Shipment created successfully"
                    }
                }
            )
        },
        tags=['Shipping - Orders']
    )
    def post(self, request):
        """Create a new shipment"""
        serializer = CreateShipmentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Create shipment with ShipRocket
                validated_data = serializer.validated_data
                if not validated_data:
                    return Response({
                        'success': False,
                        'error': 'No validated data received'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                result = shiprocket_api.create_order(validated_data)
                
                if result['success']:
                    # Save shipment to database - create dict manually
                    shipment_data = {
                        'user': request.user,
                        'order_id': validated_data.get('order_id'),
                        'customer_name': validated_data.get('customer_name'),
                        'customer_email': validated_data.get('customer_email'),
                        'customer_phone': validated_data.get('customer_phone'),
                        'billing_address': validated_data.get('billing_address'),
                        'billing_city': validated_data.get('billing_city'),
                        'billing_state': validated_data.get('billing_state'),
                        'billing_pincode': validated_data.get('billing_pincode'),
                        'weight': validated_data.get('weight'),
                        'payment_method': validated_data.get('payment_method'),
                        'shiprocket_order_id': result.get('order_id'),
                        'shiprocket_shipment_id': result.get('shipment_id'),
                        'status': 'confirmed',
                        'shiprocket_response': result.get('data', {})
                    }
                    
                    shipment = Shipment.objects.create(**shipment_data)
                    
                    return Response({
                        'success': True,
                        'shipment': ShipmentSerializer(shipment).data,
                        'message': 'Shipment created successfully'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': result.get('message', 'Shipment creation failed'),
                        'errors': result.get('errors', {})
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                logger.error(f"Shipment creation error: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Shipment creation failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class TrackShipmentView(APIView):
    """
    Track shipment by order ID or AWB code
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Track Shipment",
        operation_description="Track shipment status by order ID or AWB code",
        manual_parameters=[
            openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID", type=openapi.TYPE_STRING),
            openapi.Parameter('awb_code', openapi.IN_QUERY, description="AWB tracking code", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Tracking information",
                schema=TrackingSerializer,
                examples={
                    "application/json": {
                        "success": True,
                        "tracking": {
                            "order_id": "ORD001",
                            "awb_code": "SR123456789",
                            "status": "in_transit",
                            "current_location": "Mumbai Hub",
                            "estimated_delivery": "2025-08-30"
                        },
                        "events": [
                            {
                                "status": "dispatched",
                                "location": "Mumbai",
                                "description": "Package dispatched",
                                "event_time": "2025-08-28T10:00:00Z"
                            }
                        ]
                    }
                }
            )
        },
        tags=['Shipping - Tracking']
    )
    def get(self, request):
        """Track shipment"""
        order_id = request.query_params.get('order_id')
        awb_code = request.query_params.get('awb_code')
        
        if not order_id and not awb_code:
            return Response({
                'success': False,
                'message': 'Either order_id or awb_code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find shipment in database
            if order_id:
                shipment = get_object_or_404(Shipment, order_id=order_id)
            else:
                shipment = get_object_or_404(Shipment, awb_code=awb_code)
            
            # Get latest tracking from ShipRocket if shipment_id exists
            if shipment.shiprocket_shipment_id:
                tracking_result = shiprocket_api.track_shipment(shipment.shiprocket_shipment_id)
                if tracking_result['success']:
                    # Update shipment with latest tracking data
                    shipment.tracking_data = tracking_result['tracking_data']
                    shipment.save()
            
            # Return tracking information
            tracking_serializer = TrackingSerializer(shipment)
            return Response({
                'success': True,
                'tracking': tracking_serializer.data,
                'events': ShippingEvent.objects.filter(shipment=shipment).values(
                    'status', 'location', 'description', 'event_time'
                )[:10]
            }, status=status.HTTP_200_OK)
            
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Shipment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Tracking error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Tracking failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ShipmentListView(generics.ListAPIView):
    """
    List user's shipments
    """
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Shipment.objects.filter(user=self.request.user).order_by('-created_at')
    
    @swagger_auto_schema(
        operation_summary="List User Shipments",
        operation_description="Get list of user's shipments",
        responses={
            200: openapi.Response(
                description="List of shipments",
                schema=ShipmentSerializer(many=True)
            )
        },
        tags=['Shipping - Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ShipmentDetailView(generics.RetrieveAPIView):
    """
    Get shipment details
    """
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'
    
    def get_queryset(self):
        return Shipment.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="Get Shipment Details",
        operation_description="Get detailed information about a specific shipment",
        responses={
            200: openapi.Response(
                description="Shipment details",
                schema=ShipmentSerializer
            )
        },
        tags=['Shipping - Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([AllowAny])  # For webhooks
def shiprocket_webhook(request):
    """
    Handle ShipRocket webhooks for status updates
    """
    try:
        webhook_data = request.data
        
        # Extract shipment information
        awb_code = webhook_data.get('awb_code')
        current_status = webhook_data.get('current_status')
        
        if awb_code:
            try:
                shipment = Shipment.objects.get(awb_code=awb_code)
                
                # Update shipment status
                shipment.status = current_status.lower().replace(' ', '_')
                shipment.current_location = webhook_data.get('current_location', '')
                shipment.updated_at = timezone.now()
                
                if current_status.lower() in ['delivered', 'delivered to consignee']:
                    shipment.delivered_at = timezone.now()
                    shipment.status = 'delivered'
                
                shipment.save()
                
                # Create shipping event
                ShippingEvent.objects.create(
                    shipment=shipment,
                    event_type='webhook_update',
                    status=current_status,
                    location=webhook_data.get('current_location', ''),
                    description=webhook_data.get('comment', ''),
                    event_time=timezone.now(),
                    source='webhook',
                    raw_data=webhook_data
                )
                
                logger.info(f"Webhook processed for AWB: {awb_code}, Status: {current_status}")
                
            except Shipment.DoesNotExist:
                logger.warning(f"Shipment not found for AWB: {awb_code}")
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return Response({'status': 'error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)