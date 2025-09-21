"""
Management command for RX system optimization and maintenance
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from rx_upload.optimizations import RXSystemOptimizer, RXDatabaseOptimizer
from rx_upload.models import VerifierWorkload
from accounts.models import User


class Command(BaseCommand):
    help = 'Optimize and maintain RX upload system performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all RX system cache',
        )
        parser.add_argument(
            '--update-workloads',
            action='store_true',
            help='Update all verifier workloads',
        )
        parser.add_argument(
            '--cleanup-activities',
            type=int,
            default=90,
            help='Cleanup activities older than specified days (default: 90)',
        )
        parser.add_argument(
            '--system-health',
            action='store_true',
            help='Check and display system health status',
        )
        parser.add_argument(
            '--analytics',
            type=int,
            default=30,
            help='Show prescription analytics for specified days (default: 30)',
        )
        parser.add_argument(
            '--top-verifiers',
            type=int,
            default=5,
            help='Show top performing verifiers (default: 5)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimization tasks',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 RX System Optimization Tool'))
        self.stdout.write('=' * 50)

        if options['all'] or options['clear_cache']:
            self.clear_cache()

        if options['all'] or options['update_workloads']:
            self.update_workloads()

        if options['all'] or options['cleanup_activities']:
            self.cleanup_activities(options['cleanup_activities'])

        if options['system_health']:
            self.show_system_health()

        if options['analytics']:
            self.show_analytics(options['analytics'])

        if options['top_verifiers']:
            self.show_top_verifiers(options['top_verifiers'])

        if not any([options['clear_cache'], options['update_workloads'], 
                   options['cleanup_activities'], options['system_health'],
                   options['analytics'], options['top_verifiers'], options['all']]):
            self.stdout.write(
                self.style.WARNING('No optimization task specified. Use --help for options.')
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Optimization completed!'))

    def clear_cache(self):
        """Clear all RX system cache"""
        self.stdout.write('\n🗑️  Clearing RX system cache...')
        try:
            RXSystemOptimizer.invalidate_all_cache()
            self.stdout.write(self.style.SUCCESS('   ✅ Cache cleared successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Cache clear failed: {str(e)}'))

    def update_workloads(self):
        """Update all verifier workloads"""
        self.stdout.write('\n📊 Updating verifier workloads...')
        try:
            RXDatabaseOptimizer.bulk_update_workloads()
            verifier_count = User.objects.filter(role='rx_verifier').count()
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ Updated workloads for {verifier_count} verifiers')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Workload update failed: {str(e)}'))

    def cleanup_activities(self, days):
        """Cleanup old verification activities"""
        self.stdout.write(f'\n🧹 Cleaning up activities older than {days} days...')
        try:
            deleted_count = RXDatabaseOptimizer.cleanup_old_activities(days)
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ Cleaned up {deleted_count} old activities')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Cleanup failed: {str(e)}'))

    def show_system_health(self):
        """Show system health status"""
        self.stdout.write('\n🏥 System Health Status:')
        try:
            health = RXSystemOptimizer.get_system_health_status()
            
            # Health score with color coding
            score = health['health_score']
            status_text = health['health_status']
            
            if score >= 95:
                color = self.style.SUCCESS
            elif score >= 80:
                color = self.style.WARNING
            else:
                color = self.style.ERROR
            
            self.stdout.write(f'   Health Score: {color(f"{score}/100 ({status_text})")}')
            self.stdout.write(f'   Pending Prescriptions: {health["pending_count"]}')
            self.stdout.write(f'   Overdue Prescriptions: {health["overdue_count"]}')
            self.stdout.write(f'   Available Verifiers: {health["available_verifiers"]}')
            
            self.stdout.write('\n   📋 Recommendations:')
            for rec in health['recommendations']:
                self.stdout.write(f'      • {rec}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Health check failed: {str(e)}'))

    def show_analytics(self, days):
        """Show prescription analytics"""
        self.stdout.write(f'\n📈 Prescription Analytics (Last {days} days):')
        try:
            analytics = RXSystemOptimizer.get_prescription_analytics(days)
            
            self.stdout.write(f'   Total Prescriptions: {analytics["total_prescriptions"]}')
            self.stdout.write(f'   Total Verified: {analytics["total_verified"]}')
            self.stdout.write(f'   Total Approved: {analytics["total_approved"]}')
            self.stdout.write(f'   Total Rejected: {analytics["total_rejected"]}')
            self.stdout.write(f'   Approval Rate: {analytics["approval_rate"]}%')
            self.stdout.write(f'   Urgent Prescriptions: {analytics["urgent_prescriptions"]}')
            
            if analytics["avg_processing_time"]:
                self.stdout.write(f'   Avg Processing Time: {analytics["avg_processing_time"]:.2f} hours')
            
            self.stdout.write(f'\n   👨‍⚕️ Verifier Metrics:')
            self.stdout.write(f'   Total Verifiers: {analytics["total_verifiers"]}')
            self.stdout.write(f'   Active Verifiers: {analytics["active_verifiers"]}')
            
            if analytics["avg_approval_rate"]:
                self.stdout.write(f'   Avg Approval Rate: {analytics["avg_approval_rate"]:.2f}%')
            if analytics["avg_processing_time"]:
                self.stdout.write(f'   Avg Processing Time: {analytics["avg_processing_time"]:.2f} hours')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Analytics failed: {str(e)}'))

    def show_top_verifiers(self, limit):
        """Show top performing verifiers"""
        self.stdout.write(f'\n🏆 Top {limit} Performing Verifiers:')
        try:
            top_verifiers = RXSystemOptimizer.get_top_performing_verifiers(limit)
            
            if not top_verifiers:
                self.stdout.write('   No verifiers with sufficient data found')
                return
            
            for i, workload in enumerate(top_verifiers, 1):
                verifier = workload.verifier
                self.stdout.write(
                    f'   {i}. {verifier.full_name} '
                    f'({verifier.email}) - '
                    f'{workload.approval_rate:.1f}% approval, '
                    f'{workload.average_processing_time:.2f}h avg time, '
                    f'{workload.total_verified} total verified'
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Top verifiers query failed: {str(e)}'))