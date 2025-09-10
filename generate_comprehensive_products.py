#!/usr/bin/env python3
"""
Generate comprehensive products.json and variant.json based on exact category requirements:
- 3 products per parent category
- 2 products per subcategory  
- 3 variants per product
"""

import os
import json
import random

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
import django
django.setup()

from products.models import ProductCategory, Brand

def generate_comprehensive_products():
    """Generate products according to exact requirements"""
    
    # Get categories and brands
    parent_cats = list(ProductCategory.objects.filter(parent=None).values('id', 'name'))
    sub_cats = list(ProductCategory.objects.exclude(parent=None).values('id', 'name', 'parent__name'))
    brands = list(Brand.objects.all().values('id', 'name'))
    
    print(f"📊 Category Analysis:")
    print(f"   Parent Categories: {len(parent_cats)}")
    print(f"   Sub Categories: {len(sub_cats)}")
    print(f"   Total Products Needed: {len(parent_cats) * 3 + len(sub_cats) * 2}")
    print(f"   Total Variants Needed: {(len(parent_cats) * 3 + len(sub_cats) * 2) * 3}")
    
    products = []
    variants = []
    
    # Medicine products database
    medicine_products = {
        "prescription": [
            {"name": "Amoxicillin Capsules", "composition": "Amoxicillin 500mg", "form": "capsule", "pack_size": "10 capsules", "prescription_required": True},
            {"name": "Metformin Tablets", "composition": "Metformin HCl 500mg", "form": "tablet", "pack_size": "30 tablets", "prescription_required": True},
            {"name": "Atorvastatin Tablets", "composition": "Atorvastatin 20mg", "form": "tablet", "pack_size": "10 tablets", "prescription_required": True},
            {"name": "Lisinopril Tablets", "composition": "Lisinopril 10mg", "form": "tablet", "pack_size": "30 tablets", "prescription_required": True},
            {"name": "Omeprazole Capsules", "composition": "Omeprazole 20mg", "form": "capsule", "pack_size": "14 capsules", "prescription_required": True},
            {"name": "Amlodipine Tablets", "composition": "Amlodipine 5mg", "form": "tablet", "pack_size": "30 tablets", "prescription_required": True},
            {"name": "Losartan Tablets", "composition": "Losartan 50mg", "form": "tablet", "pack_size": "30 tablets", "prescription_required": True},
            {"name": "Simvastatin Tablets", "composition": "Simvastatin 40mg", "form": "tablet", "pack_size": "30 tablets", "prescription_required": True},
            {"name": "Levothyroxine Tablets", "composition": "Levothyroxine 100mcg", "form": "tablet", "pack_size": "100 tablets", "prescription_required": True},
            {"name": "Gabapentin Capsules", "composition": "Gabapentin 300mg", "form": "capsule", "pack_size": "90 capsules", "prescription_required": True},
        ],
        "otc": [
            {"name": "Paracetamol Tablets", "composition": "Paracetamol 500mg", "form": "tablet", "pack_size": "20 tablets", "prescription_required": False},
            {"name": "Ibuprofen Tablets", "composition": "Ibuprofen 400mg", "form": "tablet", "pack_size": "24 tablets", "prescription_required": False},
            {"name": "Aspirin Tablets", "composition": "Aspirin 325mg", "form": "tablet", "pack_size": "100 tablets", "prescription_required": False},
            {"name": "Cetirizine Tablets", "composition": "Cetirizine 10mg", "form": "tablet", "pack_size": "30 tablets", "prescription_required": False},
            {"name": "Vitamin D3 Tablets", "composition": "Cholecalciferol 1000IU", "form": "tablet", "pack_size": "60 tablets", "prescription_required": False},
            {"name": "Calcium Carbonate Tablets", "composition": "Calcium Carbonate 500mg", "form": "tablet", "pack_size": "60 tablets", "prescription_required": False},
            {"name": "Multivitamin Tablets", "composition": "Mixed Vitamins & Minerals", "form": "tablet", "pack_size": "30 tablets", "prescription_required": False},
            {"name": "Probiotics Capsules", "composition": "Lactobacillus Mix 1B CFU", "form": "capsule", "pack_size": "30 capsules", "prescription_required": False},
            {"name": "Omega-3 Capsules", "composition": "Fish Oil 1000mg", "form": "capsule", "pack_size": "60 capsules", "prescription_required": False},
            {"name": "Iron Tablets", "composition": "Ferrous Sulfate 65mg", "form": "tablet", "pack_size": "100 tablets", "prescription_required": False},
        ]
    }
    
    # Equipment products database
    equipment_products = [
        {"name": "Digital Stethoscope", "model": "DS-2000", "equipment_type": "diagnostic", "warranty": "2 years", "usage": "professional"},
        {"name": "Blood Pressure Monitor", "model": "BP-300", "equipment_type": "monitoring", "warranty": "3 years", "usage": "home/clinic"},
        {"name": "Pulse Oximeter", "model": "OX-100", "equipment_type": "monitoring", "warranty": "1 year", "usage": "home/clinic"},
        {"name": "Nebulizer Machine", "model": "NEB-500", "equipment_type": "respiratory", "warranty": "2 years", "usage": "home"},
        {"name": "Thermometer Digital", "model": "TEMP-200", "equipment_type": "diagnostic", "warranty": "1 year", "usage": "home/clinic"},
        {"name": "Glucometer Kit", "model": "GLU-400", "equipment_type": "monitoring", "warranty": "2 years", "usage": "home"},
        {"name": "ECG Machine", "model": "ECG-12L", "equipment_type": "diagnostic", "warranty": "3 years", "usage": "professional"},
        {"name": "Defibrillator AED", "model": "AED-300", "equipment_type": "emergency", "warranty": "5 years", "usage": "professional"},
        {"name": "Wheelchair Standard", "model": "WC-STD", "equipment_type": "mobility", "warranty": "1 year", "usage": "home/clinic"},
        {"name": "Hospital Bed Electric", "model": "BED-E200", "equipment_type": "furniture", "warranty": "2 years", "usage": "professional"},
        {"name": "Surgical Scissors", "model": "SS-125", "equipment_type": "surgical", "warranty": "lifetime", "usage": "professional"},
        {"name": "Forceps Surgical", "model": "FOR-200", "equipment_type": "surgical", "warranty": "lifetime", "usage": "professional"},
        {"name": "Syringe Pump", "model": "SYR-P100", "equipment_type": "infusion", "warranty": "3 years", "usage": "professional"},
        {"name": "UV Sterilizer", "model": "UV-S300", "equipment_type": "sterilization", "warranty": "2 years", "usage": "professional"},
        {"name": "Oxygen Concentrator", "model": "OXY-C500", "equipment_type": "respiratory", "warranty": "3 years", "usage": "home/clinic"},
    ]
    
    # Pathology products database
    pathology_products = [
        {"name": "Blood Collection Tubes", "test_type": "hematology", "sample_type": "blood", "reporting_time": "2-4 hours"},
        {"name": "Urine Collection Cups", "test_type": "urinalysis", "sample_type": "urine", "reporting_time": "1-2 hours"},
        {"name": "Glucose Test Strips", "test_type": "biochemistry", "sample_type": "blood", "reporting_time": "immediate"},
        {"name": "Rapid Test Kits", "test_type": "immunology", "sample_type": "blood/serum", "reporting_time": "15-30 minutes"},
        {"name": "Culture Media Plates", "test_type": "microbiology", "sample_type": "various", "reporting_time": "24-48 hours"},
        {"name": "PCR Test Kits", "test_type": "molecular", "sample_type": "swab/blood", "reporting_time": "4-6 hours"},
        {"name": "Pregnancy Test Strips", "test_type": "hormone", "sample_type": "urine", "reporting_time": "5 minutes"},
        {"name": "Cholesterol Test Kit", "test_type": "lipid profile", "sample_type": "blood", "reporting_time": "immediate"},
        {"name": "HbA1c Test Kit", "test_type": "diabetes", "sample_type": "blood", "reporting_time": "immediate"},
        {"name": "Microscope Slides", "test_type": "histopathology", "sample_type": "tissue", "reporting_time": "24-48 hours"},
    ]
    
    product_id = 1
    
    # Generate products for parent categories (3 each)
    print("\n🔹 Generating products for parent categories...")
    for parent_cat in parent_cats:
        cat_id = parent_cat['id']
        cat_name = parent_cat['name']
        
        for i in range(3):
            product_data = create_product_for_category(cat_name, cat_id, brands, product_id, 
                                                     medicine_products, equipment_products, pathology_products)
            products.append(product_data)
            
            # Generate 3 variants for this product
            product_variants = create_variants_for_product(product_data['name'], product_id)
            variants.extend(product_variants)
            
            product_id += 1
            
        print(f"   ✅ {cat_name}: 3 products created")
    
    # Generate products for sub categories (2 each)
    print("\n🔹 Generating products for sub categories...")
    for sub_cat in sub_cats:
        cat_id = sub_cat['id']
        cat_name = sub_cat['name']
        parent_name = sub_cat['parent__name']
        
        for i in range(2):
            product_data = create_product_for_category(parent_name, cat_id, brands, product_id,
                                                     medicine_products, equipment_products, pathology_products)
            products.append(product_data)
            
            # Generate 3 variants for this product
            product_variants = create_variants_for_product(product_data['name'], product_id)
            variants.extend(product_variants)
            
            product_id += 1
            
        print(f"   ✅ {cat_name}: 2 products created")
    
    # Save files
    with open('products/data/products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    with open('products/data/variant.json', 'w', encoding='utf-8') as f:
        json.dump(variants, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Generation Complete!")
    print(f"   📁 Products created: {len(products)}")
    print(f"   📁 Variants created: {len(variants)}")
    print(f"   📁 Files saved: products.json, variant.json")

def create_product_for_category(parent_cat_name, category_id, brands, product_id, medicine_products, equipment_products, pathology_products):
    """Create a product based on parent category type"""
    
    brand_id = random.choice(brands)['id']
    
    if parent_cat_name == "Medicines":
        # Choose between prescription and OTC
        med_type = random.choice(['prescription', 'otc'])
        med_data = random.choice(medicine_products[med_type])
        
        return {
            "name": med_data['name'],
            "category_id": category_id,
            "brand_id": brand_id,
            "description": f"High quality {med_data['composition']} in {med_data['form']} form. {med_data['pack_size']} per pack.",
            "image": "media/images/medicine_generic.webp",
            "price": round(random.uniform(50, 500), 2),
            "stock": random.randint(50, 200),
            "product_type": "medicine",
            "status": "published",
            "is_publish": True,
            "specifications": {
                "dosage_form": med_data['form'],
                "pack_size": med_data['pack_size'],
                "storage": "Store in cool, dry place"
            },
            "medicine_details": {
                "composition": med_data['composition'],
                "quantity": med_data['pack_size'],
                "manufacturer": random.choice(["PharmaCorp Ltd", "MediLife Industries", "HealthPlus Pharma", "Global Meds Inc"]),
                "prescription_required": med_data['prescription_required'],
                "form": med_data['form'],
                "pack_size": med_data['pack_size'],
                "batch_number": f"BATCH{product_id:06d}"
            }
        }
    
    elif parent_cat_name in ["Doctor Equipment", "Diagnostics & Monitoring", "Surgical & Medical Supplies"]:
        # Equipment product
        eq_data = random.choice(equipment_products)
        
        return {
            "name": eq_data['name'],
            "category_id": category_id,
            "brand_id": brand_id,
            "description": f"Professional grade {eq_data['name']} model {eq_data['model']}. Suitable for {eq_data['usage']} use.",
            "image": f"media/images/{eq_data['name'].lower().replace(' ', '_')}.webp",
            "price": round(random.uniform(1000, 50000), 2),
            "stock": random.randint(10, 50),
            "product_type": "equipment",
            "status": "published",
            "is_publish": True,
            "specifications": {
                "model": eq_data['model'],
                "warranty": eq_data['warranty'],
                "usage_type": eq_data['usage'],
                "certification": "CE, FDA approved"
            },
            "equipment_details": {
                "model_number": eq_data['model'],
                "warranty_period": eq_data['warranty'],
                "usage_type": eq_data['usage'],
                "technical_specifications": f"Advanced {eq_data['equipment_type']} equipment with latest technology",
                "power_requirement": "AC 220V, 50Hz" if eq_data['equipment_type'] not in ['surgical', 'manual'] else "Manual operation",
                "equipment_type": eq_data['equipment_type']
            }
        }
    
    elif parent_cat_name == "Pathology & Laboratory":
        # Pathology product
        path_data = random.choice(pathology_products)
        
        return {
            "name": path_data['name'],
            "category_id": category_id,
            "brand_id": brand_id,
            "description": f"Laboratory grade {path_data['name']} for {path_data['test_type']} testing. Sample type: {path_data['sample_type']}.",
            "image": f"media/images/{path_data['name'].lower().replace(' ', '_')}.webp",
            "price": round(random.uniform(100, 2000), 2),
            "stock": random.randint(20, 100),
            "product_type": "pathology",
            "status": "published",
            "is_publish": True,
            "specifications": {
                "test_type": path_data['test_type'],
                "sample_type": path_data['sample_type'],
                "reporting_time": path_data['reporting_time'],
                "storage": "Store as per manufacturer guidelines"
            },
            "pathology_details": {
                "test_type": path_data['test_type'],
                "sample_type": path_data['sample_type'],
                "reporting_time": path_data['reporting_time'],
                "fasting_required": random.choice([True, False]),
                "test_method": random.choice(["Automated", "Manual", "Semi-automated"]),
                "normal_range": "As per age and gender specific ranges"
            }
        }
    
    else:
        # Healthcare & Wellness, Personal Care & Hygiene - treat as general products
        wellness_products = [
            "Hand Sanitizer", "Face Masks", "Wellness Supplements", "First Aid Kit",
            "Health Monitor", "Fitness Tracker", "Massage Oil", "Health Drinks",
            "Protein Powder", "Ayurvedic Tablets"
        ]
        
        product_name = random.choice(wellness_products)
        
        return {
            "name": product_name,
            "category_id": category_id,
            "brand_id": brand_id,
            "description": f"Premium quality {product_name} for health and wellness.",
            "image": f"media/images/{product_name.lower().replace(' ', '_')}.webp",
            "price": round(random.uniform(200, 1500), 2),
            "stock": random.randint(30, 150),
            "product_type": "medicine",  # Default to medicine type
            "status": "published",
            "is_publish": True,
            "specifications": {
                "category": "Health & Wellness",
                "usage": "Daily health maintenance"
            }
        }

def create_variants_for_product(product_name, product_id):
    """Create 3 variants for each product"""
    variants = []
    
    # Common variant attributes based on product type
    variant_options = [
        {"pack_size": "Small", "price_modifier": 0.8, "stock_modifier": 1.5},
        {"pack_size": "Medium", "price_modifier": 1.0, "stock_modifier": 1.0},
        {"pack_size": "Large", "price_modifier": 1.3, "stock_modifier": 0.7},
    ]
    
    colors = ["White", "Blue", "Black", "Silver", "Grey"]
    
    for i, variant in enumerate(variant_options, 1):
        variant_data = {
            "product_name": product_name,
            "sku": f"VAR{product_id:03d}{i:02d}",
            "price": round(random.uniform(100, 2000) * variant['price_modifier'], 2),
            "stock": int(random.randint(20, 100) * variant['stock_modifier']),
            "weight": round(random.uniform(0.1, 2.0), 2),
            "dimensions": f"{random.randint(5,20)}x{random.randint(5,20)}x{random.randint(2,10)}cm",
            "status": "active",
            "attributes": [
                {"name": "Pack Size", "value": variant['pack_size']},
                {"name": "Color", "value": random.choice(colors)},
                {"name": "Type", "value": random.choice(["Standard", "Premium", "Deluxe"])}
            ]
        }
        variants.append(variant_data)
    
    return variants

if __name__ == "__main__":
    generate_comprehensive_products()
