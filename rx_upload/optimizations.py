# Performance Optimizations for RX Upload System

from django.core.cache import cache
from django.db.models import Count, Q, F, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import PrescriptionUpload, VerifierWorkload, VerificationActivity
from accounts.models import User
from .advanced_optimizations import AdvancedRXOptimizer, BackgroundTaskManager


class RXSystemOptimizer:
    """Enhanced performance optimization utilities for RX Upload System"""
    
    CACHE_TIMEOUT = 300  # 5 minutes
    WORKLOAD_CACHE_KEY = "rx_workload_stats_{}"
    DASHBOARD_CACHE_KEY = "rx_dashboard_stats_{}"
    PENDING_COUNT_CACHE_KEY = "rx_pending_count"
    
    @classmethod
    def get_cached_workload_stats(cls, verifier_id):
        """Get enhanced cached verifier workload statistics with advanced analytics"""
        # Use advanced optimizer for comprehensive stats
        return AdvancedRXOptimizer.get_enhanced_workload_stats(verifier_id)
    
    @classmethod
    def get_enhanced_system_health(cls):
        """Get enhanced system health metrics with advanced monitoring"""
        return AdvancedRXOptimizer.get_system_health_metrics()
    
    @classmethod
    def run_comprehensive_optimization(cls):
        """Run comprehensive system optimization with background tasks"""
        # Start background optimization tasks
        background_manager = BackgroundTaskManager()
        
        # Schedule database optimization
        db_task = background_manager.schedule_optimization_task('database_optimization')
        
        # Schedule cache refresh
        cache_task = background_manager.schedule_optimization_task('cache_refresh', delay_seconds=5)
        
        # Schedule system health check
        health_task = background_manager.schedule_optimization_task('system_health_check', delay_seconds=10)
        
        # Immediate optimizations
        cls.bulk_update_workloads()
        cls.invalidate_all_cache()
        
        return {
            'database_optimization': db_task,
            'cache_refresh': cache_task,
            'system_health_check': health_task,
            'immediate_optimization': 'completed'
        }
    
    @classmethod
    def get_advanced_analytics(cls, days=30):
        """Get advanced performance analytics with predictions"""
        return AdvancedRXOptimizer.get_performance_analytics(days)
    
    @classmethod
    def get_cached_workload_stats_legacy(cls, verifier_id):
        """Legacy method - maintained for compatibility"""
        cache_key = cls.WORKLOAD_CACHE_KEY.format(verifier_id)
        stats = cache.get(cache_key)
        
        if stats is None:
            try:
                workload = VerifierWorkload.objects.get(verifier_id=verifier_id)
                workload.update_workload()
                
                stats = {
                    'pending_count': workload.pending_count,
                    'in_review_count': workload.in_review_count,
                    'total_verified': workload.total_verified,
                    'total_approved': workload.total_approved,
                    'total_rejected': workload.total_rejected,
                    'approval_rate': workload.approval_rate,
                    'average_processing_time': float(workload.average_processing_time),
                    'is_available': workload.is_available,
                    'can_accept_more': workload.can_accept_more,
                    'current_daily_count': workload.current_daily_count,
                    'max_daily_capacity': workload.max_daily_capacity,
                }
                
                cache.set(cache_key, stats, cls.CACHE_TIMEOUT)
            except VerifierWorkload.DoesNotExist:
                stats = {}
        
        return stats
    
    @classmethod
    def get_cached_dashboard_stats(cls, user_role=None, verifier_id=None):
        """Get cached dashboard statistics"""
        cache_key = cls.DASHBOARD_CACHE_KEY.format(verifier_id or 'admin')
        stats = cache.get(cache_key)
        
        if stats is None:
            # Build queryset based on user role
            if user_role == 'rx_verifier' and verifier_id:
                base_queryset = PrescriptionUpload.objects.filter(verified_by_id=verifier_id)
                all_prescriptions = PrescriptionUpload.objects.all()
            else:
                base_queryset = PrescriptionUpload.objects.all()
                all_prescriptions = base_queryset
            
            # Get counts using aggregation for efficiency
            status_counts = all_prescriptions.aggregate(
                pending=Count('id', filter=Q(verification_status='pending')),
                in_review=Count('id', filter=Q(verification_status='in_review')),
                approved=Count('id', filter=Q(verification_status='approved')),
                rejected=Count('id', filter=Q(verification_status='rejected')),
                clarification_needed=Count('id', filter=Q(verification_status='clarification_needed')),
                urgent=Count('id', filter=Q(
                    is_urgent=True, 
                    verification_status__in=['pending', 'in_review']
                )),
            )
            
            # Calculate overdue prescriptions
            overdue_threshold = timezone.now() - timedelta(hours=24)
            overdue_count = all_prescriptions.filter(
                uploaded_at__lt=overdue_threshold,
                verification_status__in=['pending', 'in_review']
            ).count()
            
            status_counts['overdue'] = overdue_count
            
            stats = {
                'counts': status_counts,
                'last_updated': timezone.now().isoformat()
            }
            
            cache.set(cache_key, stats, cls.CACHE_TIMEOUT)
        
        return stats
    
    @classmethod
    def get_cached_pending_count(cls):
        """Get cached count of pending prescriptions"""
        count = cache.get(cls.PENDING_COUNT_CACHE_KEY)
        
        if count is None:
            count = PrescriptionUpload.objects.filter(
                verification_status='pending'
            ).count()
            cache.set(cls.PENDING_COUNT_CACHE_KEY, count, cls.CACHE_TIMEOUT)
        
        return count
    
    @classmethod
    def invalidate_verifier_cache(cls, verifier_id):
        """Invalidate cached data for a specific verifier"""
        cache.delete(cls.WORKLOAD_CACHE_KEY.format(verifier_id))
        cache.delete(cls.DASHBOARD_CACHE_KEY.format(verifier_id))
        cache.delete(cls.PENDING_COUNT_CACHE_KEY)
    
    @classmethod
    def invalidate_all_cache(cls):
        """Invalidate all RX system cache"""
        # Get all verifier IDs
        verifier_ids = User.objects.filter(role='rx_verifier').values_list('id', flat=True)
        
        for verifier_id in verifier_ids:
            cls.invalidate_verifier_cache(verifier_id)
        
        cache.delete(cls.DASHBOARD_CACHE_KEY.format('admin'))
    
    @classmethod
    def get_prescription_analytics(cls, date_range_days=30):
        """Get comprehensive prescription analytics"""
        since_date = timezone.now() - timedelta(days=date_range_days)
        
        # Performance metrics using database aggregation
        analytics = PrescriptionUpload.objects.filter(
            uploaded_at__gte=since_date
        ).aggregate(
            total_prescriptions=Count('id'),
            total_verified=Count('id', filter=Q(verification_status__in=['approved', 'rejected'])),
            total_approved=Count('id', filter=Q(verification_status='approved')),
            total_rejected=Count('id', filter=Q(verification_status='rejected')),
            avg_processing_time=Avg('processing_time'),
            urgent_prescriptions=Count('id', filter=Q(is_urgent=True)),
        )
        
        # Calculate approval rate
        if analytics['total_verified'] > 0:
            analytics['approval_rate'] = round(
                (analytics['total_approved'] / analytics['total_verified']) * 100, 2
            )
        else:
            analytics['approval_rate'] = 0
        
        # Verifier performance
        verifier_performance = VerifierWorkload.objects.filter(
            verifier__role='rx_verifier'
        ).aggregate(
            avg_approval_rate=Avg('approval_rate'),
            avg_processing_time=Avg('average_processing_time'),
            total_verifiers=Count('id'),
            active_verifiers=Count('id', filter=Q(is_available=True)),
        )
        
        analytics.update(verifier_performance)
        
        return analytics
    
    @classmethod
    def get_top_performing_verifiers(cls, limit=5):
        """Get top performing verifiers by approval rate and speed"""
        return VerifierWorkload.objects.filter(
            verifier__role='rx_verifier',
            total_verified__gte=10  # At least 10 verifications
        ).select_related('verifier').order_by(
            '-approval_rate', 
            'average_processing_time'
        )[:limit]
    
    @classmethod
    def get_system_health_status(cls):
        """Get overall system health indicators"""
        pending_count = cls.get_cached_pending_count()
        
        # Get overdue prescriptions
        overdue_threshold = timezone.now() - timedelta(hours=24)
        overdue_count = PrescriptionUpload.objects.filter(
            uploaded_at__lt=overdue_threshold,
            verification_status__in=['pending', 'in_review']
        ).count()
        
        # Get available verifiers
        available_verifiers = VerifierWorkload.objects.filter(
            is_available=True,
            verifier__role='rx_verifier'
        ).count()
        
        # Calculate health score
        health_score = 100
        
        if pending_count > 50:
            health_score -= 20
        elif pending_count > 25:
            health_score -= 10
        
        if overdue_count > 10:
            health_score -= 30
        elif overdue_count > 5:
            health_score -= 15
        
        if available_verifiers == 0:
            health_score -= 40
        elif available_verifiers < 2:
            health_score -= 20
        
        health_status = "Excellent"
        if health_score < 60:
            health_status = "Critical"
        elif health_score < 80:
            health_status = "Warning"
        elif health_score < 95:
            health_status = "Good"
        
        return {
            'health_score': max(0, health_score),
            'health_status': health_status,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
            'available_verifiers': available_verifiers,
            'recommendations': cls._get_health_recommendations(
                pending_count, overdue_count, available_verifiers
            )
        }
    
    @classmethod
    def _get_health_recommendations(cls, pending_count, overdue_count, available_verifiers):
        """Get system health recommendations"""
        recommendations = []
        
        if pending_count > 50:
            recommendations.append("High pending prescription volume - consider adding more verifiers")
        
        if overdue_count > 5:
            recommendations.append("Multiple overdue prescriptions - urgent attention required")
        
        if available_verifiers < 2:
            recommendations.append("Limited verifier availability - ensure adequate coverage")
        
        if not recommendations:
            recommendations.append("System operating optimally")
        
        return recommendations
    
    @classmethod
    def bulk_update_workloads(cls):
        """Bulk update all verifier workloads efficiently"""
        return RXDatabaseOptimizer.bulk_update_workloads()


