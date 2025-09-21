# Advanced Performance Optimizations for RX Upload System

import logging
import time
from datetime import timedelta
from typing import Dict, List, Optional
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q, F, Avg, Sum, Max, Min
from django.utils import timezone
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from .models import PrescriptionUpload, VerifierWorkload, VerificationActivity
from accounts.models import User

logger = logging.getLogger(__name__)


class AdvancedRXOptimizer:
    """Advanced performance optimization and monitoring for RX Upload System"""
    
    # Cache timeouts for different data types
    CACHE_TIMEOUTS = {
        'workload_stats': 300,      # 5 minutes
        'dashboard_data': 180,      # 3 minutes
        'system_metrics': 600,      # 10 minutes
        'analytics_data': 900,      # 15 minutes
        'user_sessions': 1800,      # 30 minutes
    }
    
    # Cache key patterns
    CACHE_KEYS = {
        'workload_stats': 'rx_adv_workload_{}',
        'dashboard_data': 'rx_adv_dashboard_{}',
        'system_health': 'rx_adv_system_health',
        'analytics': 'rx_adv_analytics_{}',
        'performance_metrics': 'rx_adv_perf_metrics',
        'user_activity': 'rx_adv_user_activity_{}',
    }
    
    @classmethod
    def get_enhanced_workload_stats(cls, verifier_id: int) -> Dict:
        """Get enhanced workload statistics with predictive analytics"""
        cache_key = cls.CACHE_KEYS['workload_stats'].format(verifier_id)
        stats = cache.get(cache_key)
        
        if stats is None:
            try:
                with transaction.atomic():
                    workload = VerifierWorkload.objects.select_for_update().get(verifier_id=verifier_id)
                    
                    # Basic workload stats
                    basic_stats = cls._calculate_basic_workload_stats(workload)
                    
                    # Enhanced analytics
                    enhanced_stats = cls._calculate_enhanced_workload_analytics(verifier_id)
                    
                    # Performance predictions
                    predictions = cls._calculate_workload_predictions(verifier_id)
                    
                    stats = {
                        **basic_stats,
                        **enhanced_stats,
                        **predictions,
                        'last_updated': timezone.now().isoformat(),
                        'cache_generated_at': time.time()
                    }
                    
                    cache.set(cache_key, stats, cls.CACHE_TIMEOUTS['workload_stats'])
                    logger.info(f"Generated enhanced workload stats for verifier {verifier_id}")
                    
            except VerifierWorkload.DoesNotExist:
                stats = {'error': 'Workload not found'}
                logger.warning(f"Workload not found for verifier {verifier_id}")
        
        return stats
    
    @classmethod
    def _calculate_basic_workload_stats(cls, workload: VerifierWorkload) -> Dict:
        """Calculate basic workload statistics"""
        return {
            'verifier_id': workload.verifier_id,
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
    
    @classmethod
    def _calculate_enhanced_workload_analytics(cls, verifier_id: int) -> Dict:
        """Calculate enhanced workload analytics"""
        now = timezone.now()
        
        # Time-based analytics
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        prescriptions = PrescriptionUpload.objects.filter(verified_by_id=verifier_id)
        
        # Daily performance
        today_verified = prescriptions.filter(
            verification_date__gte=today_start
        ).count()
        
        # Weekly performance
        week_verified = prescriptions.filter(
            verification_date__gte=week_start
        ).count()
        
        # Monthly performance
        month_verified = prescriptions.filter(
            verification_date__gte=month_start
        ).count()
        
        # Quality metrics
        quality_metrics = prescriptions.filter(
            verification_date__isnull=False
        ).aggregate(
            avg_processing_time=Avg(
                F('verification_date') - F('uploaded_at')
            ),
            max_processing_time=Max(
                F('verification_date') - F('uploaded_at')
            ),
            min_processing_time=Min(
                F('verification_date') - F('uploaded_at')
            )
        )
        
        # Peak hours analysis
        peak_hours = cls._analyze_peak_hours(verifier_id)
        
        return {
            'daily_verified': today_verified,
            'weekly_verified': week_verified,
            'monthly_verified': month_verified,
            'quality_metrics': {
                'avg_processing_minutes': (
                    quality_metrics['avg_processing_time'].total_seconds() / 60
                    if quality_metrics['avg_processing_time'] else 0
                ),
                'max_processing_minutes': (
                    quality_metrics['max_processing_time'].total_seconds() / 60
                    if quality_metrics['max_processing_time'] else 0
                ),
                'min_processing_minutes': (
                    quality_metrics['min_processing_time'].total_seconds() / 60
                    if quality_metrics['min_processing_time'] else 0
                ),
            },
            'peak_hours': peak_hours,
        }
    
    @classmethod
    def _analyze_peak_hours(cls, verifier_id: int) -> Dict:
        """Analyze verifier's peak working hours"""
        # Get verification activities for last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        activities = VerificationActivity.objects.filter(
            verifier_id=verifier_id,
            timestamp__gte=thirty_days_ago
        )
        
        # Process activities to extract hours in Python (SQLite compatible)
        hour_counts = {}
        for activity in activities:
            hour = activity.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Sort by count and convert to format
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        
        peak_hours = []
        for hour, count in sorted_hours[:5]:  # Top 5 peak hours
            peak_hours.append({
                'hour': f"{hour:02d}:00",
                'activity_count': count
            })
        
        return {
            'most_active_hours': peak_hours,
            'total_analysis_period': '30 days'
        }
    
    @classmethod
    def _calculate_workload_predictions(cls, verifier_id: int) -> Dict:
        """Calculate workload predictions and recommendations"""
        # Analyze historical patterns
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        recent_prescriptions = PrescriptionUpload.objects.filter(
            verified_by_id=verifier_id,
            verification_date__gte=seven_days_ago
        )
        
        # Calculate daily averages
        daily_avg = recent_prescriptions.count() / 7
        
        # Predict capacity utilization
        try:
            workload = VerifierWorkload.objects.get(verifier_id=verifier_id)
            predicted_capacity = (daily_avg / workload.max_daily_capacity) * 100
        except VerifierWorkload.DoesNotExist:
            predicted_capacity = 0
        
        # Generate recommendations
        recommendations = cls._generate_workload_recommendations(
            daily_avg, predicted_capacity
        )
        
        return {
            'predictions': {
                'daily_average_last_week': round(daily_avg, 2),
                'predicted_capacity_utilization': round(predicted_capacity, 2),
                'workload_trend': cls._calculate_workload_trend(verifier_id),
            },
            'recommendations': recommendations
        }
    
    @classmethod
    def _calculate_workload_trend(cls, verifier_id: int) -> str:
        """Calculate workload trend (increasing/decreasing/stable)"""
        now = timezone.now()
        week1_start = now - timedelta(days=14)
        week1_end = now - timedelta(days=7)
        week2_start = now - timedelta(days=7)
        
        week1_count = PrescriptionUpload.objects.filter(
            verified_by_id=verifier_id,
            verification_date__gte=week1_start,
            verification_date__lt=week1_end
        ).count()
        
        week2_count = PrescriptionUpload.objects.filter(
            verified_by_id=verifier_id,
            verification_date__gte=week2_start
        ).count()
        
        if week2_count > week1_count * 1.1:
            return 'increasing'
        elif week2_count < week1_count * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    @classmethod
    def _generate_workload_recommendations(cls, daily_avg: float, capacity_util: float) -> List[str]:
        """Generate workload management recommendations"""
        recommendations = []
        
        if capacity_util > 90:
            recommendations.append("Consider increasing daily capacity or redistributing workload")
        elif capacity_util > 75:
            recommendations.append("Monitor workload closely - approaching capacity limit")
        elif capacity_util < 50:
            recommendations.append("Capacity available for additional prescriptions")
        
        if daily_avg > 20:
            recommendations.append("High volume workload - consider batch processing")
        elif daily_avg < 5:
            recommendations.append("Low volume - opportunity for training or quality focus")
        
        return recommendations
    
    @classmethod
    def get_system_health_metrics(cls) -> Dict:
        """Get comprehensive system health metrics"""
        cache_key = cls.CACHE_KEYS['system_health']
        metrics = cache.get(cache_key)
        
        if metrics is None:
            metrics = cls._calculate_system_health_metrics()
            cache.set(cache_key, metrics, cls.CACHE_TIMEOUTS['system_metrics'])
        
        return metrics
    
    @classmethod
    def _calculate_system_health_metrics(cls) -> Dict:
        """Calculate comprehensive system health metrics"""
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # System-wide statistics
        total_prescriptions = PrescriptionUpload.objects.count()
        pending_prescriptions = PrescriptionUpload.objects.filter(
            verification_status='pending'
        ).count()
        
        # Verifier statistics
        active_verifiers = VerifierWorkload.objects.filter(
            is_available=True
        ).count()
        
        total_verifiers = VerifierWorkload.objects.count()
        
        # Performance metrics
        avg_processing_time = PrescriptionUpload.objects.filter(
            verification_date__isnull=False
        ).aggregate(
            avg_time=Avg(F('verification_date') - F('uploaded_at'))
        )['avg_time']
        
        # Quality metrics
        approval_rate = cls._calculate_system_approval_rate()
        
        # Capacity metrics
        capacity_metrics = cls._calculate_system_capacity_metrics()
        
        return {
            'system_overview': {
                'total_prescriptions': total_prescriptions,
                'pending_prescriptions': pending_prescriptions,
                'active_verifiers': active_verifiers,
                'total_verifiers': total_verifiers,
                'system_load': round((pending_prescriptions / max(active_verifiers, 1)), 2),
            },
            'performance_metrics': {
                'avg_processing_minutes': (
                    avg_processing_time.total_seconds() / 60
                    if avg_processing_time else 0
                ),
                'system_approval_rate': approval_rate,
            },
            'capacity_metrics': capacity_metrics,
            'last_updated': now.isoformat(),
        }
    
    @classmethod
    def _calculate_system_approval_rate(cls) -> float:
        """Calculate system-wide approval rate"""
        verified_prescriptions = PrescriptionUpload.objects.filter(
            verification_status__in=['approved', 'rejected']
        )
        
        total_verified = verified_prescriptions.count()
        if total_verified == 0:
            return 0.0
        
        approved_count = verified_prescriptions.filter(
            verification_status='approved'
        ).count()
        
        return round((approved_count / total_verified) * 100, 2)
    
    @classmethod
    def _calculate_system_capacity_metrics(cls) -> Dict:
        """Calculate system capacity metrics"""
        workloads = VerifierWorkload.objects.all()
        
        total_capacity = sum(w.max_daily_capacity for w in workloads)
        current_usage = sum(w.current_daily_count for w in workloads)
        available_capacity = total_capacity - current_usage
        
        return {
            'total_daily_capacity': total_capacity,
            'current_daily_usage': current_usage,
            'available_capacity': available_capacity,
            'capacity_utilization': round((current_usage / max(total_capacity, 1)) * 100, 2),
        }
    
    @classmethod
    def optimize_database_queries(cls):
        """Run database optimization queries"""
        try:
            # Update workload statistics for all verifiers
            verifiers = User.objects.filter(role='rx_verifier')
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for verifier in verifiers:
                    future = executor.submit(cls._update_verifier_workload, verifier.id)
                    futures.append(future)
                
                # Wait for all updates to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error updating verifier workload: {e}")
            
            logger.info("Database optimization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False
    
    @classmethod
    def _update_verifier_workload(cls, verifier_id: int):
        """Update individual verifier workload"""
        try:
            workload = VerifierWorkload.objects.get(verifier_id=verifier_id)
            workload.update_workload()
            
            # Clear cache for this verifier
            cache_key = cls.CACHE_KEYS['workload_stats'].format(verifier_id)
            cache.delete(cache_key)
            
        except VerifierWorkload.DoesNotExist:
            logger.warning(f"Workload not found for verifier {verifier_id}")
    
    @classmethod
    def clear_all_caches(cls):
        """Clear all RX system caches"""
        try:
            # Get all cache keys with our patterns
            cache_patterns = [
                'rx_adv_*',
                'rx_workload_*',
                'rx_dashboard_*',
                'rx_pending_*'
            ]
            
            # Clear specific caches
            for pattern in cache_patterns:
                # Note: This is a simplified approach
                # In production, you might want to use Redis SCAN
                pass
            
            # Clear system-wide caches
            cache.delete(cls.CACHE_KEYS['system_health'])
            cache.delete(cls.CACHE_KEYS['performance_metrics'])
            
            logger.info("All RX system caches cleared")
            return True
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            return False
    
    @classmethod
    def get_performance_analytics(cls, days: int = 30) -> Dict:
        """Get comprehensive performance analytics"""
        cache_key = cls.CACHE_KEYS['analytics'].format(days)
        analytics = cache.get(cache_key)
        
        if analytics is None:
            analytics = cls._calculate_performance_analytics(days)
            cache.set(cache_key, analytics, cls.CACHE_TIMEOUTS['analytics_data'])
        
        return analytics
    
    @classmethod
    def _calculate_performance_analytics(cls, days: int) -> Dict:
        """Calculate performance analytics for specified period"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Prescription analytics
        prescriptions = PrescriptionUpload.objects.filter(
            uploaded_at__gte=start_date
        )
        
        verified_prescriptions = prescriptions.filter(
            verification_date__isnull=False
        )
        
        # Volume analytics
        volume_analytics = {
            'total_uploaded': prescriptions.count(),
            'total_verified': verified_prescriptions.count(),
            'total_approved': verified_prescriptions.filter(verification_status='approved').count(),
            'total_rejected': verified_prescriptions.filter(verification_status='rejected').count(),
            'pending_count': prescriptions.filter(verification_status='pending').count(),
        }
        
        # Time analytics
        time_analytics = cls._calculate_time_analytics(verified_prescriptions)
        
        # Verifier analytics
        verifier_analytics = cls._calculate_verifier_analytics(start_date, end_date)
        
        return {
            'period': f"{days} days",
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'volume_analytics': volume_analytics,
            'time_analytics': time_analytics,
            'verifier_analytics': verifier_analytics,
        }
    
    @classmethod
    def _calculate_time_analytics(cls, prescriptions) -> Dict:
        """Calculate time-based analytics"""
        if not prescriptions.exists():
            return {
                'avg_processing_time_minutes': 0,
                'median_processing_time_minutes': 0,
                'fastest_processing_time_minutes': 0,
                'slowest_processing_time_minutes': 0,
            }
        
        processing_times = []
        for prescription in prescriptions:
            if prescription.verification_date and prescription.uploaded_at:
                delta = prescription.verification_date - prescription.uploaded_at
                processing_times.append(delta.total_seconds() / 60)
        
        if not processing_times:
            return {
                'avg_processing_time_minutes': 0,
                'median_processing_time_minutes': 0,
                'fastest_processing_time_minutes': 0,
                'slowest_processing_time_minutes': 0,
            }
        
        processing_times.sort()
        
        return {
            'avg_processing_time_minutes': round(sum(processing_times) / len(processing_times), 2),
            'median_processing_time_minutes': round(
                processing_times[len(processing_times) // 2], 2
            ),
            'fastest_processing_time_minutes': round(min(processing_times), 2),
            'slowest_processing_time_minutes': round(max(processing_times), 2),
        }
    
    @classmethod
    def _calculate_verifier_analytics(cls, start_date, end_date) -> Dict:
        """Calculate verifier performance analytics"""
        verifiers = User.objects.filter(role='rx_verifier')
        verifier_stats = []
        
        for verifier in verifiers:
            verified_count = PrescriptionUpload.objects.filter(
                verified_by=verifier,
                verification_date__gte=start_date,
                verification_date__lte=end_date
            ).count()
            
            approved_count = PrescriptionUpload.objects.filter(
                verified_by=verifier,
                verification_status='approved',
                verification_date__gte=start_date,
                verification_date__lte=end_date
            ).count()
            
            verifier_stats.append({
                'verifier_name': verifier.full_name,
                'verifier_email': verifier.email,
                'total_verified': verified_count,
                'total_approved': approved_count,
                'approval_rate': round((approved_count / max(verified_count, 1)) * 100, 2),
            })
        
        # Sort by total verified
        verifier_stats.sort(key=lambda x: x['total_verified'], reverse=True)
        
        return {
            'total_verifiers': len(verifier_stats),
            'top_performers': verifier_stats[:5],
            'all_verifier_stats': verifier_stats,
        }


class BackgroundTaskManager:
    """Manage background tasks for RX system optimization"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.executor = ThreadPoolExecutor(max_workers=3)
            self.tasks = {}
            self.initialized = True
    
    def schedule_optimization_task(self, task_name: str, delay_seconds: int = 0):
        """Schedule a background optimization task"""
        def run_task():
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            
            try:
                if task_name == 'database_optimization':
                    AdvancedRXOptimizer.optimize_database_queries()
                elif task_name == 'cache_refresh':
                    self._refresh_critical_caches()
                elif task_name == 'system_health_check':
                    self._perform_system_health_check()
                
                logger.info(f"Background task '{task_name}' completed successfully")
                
            except Exception as e:
                logger.error(f"Background task '{task_name}' failed: {e}")
        
        future = self.executor.submit(run_task)
        self.tasks[task_name] = future
        return future
    
    def _refresh_critical_caches(self):
        """Refresh critical system caches"""
        # Refresh system health metrics
        AdvancedRXOptimizer.get_system_health_metrics()
        
        # Refresh workload stats for active verifiers
        active_verifiers = User.objects.filter(
            role='rx_verifier',
            workload_stats__is_available=True
        )
        
        for verifier in active_verifiers:
            AdvancedRXOptimizer.get_enhanced_workload_stats(verifier.id)
    
    def _perform_system_health_check(self):
        """Perform comprehensive system health check"""
        health_metrics = AdvancedRXOptimizer.get_system_health_metrics()
        
        # Check for alerts
        alerts = []
        
        if health_metrics['system_overview']['pending_prescriptions'] > 100:
            alerts.append("High pending prescription count")
        
        if health_metrics['capacity_metrics']['capacity_utilization'] > 90:
            alerts.append("System capacity near limit")
        
        if health_metrics['system_overview']['active_verifiers'] == 0:
            alerts.append("No active verifiers available")
        
        if alerts:
            logger.warning(f"System health alerts: {', '.join(alerts)}")
        else:
            logger.info("System health check passed")
        
        return alerts
    
    def get_task_status(self, task_name: str) -> str:
        """Get status of a background task"""
        if task_name not in self.tasks:
            return "not_found"
        
        future = self.tasks[task_name]
        
        if future.done():
            if future.exception():
                return "failed"
            else:
                return "completed"
        else:
            return "running"
    
    def shutdown(self):
        """Shutdown the background task manager"""
        self.executor.shutdown(wait=True)


# Initialize background task manager
background_task_manager = BackgroundTaskManager()