#!/usr/bin/env python3
"""
Sophisticated Product App Seeder with ImageKit Integration
Analyzes images in media folder and creates comprehensive product data
"""

import os
import django
import sys
import random
from decimal import Decimal
from datetime import datetime, timedelta

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


class ProductSeeder:
    def __init__(self):
        self.admin_user = None
        self.supplier_users = []
        self.regular_users = []
        self.uploaded_images = {}
        self.created_brands = {}
        self.created_categories = {}
        self.created_products = []
        
        # Image categorization based on file names
        self.image_mapping = {
            # Medical Equipment
            'equipment': [
                'BpMonitor.webp',
                'Compression Therapy Machine.jpg',
                'Digital Body Fat Scale.jpg',
                'doctor-equipment.png',
                'ecg-watch.avif',
                'nebulizer.jpg',
                'oxymeter.webp',
                'Personal Emergency Response System.jpg',
                'Portable UV Sanitizer Box.jpg',
                'Professional Stethoscope.jpg',
                'sleep machine.jpg',
                'smart glass.jpg',
                'Smart Hearing Aid.jpg',
                'Therapeutic Cold Laser Device.avif',
                'thermameter.jpg',
                'wireless.jpeg'
            ],
            
            # Medicine & Pharmaceuticals
            'medicine': [
                'medicine.png',
                'glucose.webp',
                'Medicine Pill Organizer with Alarm.jpg',
                'N75.jpg',
                'N95 Respirator Masks.jpg',
                'Hospital-Grade Hand Sanitizer.jpg',
                'health-supplements.png'
            ],
            
            # Pathology & Laboratory
            'pathology': [
                'pathology-supplies.png',
                'Home Saliva Drug Test Kit.jpg',
                'firstaid.jpg',
                'surgical-supplies.png'
            ],
            
            # Mobility & Support
            'mobility': [
                'Adjustable Walking Cane.webp',
                'Lightweight Folding Wheelchair.jpg',
                'Posture Corrector Brace.webp'
            ],
            
            # Brand/Company logos
            'brands': [
                'medixmall.jpg'
            ],
            
            # General/UI images
            'general': [
                'medical-pattern.svg',
                'prescription-upload.png',
                'prescription-upload.svg',
                'rx.svg'
            ]
        }
        
        # Product data templates
        self.product_templates = {
            'medicine': {
                'Paracetamol': {
                    'description': 'Fast-acting pain relief and fever reducer',
                    'composition': 'Paracetamol 500mg',
                    'manufacturer': 'MediPharm Ltd',
                    'form': 'tablet',
                    'pack_size': '10 tablets',
                    'prescription_required': False,
                    'price_range': (25, 75)
                },
                'Glucose Powder': {
                    'description': 'Instant energy glucose powder for quick energy boost',
                    'composition': 'Glucose 99.9%',
                    'manufacturer': 'Health Plus',
                    'form': 'powder',
                    'pack_size': '200g',
                    'prescription_required': False,
                    'price_range': (45, 85)
                },
                'Health Supplements': {
                    'description': 'Complete multivitamin and mineral supplement',
                    'composition': 'Vitamins A, B, C, D, E + Minerals',
                    'manufacturer': 'NutriHealth',
                    'form': 'capsule',
                    'pack_size': '30 capsules',
                    'prescription_required': False,
                    'price_range': (299, 599)
                },
                'N95 Mask': {
                    'description': 'High-filtration respiratory protection mask',
                    'composition': 'Non-woven fabric with melt-blown filter',
                    'manufacturer': 'SafeGuard Medical',
                    'form': 'mask',
                    'pack_size': '10 pieces',
                    'prescription_required': False,
                    'price_range': (150, 300)
                },
                'Hand Sanitizer': {
                    'description': 'Hospital-grade alcohol-based hand sanitizer',
                    'composition': 'Ethyl Alcohol 70%, Glycerin, Aloe Vera',
                    'manufacturer': 'CleanMed',
                    'form': 'gel',
                    'pack_size': '500ml',
                    'prescription_required': False,
                    'price_range': (120, 250)
                }
            },
            
            'equipment': {
                'Digital Blood Pressure Monitor': {
                    'description': 'Automatic digital BP monitor with large display',
                    'model_number': 'BP-2000X',
                    'warranty_period': '2 years',
                    'usage_type': 'Home use',
                    'technical_specifications': 'Range: 0-299mmHg, Memory: 99 readings',
                    'power_requirement': '4 AA batteries or AC adapter',
                    'equipment_type': 'Diagnostic Equipment',
                    'price_range': (1499, 3499)
                },
                'Pulse Oximeter': {
                    'description': 'Fingertip pulse oximeter for oxygen saturation monitoring',
                    'model_number': 'OXY-100',
                    'warranty_period': '1 year',
                    'usage_type': 'Home/Clinical use',
                    'technical_specifications': 'SpO2: 70-100%, Pulse: 30-250bpm',
                    'power_requirement': '2 AAA batteries',
                    'equipment_type': 'Monitoring Device',
                    'price_range': (899, 1999)
                },
                'Digital Thermometer': {
                    'description': 'Fast and accurate digital thermometer',
                    'model_number': 'TEMP-FAST',
                    'warranty_period': '1 year',
                    'usage_type': 'Home use',
                    'technical_specifications': 'Range: 32-42.9°C, Accuracy: ±0.1°C',
                    'power_requirement': '1 LR41 battery',
                    'equipment_type': 'Diagnostic Equipment',
                    'price_range': (299, 799)
                },
                'ECG Watch': {
                    'description': 'Smart ECG monitoring watch with health tracking',
                    'model_number': 'ECG-SMART-01',
                    'warranty_period': '1 year',
                    'usage_type': 'Personal monitoring',
                    'technical_specifications': '12-lead ECG, Heart rate, Blood pressure estimation',
                    'power_requirement': 'Rechargeable Li-ion battery',
                    'equipment_type': 'Wearable Device',
                    'price_range': (4999, 9999)
                },
                'Nebulizer': {
                    'description': 'Portable nebulizer for respiratory medication delivery',
                    'model_number': 'NEB-COMP-500',
                    'warranty_period': '2 years',
                    'usage_type': 'Home/Clinical use',
                    'technical_specifications': 'Particle size: 0.5-5μm, Flow rate: 0.2ml/min',
                    'power_requirement': '220V AC',
                    'equipment_type': 'Respiratory Equipment',
                    'price_range': (2499, 5999)
                },
                'Digital Weight Scale': {
                    'description': 'Digital body fat scale with BMI calculation',
                    'model_number': 'SCALE-BF-200',
                    'warranty_period': '1 year',
                    'usage_type': 'Home use',
                    'technical_specifications': 'Capacity: 180kg, Body fat %, BMI, Muscle mass',
                    'power_requirement': '4 AAA batteries',
                    'equipment_type': 'Health Monitoring',
                    'price_range': (1299, 2999)
                },
                'Stethoscope': {
                    'description': 'Professional-grade stethoscope for medical examination',
                    'model_number': 'STETHO-PRO-2000',
                    'warranty_period': '5 years',
                    'usage_type': 'Professional use',
                    'technical_specifications': 'Dual-head design, High acoustic sensitivity',
                    'power_requirement': 'None (Manual)',
                    'equipment_type': 'Diagnostic Equipment',
                    'price_range': (1999, 4999)
                }
            },
            
            'pathology': {
                'Drug Test Kit': {
                    'description': 'Home saliva drug test kit for multiple substances',
                    'compatible_tests': 'Cocaine, Marijuana, Opiates, Amphetamines',
                    'chemical_composition': 'Immunoassay test strips',
                    'storage_condition': 'Store at 2-30°C, dry place',
                    'price_range': (499, 999)
                },
                'First Aid Kit': {
                    'description': 'Complete first aid kit for home and office use',
                    'compatible_tests': 'Emergency treatment supplies',
                    'chemical_composition': 'Bandages, antiseptic, gauze, medical tape',
                    'storage_condition': 'Store in cool, dry place',
                    'price_range': (299, 799)
                },
                'Surgical Supplies': {
                    'description': 'Sterile surgical supplies for medical procedures',
                    'compatible_tests': 'Minor surgical procedures',
                    'chemical_composition': 'Sterile cotton, surgical blades, forceps',
                    'storage_condition': 'Store in sterile environment',
                    'price_range': (199, 599)
                },
                'Pathology Collection Kit': {
                    'description': 'Sample collection kit for laboratory testing',
                    'compatible_tests': 'Blood, urine, saliva sample collection',
                    'chemical_composition': 'Collection tubes, preservatives, labels',
                    'storage_condition': 'Store at room temperature',
                    'price_range': (99, 299)
                }
            }
        }
        
        self.brands_data = {
            'MediPharm': 'Leading pharmaceutical company',
            'HealthTech': 'Medical equipment manufacturer',
            'DiagnoCare': 'Diagnostic equipment specialist',
            'MedSupply': 'Medical supplies provider',
            'CareFirst': 'Healthcare solutions provider',
            'MedixMall': 'Healthcare marketplace',
            'LifeCare': 'Life sciences company',
            'MedEquip': 'Medical equipment solutions'
        }
    
    def setup_users(self):
        """Create or get required users"""
        print("🔧 Setting up users...")
        
        # Get or create admin user
        try:
            self.admin_user = User.objects.get(email='admin@example.com')
            print("✅ Admin user found")
        except User.DoesNotExist:
            print("❌ Admin user not found. Please create admin user first.")
            return False
        
        # Get existing supplier and regular users
        self.supplier_users = list(User.objects.filter(role='supplier')[:3])
        self.regular_users = list(User.objects.filter(role='user')[:5])
        
        print(f"✅ Found {len(self.supplier_users)} supplier users")
        print(f"✅ Found {len(self.regular_users)} regular users")
        
        return True
    
    def upload_images_to_imagekit(self):
        """Upload all images from media folder to ImageKit"""
        print("\n📷 Uploading images to ImageKit...")
        
        images_dir = "media/images"
        success_count = 0
        error_count = 0
        
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif', '.svg')):
                image_path = os.path.join(images_dir, filename)
                
                try:
                    with open(image_path, 'rb') as image_file:
                        # Generate a clean filename for ImageKit
                        clean_filename = slugify(filename.rsplit('.', 1)[0]) + '.' + filename.rsplit('.', 1)[1]
                        
                        # Upload to ImageKit
                        uploaded_url = upload_image(image_file.read(), clean_filename)
                        
                        if 'imagekit.io' in uploaded_url:
                            self.uploaded_images[filename] = uploaded_url
                            success_count += 1
                            print(f"✅ {filename} -> {uploaded_url}")
                        else:
                            error_count += 1
                            print(f"❌ Failed to upload {filename}")
                            
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error uploading {filename}: {e}")
        
        print(f"\n📊 Upload Summary: {success_count} successful, {error_count} failed")
        return success_count > 0
    
    def create_brands(self):
        """Create brands with uploaded images"""
        print("\n🏭 Creating brands...")
        
        # Use medixmall.jpg for MedixMall brand if available
        medixmall_image = self.uploaded_images.get('medixmall.jpg', '')
        
        for brand_name, description in self.brands_data.items():
            try:
                brand, created = Brand.objects.get_or_create(
                    name=brand_name,
                    defaults={
                        'image': medixmall_image if brand_name == 'MedixMall' else '',
                        'created_by': self.admin_user
                    }
                )
                
                self.created_brands[brand_name] = brand
                status = "created" if created else "exists"
                print(f"✅ Brand '{brand_name}' {status}")
                
            except Exception as e:
                print(f"❌ Error creating brand '{brand_name}': {e}")
    
    def create_categories(self):
        """Create product categories with uploaded images"""
        print("\n🏷️ Creating categories...")
        
        categories_data = {
            'Medicine': {
                'icon': self.uploaded_images.get('medicine.png', ''),
                'subcategories': ['Pain Relief', 'Diabetes Care', 'Vitamins & Supplements']
            },
            'Medical Equipment': {
                'icon': self.uploaded_images.get('doctor-equipment.png', ''),
                'subcategories': ['Diagnostic Equipment', 'Monitoring Devices', 'Respiratory Equipment']
            },
            'Pathology Supplies': {
                'icon': self.uploaded_images.get('pathology-supplies.png', ''),
                'subcategories': ['Test Kits', 'Collection Supplies', 'Emergency Supplies']
            },
            'Health Supplements': {
                'icon': self.uploaded_images.get('health-supplements.png', ''),
                'subcategories': ['Multivitamins', 'Protein Supplements', 'Herbal Supplements']
            },
            'Surgical Supplies': {
                'icon': self.uploaded_images.get('surgical-supplies.png', ''),
                'subcategories': ['Disposable Items', 'Instruments', 'Protective Equipment']
            }
        }
        
        for category_name, category_data in categories_data.items():
            try:
                # Create main category
                category, created = ProductCategory.objects.get_or_create(
                    name=category_name,
                    defaults={
                        'icon': category_data['icon'],
                        'created_by': self.admin_user,
                        'is_publish': True,
                        'status': 'published'
                    }
                )
                
                self.created_categories[category_name] = category
                status = "created" if created else "exists"
                print(f"✅ Category '{category_name}' {status}")
                
                # Create subcategories
                for subcategory_name in category_data['subcategories']:
                    subcategory, sub_created = ProductCategory.objects.get_or_create(
                        name=subcategory_name,
                        defaults={
                            'parent': category,
                            'created_by': self.admin_user,
                            'is_publish': True,
                            'status': 'published'
                        }
                    )
                    
                    sub_status = "created" if sub_created else "exists"
                    print(f"  ✅ Subcategory '{subcategory_name}' {sub_status}")
                
            except Exception as e:
                print(f"❌ Error creating category '{category_name}': {e}")
    
    def create_products(self):
        """Create products with uploaded images"""
        print("\n💊 Creating products...")
        
        product_count = 0
        
        # Medicine products
        medicine_images = self.image_mapping['medicine']
        medicine_category = self.created_categories.get('Medicine')
        
        if medicine_category:
            for product_name, product_data in self.product_templates['medicine'].items():
                # Find appropriate image
                product_image = ''
                for img_filename in medicine_images:
                    if img_filename in self.uploaded_images:
                        product_image = self.uploaded_images[img_filename]
                        break
                
                try:
                    product = Product.objects.create(
                        name=product_name,
                        category=medicine_category,
                        brand=random.choice(list(self.created_brands.values())),
                        description=product_data['description'],
                        image=product_image,
                        product_type='medicine',
                        price=Decimal(str(random.randint(*product_data['price_range']))),
                        stock=random.randint(50, 200),
                        composition=product_data['composition'],
                        manufacturer=product_data['manufacturer'],
                        form=product_data['form'],
                        pack_size=product_data['pack_size'],
                        prescription_required=product_data['prescription_required'],
                        quantity=f"{random.randint(1, 10) * 100}mg",
                        expiry_date=datetime.now().date() + timedelta(days=random.randint(365, 1095)),
                        batch_number=f"BT{random.randint(10000, 99999)}",
                        created_by=self.admin_user,
                        is_publish=True,
                        status='published'
                    )
                    
                    self.created_products.append(product)
                    product_count += 1
                    print(f"✅ Medicine product '{product_name}' created")
                    
                except Exception as e:
                    print(f"❌ Error creating medicine product '{product_name}': {e}")
        
        # Equipment products
        equipment_images = self.image_mapping['equipment']
        equipment_category = self.created_categories.get('Medical Equipment')
        
        if equipment_category:
            for product_name, product_data in self.product_templates['equipment'].items():
                # Find appropriate image
                product_image = ''
                for img_filename in equipment_images:
                    if img_filename in self.uploaded_images:
                        product_image = self.uploaded_images[img_filename]
                        break
                
                try:
                    product = Product.objects.create(
                        name=product_name,
                        category=equipment_category,
                        brand=random.choice(list(self.created_brands.values())),
                        description=product_data['description'],
                        image=product_image,
                        product_type='equipment',
                        price=Decimal(str(random.randint(*product_data['price_range']))),
                        stock=random.randint(10, 50),
                        model_number=product_data['model_number'],
                        warranty_period=product_data['warranty_period'],
                        usage_type=product_data['usage_type'],
                        technical_specifications=product_data['technical_specifications'],
                        power_requirement=product_data['power_requirement'],
                        equipment_type=product_data['equipment_type'],
                        created_by=self.admin_user,
                        is_publish=True,
                        status='published'
                    )
                    
                    self.created_products.append(product)
                    product_count += 1
                    print(f"✅ Equipment product '{product_name}' created")
                    
                except Exception as e:
                    print(f"❌ Error creating equipment product '{product_name}': {e}")
        
        # Pathology products
        pathology_images = self.image_mapping['pathology']
        pathology_category = self.created_categories.get('Pathology Supplies')
        
        if pathology_category:
            for product_name, product_data in self.product_templates['pathology'].items():
                # Find appropriate image
                product_image = ''
                for img_filename in pathology_images:
                    if img_filename in self.uploaded_images:
                        product_image = self.uploaded_images[img_filename]
                        break
                
                try:
                    product = Product.objects.create(
                        name=product_name,
                        category=pathology_category,
                        brand=random.choice(list(self.created_brands.values())),
                        description=product_data['description'],
                        image=product_image,
                        product_type='pathology',
                        price=Decimal(str(random.randint(*product_data['price_range']))),
                        stock=random.randint(20, 100),
                        compatible_tests=product_data['compatible_tests'],
                        chemical_composition=product_data['chemical_composition'],
                        storage_condition=product_data['storage_condition'],
                        created_by=self.admin_user,
                        is_publish=True,
                        status='published'
                    )
                    
                    self.created_products.append(product)
                    product_count += 1
                    print(f"✅ Pathology product '{product_name}' created")
                    
                except Exception as e:
                    print(f"❌ Error creating pathology product '{product_name}': {e}")
        
        print(f"\n📊 Created {product_count} products total")
    
    def create_variants_and_prices(self):
        """Create product variants and supplier prices"""
        print("\n🔄 Creating product variants and supplier prices...")
        
        variant_count = 0
        price_count = 0
        
        for product in self.created_products:
            try:
                # Create 1-2 variants per product
                for i in range(random.randint(1, 3)):
                    sizes = ['Small', 'Medium', 'Large', 'XL'] if product.product_type == 'equipment' else ['Regular', 'Family Pack']
                    weights = ['100g', '250g', '500g', '1kg'] if product.product_type == 'medicine' else None
                    
                    variant_data = {
                        'product': product,
                        'size': random.choice(sizes),
                        'additional_price': Decimal(str(random.randint(0, 100))),
                        'stock': random.randint(10, 50)
                    }
                    
                    if weights:
                        variant_data['weight'] = random.choice(weights)
                    
                    # Check if variant already exists
                    existing_variant = ProductVariant.objects.filter(
                        product=product,
                        size=variant_data['size'],
                        weight=variant_data.get('weight')
                    ).first()
                    
                    if not existing_variant:
                        variant = ProductVariant.objects.create(**variant_data)
                        variant_count += 1
                
                # Create supplier prices if we have suppliers
                if self.supplier_users:
                    for supplier in random.sample(self.supplier_users, min(2, len(self.supplier_users))):
                        pincodes = ['110001', '400001', '560001', '700001', '500001']
                        districts = ['New Delhi', 'Mumbai', 'Bangalore', 'Kolkata', 'Hyderabad']
                        
                        price_data = {
                            'supplier': supplier,
                            'product': product,
                            'price': product.price - Decimal(str(random.randint(10, 50))),
                            'pincode': random.choice(pincodes),
                            'district': random.choice(districts)
                        }
                        
                        # Check if price already exists
                        existing_price = SupplierProductPrice.objects.filter(
                            supplier=supplier,
                            product=product,
                            pincode=price_data['pincode'],
                            district=price_data['district']
                        ).first()
                        
                        if not existing_price:
                            supplier_price = SupplierProductPrice.objects.create(**price_data)
                            price_count += 1
                            
            except Exception as e:
                print(f"❌ Error creating variants/prices for '{product.name}': {e}")
        
        print(f"✅ Created {variant_count} variants")
        print(f"✅ Created {price_count} supplier prices")
    
    def create_reviews(self):
        """Create product reviews"""
        print("\n⭐ Creating product reviews...")
        
        if not self.regular_users:
            print("⚠️ No regular users found for creating reviews")
            return
        
        review_count = 0
        
        for product in self.created_products:
            # Create 2-5 reviews per product
            num_reviews = random.randint(2, 5)
            review_users = random.sample(self.regular_users, min(num_reviews, len(self.regular_users)))
            
            for user in review_users:
                try:
                    # Check if review already exists
                    existing_review = ProductReview.objects.filter(product=product, user=user).first()
                    
                    if not existing_review:
                        rating = random.randint(3, 5)  # Mostly positive reviews
                        comments = [
                            "Excellent product, highly recommended!",
                            "Good quality and fast delivery.",
                            "Works as expected, satisfied with purchase.",
                            "Great value for money.",
                            "Professional grade quality.",
                            "Would buy again.",
                            "Helpful for daily use."
                        ]
                        
                        review = ProductReview.objects.create(
                            product=product,
                            user=user,
                            rating=rating,
                            comment=random.choice(comments),
                            is_published=True
                        )
                        
                        review_count += 1
                        
                except Exception as e:
                    print(f"❌ Error creating review for '{product.name}': {e}")
        
        print(f"✅ Created {review_count} reviews")
    
    def run_seeder(self):
        """Run the complete seeding process"""
        print("🚀 STARTING SOPHISTICATED PRODUCT SEEDER")
        print("=" * 60)
        
        # Step 1: Setup users
        if not self.setup_users():
            print("❌ Failed to setup users. Aborting.")
            return
        
        # Step 2: Upload images to ImageKit
        if not self.upload_images_to_imagekit():
            print("❌ Failed to upload images. Aborting.")
            return
        
        # Step 3: Create brands
        self.create_brands()
        
        # Step 4: Create categories
        self.create_categories()
        
        # Step 5: Create products
        self.create_products()
        
        # Step 6: Create variants and supplier prices
        self.create_variants_and_prices()
        
        # Step 7: Create reviews
        self.create_reviews()
        
        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Summary
        print(f"📊 Summary:")
        print(f"   🏭 Brands: {len(self.created_brands)}")
        print(f"   🏷️ Categories: {len(self.created_categories)}")
        print(f"   💊 Products: {len(self.created_products)}")
        print(f"   📷 Images uploaded: {len(self.uploaded_images)}")
        print(f"   🔗 All images stored on ImageKit server")
        
        print(f"\n🌐 Sample ImageKit URLs:")
        for filename, url in list(self.uploaded_images.items())[:3]:
            print(f"   {filename}: {url}")


def main():
    seeder = ProductSeeder()
    seeder.run_seeder()


if __name__ == "__main__":
    main()