class RXDatabaseOptimizer:
    """Database optimization utilities"""
    
    @classmethod
    def optimize_prescription_queries(cls, queryset):
        """Optimize prescription querysets with select_related and prefetch_related"""
        return queryset.select_related(
            'customer',
            'verified_by'
        ).prefetch_related(
            'medications',
            'activities'
        )
    
    @classmethod
    def get_optimized_prescription_list(cls, user, filters=None):
        """Get optimized prescription list with proper filtering"""
        # Base queryset
        if user.role in ['rx_verifier', 'admin']:
            queryset = PrescriptionUpload.objects.all()
        else:
            queryset = PrescriptionUpload.objects.filter(customer=user)
        
        # Apply filters
        if filters:
            if 'verification_status' in filters:
                queryset = queryset.filter(verification_status=filters['verification_status'])
            
            if 'is_urgent' in filters:
                # Handle string boolean values
                is_urgent = filters['is_urgent']
                if isinstance(is_urgent, str):
                    is_urgent = is_urgent.lower() in ['true', '1', 'yes']
                else:
                    is_urgent = bool(is_urgent)
                queryset = queryset.filter(is_urgent=is_urgent)
            
            if 'verified_by' in filters:
                queryset = queryset.filter(verified_by=filters['verified_by'])
            
            if 'assigned_to_me' in filters and user.role == 'rx_verifier':
                queryset = queryset.filter(verified_by=user)
        
        # Optimize with relations
        return cls.optimize_prescription_queries(queryset)
    
    @classmethod
    def bulk_update_workloads(cls):
        """Bulk update all verifier workloads efficiently"""
        verifier_ids = User.objects.filter(role='rx_verifier').values_list('id', flat=True)
        
        for verifier_id in verifier_ids:
            try:
                workload = VerifierWorkload.objects.get(verifier_id=verifier_id)
                workload.update_workload()
                # Clear cache for this verifier
                RXSystemOptimizer.invalidate_verifier_cache(verifier_id)
            except VerifierWorkload.DoesNotExist:
                continue
    
    @classmethod
    def cleanup_old_activities(cls, days=90):
        """Cleanup old verification activities to maintain database performance"""
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = VerificationActivity.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        return deleted_count[0] if deleted_count else 0


# Performance monitoring decorator
def cache_invalidate_on_prescription_change(func):
    """Decorator to invalidate cache when prescription data changes"""
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        
        # Invalidate relevant cache
        if hasattr(self, 'verified_by') and self.verified_by:
            RXSystemOptimizer.invalidate_verifier_cache(self.verified_by.id)
        
        RXSystemOptimizer.invalidate_all_cache()
        
        return result
    return wrapper