#!/usr/bin/env python3
"""
Fix Existing Product Images by Re-uploading to ImageKit
Updates all existing products with properly uploaded images
"""

import os
import django
import sys

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, ProductCategory, Brand
from products.utils.imagekit import upload_image
from django.db import transaction


class ProductImageFixer:
    def __init__(self):
        self.fixed_count = 0
        self.error_count = 0
        self.image_mapping = {}
        
        # Map images to product types for better matching
        self.product_image_mapping = {
            # Medicine products
            'medicine': [
                'medicine.png',
                'glucose.webp', 
                'health-supplements.png',
                'N95 Respirator Masks.jpg',
                'Hospital-Grade Hand Sanitizer.jpg',
                'Medicine Pill Organizer with Alarm.jpg'
            ],
            
            # Equipment products  
            'equipment': [
                'BpMonitor.webp',
                'doctor-equipment.png',
                'oxymeter.webp',
                'thermameter.jpg',
                'nebulizer.jpg',
                'Digital Body Fat Scale.jpg',
                'Professional Stethoscope.jpg',
                'ecg-watch.avif',
                'smart glass.jpg',
                'Smart Hearing Aid.jpg'
            ],
            
            # Pathology products
            'pathology': [
                'pathology-supplies.png',
                'firstaid.jpg',
                'surgical-supplies.png',
                'Home Saliva Drug Test Kit.jpg'
            ]
        }
    
    def upload_image_from_media(self, filename):
        """Upload a specific image from media folder"""
        image_path = f"media/images/{filename}"
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {filename}")
            return None
            
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                
                # Create a clean filename
                clean_name = filename.replace(' ', '_').lower()
                uploaded_url = upload_image(image_data, f"fixed_{clean_name}")
                
                if 'imagekit.io' in uploaded_url:
                    print(f"✅ Uploaded {filename} -> {uploaded_url}")
                    return uploaded_url
                else:
                    print(f"❌ Upload failed for {filename}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error uploading {filename}: {e}")
            return None
    
    def fix_product_images(self):
        """Fix all product images by re-uploading"""
        print("🔧 FIXING PRODUCT IMAGES")
        print("=" * 40)
        
        products = Product.objects.all()
        
        for product in products:
            print(f"\n📦 Fixing: {product.name}")
            
            # Find appropriate image for this product
            product_type = product.product_type
            images_for_type = self.product_image_mapping.get(product_type, [])
            
            uploaded_url = None
            
            # Try to find and upload an appropriate image
            for image_filename in images_for_type:
                if image_filename not in self.image_mapping:
                    uploaded_url = self.upload_image_from_media(image_filename)
                    if uploaded_url:
                        self.image_mapping[image_filename] = uploaded_url
                        break
                else:
                    uploaded_url = self.image_mapping[image_filename]
                    break
            
            # If no specific image found, use a generic one
            if not uploaded_url:
                generic_images = ['medicine.png', 'doctor-equipment.png', 'pathology-supplies.png']
                for generic_img in generic_images:
                    if generic_img not in self.image_mapping:
                        uploaded_url = self.upload_image_from_media(generic_img)
                        if uploaded_url:
                            self.image_mapping[generic_img] = uploaded_url
                            break
                    else:
                        uploaded_url = self.image_mapping[generic_img]
                        break
            
            # Update product with new image URL
            if uploaded_url:
                try:
                    with transaction.atomic():
                        product.image = uploaded_url
                        product.save(update_fields=['image'])
                        self.fixed_count += 1
                        print(f"✅ Updated {product.name} with {uploaded_url}")
                except Exception as e:
                    print(f"❌ Failed to update {product.name}: {e}")
                    self.error_count += 1
            else:
                print(f"⚠️ No image found for {product.name}")
                self.error_count += 1
    
    def fix_category_images(self):
        """Fix category images"""
        print(f"\n🏷️ FIXING CATEGORY IMAGES")
        print("=" * 30)
        
        category_images = {
            'Medicine': 'medicine.png',
            'Medical Equipment': 'doctor-equipment.png',
            'Pathology Supplies': 'pathology-supplies.png',
            'Health Supplements': 'health-supplements.png',
            'Surgical Supplies': 'surgical-supplies.png'
        }
        
        for category_name, image_filename in category_images.items():
            try:
                categories = ProductCategory.objects.filter(name__icontains=category_name)
                
                if not categories.exists():
                    continue
                
                # Upload image if not already uploaded
                if image_filename not in self.image_mapping:
                    uploaded_url = self.upload_image_from_media(image_filename)
                    if uploaded_url:
                        self.image_mapping[image_filename] = uploaded_url
                else:
                    uploaded_url = self.image_mapping[image_filename]
                
                if uploaded_url:
                    for category in categories:
                        category.icon = uploaded_url
                        category.save(update_fields=['icon'])
                        print(f"✅ Updated category '{category.name}' with {uploaded_url}")
                        
            except Exception as e:
                print(f"❌ Error updating category '{category_name}': {e}")
    
    def fix_brand_images(self):
        """Fix brand images"""
        print(f"\n🏭 FIXING BRAND IMAGES")
        print("=" * 25)
        
        # Upload MedixMall logo for brands
        medixmall_url = None
        if 'medixmall.jpg' not in self.image_mapping:
            medixmall_url = self.upload_image_from_media('medixmall.jpg')
            if medixmall_url:
                self.image_mapping['medixmall.jpg'] = medixmall_url
        else:
            medixmall_url = self.image_mapping['medixmall.jpg']
        
        if medixmall_url:
            try:
                # Update MedixMall brand specifically
                medixmall_brand = Brand.objects.filter(name__icontains='MedixMall').first()
                if medixmall_brand:
                    medixmall_brand.image = medixmall_url
                    medixmall_brand.save(update_fields=['image'])
                    print(f"✅ Updated MedixMall brand with logo")
                
                # Update other major brands with the logo too
                major_brands = Brand.objects.filter(name__in=['MediPharm', 'HealthTech', 'DiagnoCare'])
                for brand in major_brands:
                    brand.image = medixmall_url
                    brand.save(update_fields=['image'])
                    print(f"✅ Updated brand '{brand.name}' with logo")
                    
            except Exception as e:
                print(f"❌ Error updating brands: {e}")
    
    def verify_fixes(self):
        """Verify that fixes are working"""
        print(f"\n✅ VERIFICATION")
        print("=" * 20)
        
        # Check products
        products_with_imagekit = Product.objects.filter(image__icontains='imagekit.io').count()
        total_products = Product.objects.count()
        
        print(f"📦 Products with ImageKit URLs: {products_with_imagekit}/{total_products}")
        
        # Check categories
        categories_with_imagekit = ProductCategory.objects.filter(icon__icontains='imagekit.io').count()
        total_categories = ProductCategory.objects.count()
        
        print(f"🏷️ Categories with ImageKit URLs: {categories_with_imagekit}/{total_categories}")
        
        # Check brands
        brands_with_imagekit = Brand.objects.filter(image__icontains='imagekit.io').count()
        total_brands = Brand.objects.count()
        
        print(f"🏭 Brands with ImageKit URLs: {brands_with_imagekit}/{total_brands}")
        
        # Show sample URLs for testing
        print(f"\n🌐 SAMPLE URLS TO TEST IN BROWSER:")
        
        sample_product = Product.objects.filter(image__icontains='imagekit.io').first()
        if sample_product:
            print(f"📦 Product: {sample_product.image}")
            
        sample_category = ProductCategory.objects.filter(icon__icontains='imagekit.io').first()
        if sample_category:
            print(f"🏷️ Category: {sample_category.icon}")
            
        sample_brand = Brand.objects.filter(image__icontains='imagekit.io').first()
        if sample_brand:
            print(f"🏭 Brand: {sample_brand.image}")
    
    def run_complete_fix(self):
        """Run complete image fixing process"""
        print("🚀 STARTING COMPLETE IMAGE FIX")
        print("=" * 50)
        
        try:
            # Fix products
            self.fix_product_images()
            
            # Fix categories  
            self.fix_category_images()
            
            # Fix brands
            self.fix_brand_images()
            
            # Verify results
            self.verify_fixes()
            
            print(f"\n📊 FINAL SUMMARY:")
            print(f"   ✅ Fixed: {self.fixed_count} items")
            print(f"   ❌ Errors: {self.error_count} items")
            print(f"   📷 Images uploaded: {len(self.image_mapping)}")
            
            print(f"\n🎯 SUCCESS! All images should now be properly uploaded to ImageKit")
            
        except Exception as e:
            print(f"❌ Critical error during fix: {e}")
            import traceback
            traceback.print_exc()


def main():
    fixer = ProductImageFixer()
    fixer.run_complete_fix()


if __name__ == "__main__":
    main()