#!/usr/bin/env python3
"""
Fixed Product Seeder - Re-upload all images correctly
Fixes broken images by re-uploading them properly to ImageKit
"""

import os
import django
import sys
import random
from decimal import Decimal

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import (
    Brand, ProductCategory, Product, ProductVariant, 
    ProductReview, SupplierProductPrice
)
from products.utils.imagekit import upload_image
from django.utils.text import slugify

User = get_user_model()


class FixedImageReSeeder:
    def __init__(self):
        self.admin_user = None
        self.uploaded_images = {}
        self.fixed_count = 0
        self.failed_count = 0
        
    def setup_admin_user(self):
        """Get admin user"""
        try:
            self.admin_user = User.objects.get(email='admin@example.com')
            print("✅ Admin user found")
            return True
        except User.DoesNotExist:
            print("❌ Admin user not found")
            return False
    
    def upload_all_images_fixed(self):
        """Re-upload all images with the fixed function"""
        print("\n📷 Re-uploading all images with fixed function...")
        
        images_dir = "media/images"
        if not os.path.exists(images_dir):
            print(f"❌ Images directory not found: {images_dir}")
            return False
        
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif')):
                image_path = os.path.join(images_dir, filename)
                
                try:
                    print(f"\n📤 Uploading {filename}...")
                    
                    with open(image_path, 'rb') as image_file:
                        # Generate clean filename
                        clean_filename = slugify(filename.rsplit('.', 1)[0]) + '.' + filename.rsplit('.', 1)[1]
                        
                        # Upload with fixed function
                        uploaded_url = upload_image(image_file.read(), f"fixed_{clean_filename}")
                        
                        if uploaded_url and 'imagekit.io' in uploaded_url:
                            self.uploaded_images[filename] = uploaded_url
                            self.fixed_count += 1
                            print(f"✅ {filename} -> SUCCESS")
                        else:
                            self.failed_count += 1
                            print(f"❌ {filename} -> FAILED")
                            
                except Exception as e:
                    self.failed_count += 1
                    print(f"❌ Error uploading {filename}: {e}")
        
        print(f"\n📊 Re-upload Summary: {self.fixed_count} successful, {self.failed_count} failed")
        return self.fixed_count > 0
    
    def update_brands_with_fixed_images(self):
        """Update brands with properly uploaded images"""
        print("\n🏭 Updating brands with fixed images...")
        
        # Update MedixMall brand with proper logo
        medixmall_image = self.uploaded_images.get('medixmall.jpg', '')
        
        if medixmall_image:
            try:
                medixmall_brand = Brand.objects.get(name='MedixMall')
                medixmall_brand.image = medixmall_image
                medixmall_brand.save()
                print(f"✅ Updated MedixMall brand image: {medixmall_image}")
            except Brand.DoesNotExist:
                print("⚠️ MedixMall brand not found")
    
    def update_categories_with_fixed_images(self):
        """Update categories with properly uploaded images"""
        print("\n🏷️ Updating categories with fixed images...")
        
        category_image_mapping = {
            'Medicine': 'medicine.png',
            'Medical Equipment': 'doctor-equipment.png',
            'Pathology Supplies': 'pathology-supplies.png',
            'Health Supplements': 'health-supplements.png',
            'Surgical Supplies': 'surgical-supplies.png'
        }
        
        for category_name, image_filename in category_image_mapping.items():
            if image_filename in self.uploaded_images:
                try:
                    category = ProductCategory.objects.get(name=category_name)
                    category.icon = self.uploaded_images[image_filename]
                    category.save()
                    print(f"✅ Updated {category_name} icon: {self.uploaded_images[image_filename]}")
                except ProductCategory.DoesNotExist:
                    print(f"⚠️ Category {category_name} not found")
    
    def update_products_with_fixed_images(self):
        """Update products with properly uploaded images"""
        print("\n💊 Updating products with fixed images...")
        
        # Define product-image associations
        product_image_associations = {
            'medicine': [
                'medicine.png', 'glucose.webp', 'health-supplements.png',
                'N75.jpg', 'N95 Respirator Masks.jpg', 'Hospital-Grade Hand Sanitizer.jpg'
            ],
            'equipment': [
                'BpMonitor.webp', 'oxymeter.webp', 'thermameter.jpg', 'ecg-watch.avif',
                'nebulizer.jpg', 'Digital Body Fat Scale.jpg', 'Professional Stethoscope.jpg'
            ],
            'pathology': [
                'pathology-supplies.png', 'Home Saliva Drug Test Kit.jpg',
                'firstaid.jpg', 'surgical-supplies.png'
            ]
        }
        
        products = Product.objects.all()
        updated_count = 0
        
        for product in products:
            # Get appropriate images for this product type
            available_images = product_image_associations.get(product.product_type, [])
            
            # Find an uploaded image for this product
            product_image = None
            for img_filename in available_images:
                if img_filename in self.uploaded_images:
                    product_image = self.uploaded_images[img_filename]
                    break
            
            # If no specific image found, use any available image
            if not product_image and self.uploaded_images:
                product_image = next(iter(self.uploaded_images.values()))
            
            if product_image:
                try:
                    product.image = product_image
                    product.save()
                    updated_count += 1
                    print(f"✅ Updated {product.name}: {product_image}")
                except Exception as e:
                    print(f"❌ Error updating {product.name}: {e}")
        
        print(f"📊 Updated {updated_count} products with fixed images")
    
    def verify_fixed_images(self):
        """Verify that all fixed images are accessible"""
        print("\n🔍 Verifying fixed images accessibility...")
        
        import requests
        accessible_count = 0
        inaccessible_count = 0
        
        for filename, url in self.uploaded_images.items():
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    accessible_count += 1
                    print(f"✅ {filename}: Accessible")
                else:
                    inaccessible_count += 1
                    print(f"❌ {filename}: Status {response.status_code}")
            except Exception as e:
                inaccessible_count += 1
                print(f"❌ {filename}: Error - {e}")
        
        print(f"\n📊 Verification: {accessible_count} accessible, {inaccessible_count} inaccessible")
        return accessible_count, inaccessible_count
    
    def create_sample_products_with_fixed_images(self):
        """Create a few sample products with the fixed images to test"""
        print("\n🧪 Creating sample products with fixed images...")
        
        if not self.admin_user:
            print("❌ No admin user available")
            return
        
        # Get or create a test category
        try:
            test_category, created = ProductCategory.objects.get_or_create(
                name="Fixed Images Test",
                defaults={
                    'icon': self.uploaded_images.get('medicine.png', ''),
                    'created_by': self.admin_user,
                    'is_publish': True,
                    'status': 'published'
                }
            )
            
            if created:
                print("✅ Created test category")
        except Exception as e:
            print(f"❌ Error creating test category: {e}")
            return
        
        # Create sample products with different images
        sample_products = [
            {
                'name': 'Fixed Image Test Medicine',
                'product_type': 'medicine',
                'image_key': 'glucose.webp',
                'price': '99.99'
            },
            {
                'name': 'Fixed Image Test Equipment',
                'product_type': 'equipment', 
                'image_key': 'BpMonitor.webp',
                'price': '1999.99'
            },
            {
                'name': 'Fixed Image Test Pathology',
                'product_type': 'pathology',
                'image_key': 'pathology-supplies.png',
                'price': '299.99'
            }
        ]
        
        created_products = []
        
        for product_data in sample_products:
            image_url = self.uploaded_images.get(product_data['image_key'], '')
            
            if image_url:
                try:
                    product = Product.objects.create(
                        name=product_data['name'],
                        category=test_category,
                        description=f"Test product with fixed {product_data['image_key']} image",
                        image=image_url,
                        product_type=product_data['product_type'],
                        price=Decimal(product_data['price']),
                        stock=100,
                        created_by=self.admin_user,
                        is_publish=True,
                        status='published'
                    )
                    
                    created_products.append(product)
                    print(f"✅ Created test product: {product.name}")
                    print(f"   Image: {image_url}")
                    
                except Exception as e:
                    print(f"❌ Error creating test product {product_data['name']}: {e}")
        
        return created_products
    
    def run_fix_process(self):
        """Run the complete image fix process"""
        print("🚀 STARTING IMAGEKIT IMAGE FIX PROCESS")
        print("=" * 60)
        
        # Setup
        if not self.setup_admin_user():
            print("❌ Cannot proceed without admin user")
            return
        
        # Re-upload all images with fixed function
        if not self.upload_all_images_fixed():
            print("❌ Failed to upload images")
            return
        
        # Update existing data with fixed images
        self.update_brands_with_fixed_images()
        self.update_categories_with_fixed_images()
        self.update_products_with_fixed_images()
        
        # Verify all images are accessible
        accessible, inaccessible = self.verify_fixed_images()
        
        # Create test products to verify functionality
        test_products = self.create_sample_products_with_fixed_images()
        
        print("\n" + "=" * 60)
        print("✅ IMAGE FIX PROCESS COMPLETED!")
        print("=" * 60)
        
        print(f"📊 Final Summary:")
        print(f"   📷 Images re-uploaded: {self.fixed_count}")
        print(f"   ✅ Accessible images: {accessible}")
        print(f"   ❌ Failed uploads: {self.failed_count}")
        print(f"   🧪 Test products created: {len(test_products) if test_products else 0}")
        
        if accessible > 0:
            print(f"\n🎉 SUCCESS! {accessible} images are now properly uploaded and accessible!")
            print(f"🌐 Sample working URLs:")
            for filename, url in list(self.uploaded_images.items())[:3]:
                print(f"   {filename}: {url}")
        
        return accessible > 0


def main():
    fixer = FixedImageReSeeder()
    success = fixer.run_fix_process()
    
    if success:
        print(f"\n✅ All images have been fixed and are now working correctly!")
    else:
        print(f"\n❌ Image fix process failed. Please check the logs above.")


if __name__ == "__main__":
    main()