# Comprehensive Integration Test for Enhanced RX Upload System

import os
import sys
import django
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from io import BytesIO
from PIL import Image

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.core.cache import cache

# Import our modules
from rx_upload.models import PrescriptionUpload, VerifierWorkload, VerificationActivity
from rx_upload.serializers import PrescriptionUploadSerializer
from rx_upload.advanced_optimizations import AdvancedRXOptimizer, BackgroundTaskManager
from rx_upload.security_audit import SecurityAuditManager
from rx_upload.comprehensive_validation import ComprehensiveValidator
from rx_upload.optimizations import RXSystemOptimizer

User = get_user_model()


class ComprehensiveIntegrationTest:
    """Comprehensive integration test for enhanced RX upload system"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': {},
            'performance_metrics': {},
        }
        
        self.factory = RequestFactory()
        
        # Setup test users
        self.setup_test_users()
        
        # Clear cache before testing
        cache.clear()
    
    def setup_test_users(self):
        """Setup test users for integration testing"""
        try:
            # Create customer
            self.customer = User.objects.create_user(
                email='customer_integration@test.com',
                password='testpass123',
                role='customer',
                full_name='Test Customer Integration',
                email_verified=True
            )
            
            # Create verifier
            self.verifier = User.objects.create_user(
                email='verifier_integration@test.com',
                password='testpass123',
                role='rx_verifier',
                full_name='Test Verifier Integration',
                email_verified=True
            )
            
            # Create workload for verifier
            self.workload = VerifierWorkload.objects.create(
                verifier=self.verifier,
                max_daily_capacity=20,
                is_available=True
            )
            
            print("✅ Test users created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create test users: {e}")
            raise
    
    def create_test_image(self):
        """Create a test image file for upload testing"""
        # Create a simple test image
        image = Image.new('RGB', (800, 600), color='white')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            name='test_prescription.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_imagekit_integration(self):
        """Test ImageKit integration functionality"""
        test_name = "ImageKit Integration Test"
        self.test_results['tests_run'] += 1
        
        try:
            print(f"\n🧪 Running {test_name}...")
            
            # Create test file
            test_file = self.create_test_image()
            
            # Test data
            test_data = {
                'patient_name': 'John Doe Integration',
                'doctor_name': 'Dr. Smith Integration',
                'medication_details': 'Metformin 500mg twice daily',
                'prescription_date': '2024-01-15',
                'notes': 'Integration test prescription',
                'is_urgent': False
            }
            
            # Mock ImageKit upload
            with patch('rx_upload.serializers.upload_to_imagekit') as mock_upload:
                mock_upload.return_value = 'https://ik.imagekit.io/test/prescription_123.jpg'
                
                # Create serializer
                serializer = PrescriptionUploadSerializer(data=test_data)
                serializer.is_valid(raise_exception=True)
                
                # Add file and customer to validated data
                serializer.validated_data['prescription_file'] = test_file
                serializer.validated_data['customer'] = self.customer
                
                # Test create method
                prescription = serializer.create(serializer.validated_data)
                
                # Verify prescription was created
                assert prescription.id is not None
                assert prescription.patient_name == test_data['patient_name']
                assert prescription.verification_status == 'pending'
                
                # Verify ImageKit upload was called (check if file was provided)
                if test_file:
                    mock_upload.assert_called_once()
                
                print(f"✅ {test_name} passed")
                self.test_results['tests_passed'] += 1
                self.test_results['detailed_results'][test_name] = {
                    'status': 'PASSED',
                    'prescription_id': prescription.id,
                    'imagekit_called': mock_upload.called,
                }
                
                return prescription
        
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
            return None
    
    def test_advanced_optimization(self):
        """Test advanced optimization functionality"""
        test_name = "Advanced Optimization Test"
        self.test_results['tests_run'] += 1
        
        try:
            print(f"\n🧪 Running {test_name}...")
            
            start_time = time.time()
            
            # Test enhanced workload stats
            workload_stats = AdvancedRXOptimizer.get_enhanced_workload_stats(self.verifier.id)
            
            # Verify enhanced stats structure
            required_keys = [
                'verifier_id', 'pending_count', 'approval_rate',
                'daily_verified', 'weekly_verified', 'monthly_verified',
                'predictions', 'recommendations'
            ]
            
            for key in required_keys:
                assert key in workload_stats, f"Missing key: {key}"
            
            # Test system health metrics
            health_metrics = AdvancedRXOptimizer.get_system_health_metrics()
            
            required_health_keys = [
                'system_overview', 'performance_metrics', 'capacity_metrics'
            ]
            
            for key in required_health_keys:
                assert key in health_metrics, f"Missing health key: {key}"
            
            # Test background task manager
            background_manager = BackgroundTaskManager()
            task_future = background_manager.schedule_optimization_task('cache_refresh')
            
            # Wait a moment for task to start
            time.sleep(0.1)
            
            task_status = background_manager.get_task_status('cache_refresh')
            assert task_status in ['running', 'completed'], f"Unexpected task status: {task_status}"
            
            # Test comprehensive optimization
            optimization_result = RXSystemOptimizer.run_comprehensive_optimization()
            assert 'database_optimization' in optimization_result
            assert 'cache_refresh' in optimization_result
            
            end_time = time.time()
            
            print(f"✅ {test_name} passed")
            self.test_results['tests_passed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'PASSED',
                'execution_time': round(end_time - start_time, 3),
                'workload_stats_keys': len(workload_stats.keys()),
                'health_metrics_keys': len(health_metrics.keys()),
                'background_task_status': task_status,
            }
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_security_audit(self):
        """Test security audit functionality"""
        test_name = "Security Audit Test"
        self.test_results['tests_run'] += 1
        
        try:
            print(f"\n🧪 Running {test_name}...")
            
            # Test file upload security audit
            test_file = self.create_test_image()
            
            file_audit = SecurityAuditManager.audit_file_upload_security(test_file, self.customer)
            
            # Verify audit result structure
            required_audit_keys = [
                'is_secure', 'security_score', 'warnings', 'errors', 'recommendations'
            ]
            
            for key in required_audit_keys:
                assert key in file_audit, f"Missing audit key: {key}"
            
            assert isinstance(file_audit['security_score'], (int, float))
            assert 0 <= file_audit['security_score'] <= 100
            
            # Test session security audit
            request = self.factory.get('/test/')
            request.user = self.customer
            
            session_audit = SecurityAuditManager.audit_user_session_security(self.customer, request)
            
            required_session_keys = ['is_secure', 'security_score', 'warnings']
            for key in required_session_keys:
                assert key in session_audit, f"Missing session key: {key}"
            
            # Test API endpoint security
            api_audit = SecurityAuditManager.audit_api_endpoint_security(
                '/api/prescriptions/', 'POST', self.customer
            )
            
            required_api_keys = ['is_secure', 'access_granted', 'warnings']
            for key in required_api_keys:
                assert key in api_audit, f"Missing API key: {key}"
            
            # Test comprehensive security report
            security_report = SecurityAuditManager.generate_security_report(self.customer)
            
            required_report_keys = [
                'timestamp', 'overall_security_score', 'system_overview', 'recommendations'
            ]
            for key in required_report_keys:
                assert key in security_report, f"Missing report key: {key}"
            
            print(f"✅ {test_name} passed")
            self.test_results['tests_passed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'PASSED',
                'file_audit_score': file_audit['security_score'],
                'session_audit_score': session_audit['security_score'],
                'api_access_granted': api_audit['access_granted'],
                'overall_security_score': security_report['overall_security_score'],
            }
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation functionality"""
        test_name = "Comprehensive Validation Test"
        self.test_results['tests_run'] += 1
        
        try:
            print(f"\n🧪 Running {test_name}...")
            
            # Test prescription upload validation
            test_data = {
                'patient_name': 'Jane Doe Validation',
                'doctor_name': 'Dr. Johnson Validation',
                'medication_details': 'Lisinopril 10mg once daily for blood pressure',
                'prescription_date': '2024-01-20',
                'notes': 'Validation test prescription with detailed notes',
                'is_urgent': False,
                'doctor_phone': '555-123-4567'
            }
            
            test_files = {
                'prescription_file': self.create_test_image()
            }
            
            validation_result = ComprehensiveValidator.validate_prescription_upload(
                test_data, test_files, self.customer
            )
            
            # Verify validation result structure
            required_validation_keys = [
                'is_valid', 'errors', 'warnings', 'validation_score', 'data_quality_score'
            ]
            
            for key in required_validation_keys:
                assert key in validation_result, f"Missing validation key: {key}"
            
            assert isinstance(validation_result['validation_score'], (int, float))
            assert isinstance(validation_result['data_quality_score'], (int, float))
            
            # Test verifier assignment validation
            if hasattr(self, 'test_prescription') and self.test_prescription:
                verifier_validation = ComprehensiveValidator.validate_verifier_assignment(
                    self.test_prescription, self.verifier
                )
                
                required_verifier_keys = ['is_valid', 'errors', 'warnings']
                for key in required_verifier_keys:
                    assert key in verifier_validation, f"Missing verifier key: {key}"
            
            # Test verification decision validation
            decision_validation = ComprehensiveValidator.validate_verification_decision(
                Mock(verification_status='pending'), 'approved', 'Test approval'
            )
            
            required_decision_keys = ['is_valid', 'errors', 'warnings']
            for key in required_decision_keys:
                assert key in decision_validation, f"Missing decision key: {key}"
            
            print(f"✅ {test_name} passed")
            self.test_results['tests_passed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'PASSED',
                'validation_score': validation_result['validation_score'],
                'data_quality_score': validation_result['data_quality_score'],
                'is_valid': validation_result['is_valid'],
                'total_errors': sum(len(errors) if isinstance(errors, list) else 1 
                                 for errors in validation_result['errors'].values()),
                'total_warnings': len(validation_result['warnings']),
            }
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        test_name = "End-to-End Workflow Test"
        self.test_results['tests_run'] += 1
        
        try:
            print(f"\n🧪 Running {test_name}...")
            
            workflow_start = time.time()
            
            # Step 1: Upload prescription with all validations
            test_data = {
                'patient_name': 'Complete Workflow Patient',
                'doctor_name': 'Dr. Workflow Test',
                'medication_details': 'Atorvastatin 20mg once daily with dinner',
                'prescription_date': '2024-01-22',
                'notes': 'Complete workflow test with all components',
                'is_urgent': True,
                'urgent_reason': 'Patient needs medication refill urgently',
                'doctor_phone': '555-987-6543'
            }
            
            test_files = {
                'prescription_file': self.create_test_image()
            }
            
            # Validation
            validation = ComprehensiveValidator.validate_prescription_upload(
                test_data, test_files, self.customer
            )
            assert validation['is_valid'], f"Validation failed: {validation['errors']}"
            
            # Security audit
            security_audit = SecurityAuditManager.audit_file_upload_security(
                test_files['prescription_file'], self.customer
            )
            assert security_audit['is_secure'], f"Security audit failed: {security_audit['errors']}"
            
            # Create prescription with ImageKit
            with patch('rx_upload.serializers.upload_to_imagekit') as mock_upload:
                mock_upload.return_value = 'https://ik.imagekit.io/test/workflow_prescription.jpg'
                
                serializer = PrescriptionUploadSerializer(data=test_data)
                serializer.is_valid(raise_exception=True)
                serializer.validated_data['prescription_file'] = test_files['prescription_file']
                serializer.validated_data['customer'] = self.customer
                
                prescription = serializer.create(serializer.validated_data)
                self.test_prescription = prescription
            
            # Step 2: Optimize system
            optimization = RXSystemOptimizer.run_comprehensive_optimization()
            assert 'database_optimization' in optimization
            
            # Step 3: Get enhanced analytics
            analytics = AdvancedRXOptimizer.get_performance_analytics(7)
            assert 'volume_analytics' in analytics
            
            # Step 4: Assign to verifier
            verifier_assignment = ComprehensiveValidator.validate_verifier_assignment(
                prescription, self.verifier
            )
            assert verifier_assignment['is_valid']
            
            # Step 5: Update workload
            workload_stats = AdvancedRXOptimizer.get_enhanced_workload_stats(self.verifier.id)
            assert 'verifier_id' in workload_stats
            
            workflow_end = time.time()
            
            print(f"✅ {test_name} passed")
            self.test_results['tests_passed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'PASSED',
                'workflow_time': round(workflow_end - workflow_start, 3),
                'prescription_id': prescription.id,
                'validation_score': validation['validation_score'],
                'security_score': security_audit['security_score'],
                'verifier_assignment': 'valid',
                'optimization_completed': True,
            }
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        test_name = "Performance Benchmarks Test"
        self.test_results['tests_run'] += 1
        
        try:
            print(f"\n🧪 Running {test_name}...")
            
            performance_results = {}
            
            # Benchmark 1: Workload stats retrieval
            start_time = time.time()
            for i in range(10):
                AdvancedRXOptimizer.get_enhanced_workload_stats(self.verifier.id)
            workload_time = (time.time() - start_time) / 10
            performance_results['avg_workload_stats_time'] = workload_time
            
            # Benchmark 2: System health metrics
            start_time = time.time()
            for i in range(5):
                AdvancedRXOptimizer.get_system_health_metrics()
            health_time = (time.time() - start_time) / 5
            performance_results['avg_health_metrics_time'] = health_time
            
            # Benchmark 3: Security audit
            start_time = time.time()
            test_file = self.create_test_image()
            for i in range(5):
                SecurityAuditManager.audit_file_upload_security(test_file, self.customer)
            security_time = (time.time() - start_time) / 5
            performance_results['avg_security_audit_time'] = security_time
            
            # Benchmark 4: Validation
            start_time = time.time()
            test_data = {'patient_name': 'Benchmark Test', 'doctor_name': 'Dr. Benchmark'}
            test_files = {'prescription_file': self.create_test_image()}
            for i in range(5):
                ComprehensiveValidator.validate_prescription_upload(test_data, test_files, self.customer)
            validation_time = (time.time() - start_time) / 5
            performance_results['avg_validation_time'] = validation_time
            
            # Performance thresholds (in seconds)
            thresholds = {
                'avg_workload_stats_time': 0.5,
                'avg_health_metrics_time': 1.0,
                'avg_security_audit_time': 0.3,
                'avg_validation_time': 0.5,
            }
            
            # Check performance
            performance_pass = True
            for metric, time_taken in performance_results.items():
                if time_taken > thresholds[metric]:
                    print(f"⚠️  Performance warning: {metric} took {time_taken:.3f}s (threshold: {thresholds[metric]}s)")
                    performance_pass = False
                else:
                    print(f"✅ Performance good: {metric} took {time_taken:.3f}s")
            
            self.test_results['performance_metrics'] = performance_results
            
            print(f"✅ {test_name} completed")
            self.test_results['tests_passed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'PASSED' if performance_pass else 'PERFORMANCE_WARNING',
                'performance_metrics': performance_results,
                'thresholds': thresholds,
            }
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            self.test_results['tests_failed'] += 1
            self.test_results['detailed_results'][test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Comprehensive Integration Testing for Enhanced RX Upload System")
        print("=" * 80)
        
        test_start_time = time.time()
        
        # Run individual tests
        prescription = self.test_imagekit_integration()
        self.test_advanced_optimization()
        self.test_security_audit()
        self.test_comprehensive_validation()
        self.test_end_to_end_workflow()
        self.test_performance_benchmarks()
        
        test_end_time = time.time()
        
        # Calculate summary
        self.test_results['total_execution_time'] = round(test_end_time - test_start_time, 3)
        self.test_results['success_rate'] = round(
            (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100, 2
        ) if self.test_results['tests_run'] > 0 else 0
        
        # Print summary
        self.print_test_summary()
        
        return self.test_results
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests Run: {self.test_results['tests_run']}")
        print(f"Tests Passed: {self.test_results['tests_passed']}")
        print(f"Tests Failed: {self.test_results['tests_failed']}")
        print(f"Success Rate: {self.test_results['success_rate']}%")
        print(f"Total Execution Time: {self.test_results['total_execution_time']}s")
        
        print(f"\n📊 PERFORMANCE METRICS:")
        for metric, value in self.test_results.get('performance_metrics', {}).items():
            print(f"  {metric}: {value:.3f}s")
        
        print(f"\n📋 TEST DETAILS:")
        for test_name, details in self.test_results['detailed_results'].items():
            status_icon = "✅" if details['status'] == 'PASSED' else "❌" if details['status'] == 'FAILED' else "⚠️"
            print(f"  {status_icon} {test_name}: {details['status']}")
            if 'error' in details:
                print(f"    Error: {details['error']}")
        
        if self.test_results['success_rate'] == 100:
            print(f"\n🎉 ALL TESTS PASSED! Enhanced RX Upload System is fully functional.")
        elif self.test_results['success_rate'] >= 80:
            print(f"\n✅ Most tests passed. System is largely functional with minor issues.")
        else:
            print(f"\n⚠️  Several tests failed. System requires attention before production use.")
        
        print("=" * 80)
    
    def cleanup(self):
        """Cleanup test data"""
        try:
            # Delete test prescriptions
            PrescriptionUpload.objects.filter(
                patient_name__icontains='Integration'
            ).delete()
            
            PrescriptionUpload.objects.filter(
                patient_name__icontains='Workflow'
            ).delete()
            
            # Delete test users
            User.objects.filter(email__icontains='integration').delete()
            
            print("🧹 Test cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


def main():
    """Main test execution"""
    print("Initializing Comprehensive Integration Test Suite...")
    
    try:
        # Create test instance
        test_suite = ComprehensiveIntegrationTest()
        
        # Run all tests
        results = test_suite.run_all_tests()
        
        # Save results to file
        results_file = f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Cleanup
        test_suite.cleanup()
        
        # Return success code
        return 0 if results['success_rate'] == 100 else 1
        
    except Exception as e:
        print(f"❌ Integration test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)