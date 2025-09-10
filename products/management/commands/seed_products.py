import json
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import (
    Product, ProductCategory, Brand, ProductVariant, ProductAttribute, 
    ProductAttributeValue, MedicineDetails, EquipmentDetails, PathologyDetails
)
from accounts.models import upload_to_imagekit
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed products and variants from JSON data files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing products before seeding',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Deleting existing products...')
            Product.objects.all().delete()
            ProductAttribute.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing products deleted.'))

        # Get or create admin user for created_by field
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'full_name': 'Admin User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.email}')

        # Load product data
        products_file = os.path.join('products', 'data', 'products.json')
        variants_file = os.path.join('products', 'data', 'variant.json')

        if not os.path.exists(products_file):
            self.stdout.write(self.style.ERROR(f'Products file not found: {products_file}'))
            return

        if not os.path.exists(variants_file):
            self.stdout.write(self.style.ERROR(f'Variants file not found: {variants_file}'))
            return

        with open(products_file, 'r') as f:
            products_data = json.load(f)

        with open(variants_file, 'r') as f:
            variants_data = json.load(f)

        self.stdout.write(f'Loaded {len(products_data)} products and {len(variants_data)} variants')

        # Create products
        created_products = {}
        for product_data in products_data:
            try:
                # Get category and brand
                category = ProductCategory.objects.get(id=product_data['category_id'])
                brand = None
                if product_data.get('brand_id'):
                    brand = Brand.objects.get(id=product_data['brand_id'])

                # Get optimized image URL
                image_url = self.get_product_image_url(product_data)

                # Create product
                product = Product.objects.create(
                    name=product_data['name'],
                    category=category,
                    brand=brand,
                    description=product_data.get('description', ''),
                    image=image_url,
                    price=Decimal(str(product_data.get('price', '0.00'))),
                    stock=product_data.get('stock', 0),
                    product_type=product_data.get('product_type', 'medicine'),
                    status=product_data.get('status', 'published'),
                    is_publish=product_data.get('is_publish', True),
                    created_by=admin_user,
                    specifications=product_data.get('specifications', {})
                )

                # Create type-specific details
                if product.product_type == 'medicine' and 'medicine_details' in product_data:
                    med_data = product_data['medicine_details']
                    MedicineDetails.objects.create(
                        product=product,
                        composition=med_data.get('composition', ''),
                        quantity=med_data.get('quantity', ''),
                        manufacturer=med_data.get('manufacturer', ''),
                        prescription_required=med_data.get('prescription_required', False),
                        form=med_data.get('form', ''),
                        pack_size=med_data.get('pack_size', ''),
                        batch_number=med_data.get('batch_number', f'BATCH{product.id:06d}')
                    )
                elif product.product_type == 'equipment' and 'equipment_details' in product_data:
                    eq_data = product_data['equipment_details']
                    EquipmentDetails.objects.create(
                        product=product,
                        model_number=eq_data.get('model_number', ''),
                        warranty_period=eq_data.get('warranty_period', ''),
                        usage_type=eq_data.get('usage_type', ''),
                        technical_specifications=eq_data.get('technical_specifications', ''),
                        power_requirement=eq_data.get('power_requirement', ''),
                        equipment_type=eq_data.get('equipment_type', '')
                    )
                elif product.product_type == 'pathology' and 'pathology_details' in product_data:
                    path_data = product_data['pathology_details']
                    PathologyDetails.objects.create(
                        product=product,
                        compatible_tests=path_data.get('test_type', ''),
                        chemical_composition=path_data.get('test_method', ''),
                        storage_condition=path_data.get('storage_condition', 'Store as per manufacturer guidelines')
                    )

                created_products[product_data['name']] = product
                self.stdout.write(f'✅ Created product: {product.name} with image: {product.image}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error creating product {product_data.get("name", "Unknown")}: {str(e)}'))
                continue

        self.stdout.write(f'✅ Created {len(created_products)} products')

        # Create variants
        created_variants = 0
        for variant_data in variants_data:
            try:
                product_name = variant_data.get('product_name', '')
                if product_name not in created_products:
                    self.stdout.write(self.style.WARNING(f'⚠️ Product "{product_name}" not found for variant, skipping...'))
                    continue

                product = created_products[product_name]

                # Create variant
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=variant_data.get('sku', f'VAR{product.id}001'),
                    price=Decimal(str(variant_data.get('price', '0.00'))),
                    additional_price=Decimal(str(variant_data.get('additional_price', '0.00'))),
                    stock=variant_data.get('stock', 0),
                    is_active=True
                )

                # Create and assign attributes
                for attr_data in variant_data.get('attributes', []):
                    attr_name = attr_data.get('name', '')
                    attr_value = attr_data.get('value', '')
                    
                    if attr_name and attr_value:
                        # Get or create attribute
                        attribute, _ = ProductAttribute.objects.get_or_create(name=attr_name)
                        
                        # Get or create attribute value
                        attr_value_obj, _ = ProductAttributeValue.objects.get_or_create(
                            attribute=attribute,
                            value=attr_value
                        )
                        
                        # Assign to variant
                        variant.attributes.add(attr_value_obj)

                created_variants += 1
                self.stdout.write(f'✅ Created variant: {variant.sku} for {product.name}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error creating variant: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'🎉 Successfully created {len(created_products)} products and {created_variants} variants!'))

    def create_optimized_product_image(self, product_name, product_type='medicine', size=800, quality=85):
        """Create a highly optimized product image based on product type with higher resolution for detail views"""
        try:
            # Create background based on product type
            if product_type == 'medicine':
                bg_color = '#f0f9ff'  # Light blue for medicines
                accent_color = '#0ea5e9'  # Sky blue
                icon_color = '#0369a1'
            elif product_type == 'equipment':
                bg_color = '#f0fdf4'  # Light green for equipment
                accent_color = '#22c55e'  # Green
                icon_color = '#15803d'
            elif product_type == 'pathology':
                bg_color = '#fdf4ff'  # Light purple for pathology
                accent_color = '#a855f7'  # Purple
                icon_color = '#7c3aed'
            else:
                bg_color = '#f8fafc'  # Default light gray
                accent_color = '#64748b'  # Gray
                icon_color = '#475569'

            image = Image.new('RGB', (size, size), color=bg_color)
            draw = ImageDraw.Draw(image)
            
            # Add subtle gradient background
            for y in range(size):
                # Very subtle gradient
                base_r, base_g, base_b = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
                color_factor = 1 + (0.05 * y / size)
                color = (
                    min(255, int(base_r * color_factor)),
                    min(255, int(base_g * color_factor)),
                    min(255, int(base_b * color_factor))
                )
                draw.line([(0, y), (size, y)], fill=color)
            
            # Product initial in a modern circle
            initial = product_name[0].upper()
            circle_size = size // 2.5
            circle_x = (size - circle_size) // 2
            circle_y = (size - circle_size) // 2
            
            # Draw modern circle with shadow effect
            shadow_offset = 2
            draw.ellipse(
                [circle_x + shadow_offset, circle_y + shadow_offset, 
                 circle_x + circle_size + shadow_offset, circle_y + circle_size + shadow_offset],
                fill='#e2e8f0'  # Light shadow
            )
            
            # Main circle
            draw.ellipse(
                [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
                fill=accent_color,
                outline=icon_color,
                width=2
            )
            
            # Add product initial
            try:
                font_size = circle_size // 3
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Center the text
            bbox = draw.textbbox((0, 0), initial, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = circle_x + (circle_size - text_width) // 2
            text_y = circle_y + (circle_size - text_height) // 2
            
            draw.text(
                (text_x, text_y),
                initial,
                fill='white',
                font=font
            )
            
            # Add product name at bottom (smaller font)
            try:
                name_font_size = max(8, size // 20)
                name_font = ImageFont.truetype("arial.ttf", name_font_size)
            except:
                name_font = ImageFont.load_default()
            
            # Truncate long names for optimization
            display_name = product_name if len(product_name) <= 12 else product_name[:9] + "..."
            
            name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (size - name_width) // 2
            name_y = size - size // 6
            
            draw.text(
                (name_x, name_y),
                display_name,
                fill=icon_color,
                font=name_font
            )
            
            # Optimize for web with aggressive compression
            output = BytesIO()
            
            # Convert to P mode (palette) for smaller PNG files
            image = image.convert('P', palette=Image.ADAPTIVE, colors=64)
            image.save(output, format='PNG', optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating optimized image for {product_name}: {e}")
            return None

    def get_product_image_url(self, product_data, use_imagekit=True, image_size=800, quality=85):
        """Get product image URL, prioritizing existing media files over generated images"""
        product_name = product_data.get('name', '')
        product_type = product_data.get('product_type', 'medicine')
        existing_image = product_data.get('image', '')
        
        # Priority 1: Check if there's a specific image file mentioned in data
        if existing_image and existing_image.startswith('media/images/'):
            image_filename = os.path.basename(existing_image)
            image_path = os.path.join('media', 'images', image_filename)
            
            if os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    
                    if use_imagekit:
                        imagekit_filename = f"product_{product_name.lower().replace(' ', '_').replace('&', 'and')}.{image_filename.split('.')[-1]}"
                        
                        uploaded_url = upload_to_imagekit(
                            image_data,
                            f"products/{imagekit_filename}",
                            {
                                'product': product_name,
                                'type': 'product_image',
                                'product_type': product_type,
                                'source': 'existing_media'
                            }
                        )
                        
                        if uploaded_url:
                            if 'imagekit.io' in uploaded_url:
                                optimization_params = (
                                    f"tr=w-{image_size},h-{image_size},"
                                    f"q-{quality},f-auto,pr-true,lo-true"
                                )
                                if '?' in uploaded_url:
                                    return f"{uploaded_url}&{optimization_params}"
                                else:
                                    return f"{uploaded_url}?{optimization_params}"
                            else:
                                return uploaded_url
                except Exception as e:
                    logger.error(f"Error uploading existing image for {product_name}: {e}")
        
        # Priority 2: Look for matching images in media/images based on product name/type
        product_name_clean = product_name.lower().replace(' ', '_').replace('&', 'and')
        
        # Common image patterns to check
        possible_filenames = [
            f"{product_name_clean}.webp",
            f"{product_name_clean}.jpg", 
            f"{product_name_clean}.jpeg",
            f"{product_name_clean}.png",
            # Generic type-based images
            f"{product_type}_generic.webp",
            f"{product_type}_default.jpg",
            "medicine_generic.webp" if product_type == 'medicine' else None,
            "equipment_generic.jpg" if product_type == 'equipment' else None,
            "pathology_generic.webp" if product_type == 'pathology' else None,
        ]
        
        # Remove None values
        possible_filenames = [f for f in possible_filenames if f]
        
        for filename in possible_filenames:
            image_path = os.path.join('media', 'images', filename)
            if os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                    
                    if use_imagekit:
                        imagekit_filename = f"product_{product_name_clean}.{filename.split('.')[-1]}"
                        
                        uploaded_url = upload_to_imagekit(
                            image_data,
                            f"products/{imagekit_filename}",
                            {
                                'product': product_name,
                                'type': 'product_image', 
                                'product_type': product_type,
                                'source': f'media_images_{filename}'
                            }
                        )
                        
                        if uploaded_url:
                            if 'imagekit.io' in uploaded_url:
                                optimization_params = (
                                    f"tr=w-{image_size},h-{image_size},"
                                    f"q-{quality},f-auto,pr-true,lo-true"
                                )
                                if '?' in uploaded_url:
                                    return f"{uploaded_url}&{optimization_params}"
                                else:
                                    return f"{uploaded_url}?{optimization_params}"
                            else:
                                return uploaded_url
                except Exception as e:
                    logger.error(f"Error uploading {filename} for {product_name}: {e}")
                    continue
        
        # Priority 3: Check for default product images in media/products/
        default_product_paths = [
            os.path.join('media', 'products', f'{product_type}_default.webp'),
            os.path.join('media', 'products', f'{product_type}_default.jpg'),
            os.path.join('media', 'products', 'default.webp'),
            os.path.join('media', 'products', 'default.jpg'),
            os.path.join('media', 'products', 'default.png'),
        ]
        
        for default_path in default_product_paths:
            if os.path.exists(default_path):
                try:
                    with open(default_path, 'rb') as f:
                        image_data = f.read()
                    
                    if use_imagekit:
                        filename = os.path.basename(default_path)
                        imagekit_filename = f"product_{product_name_clean}_default.{filename.split('.')[-1]}"
                        
                        uploaded_url = upload_to_imagekit(
                            image_data,
                            f"products/{imagekit_filename}",
                            {
                                'product': product_name,
                                'type': 'product_image',
                                'product_type': product_type,
                                'source': 'default_product_image'
                            }
                        )
                        
                        if uploaded_url:
                            if 'imagekit.io' in uploaded_url:
                                optimization_params = (
                                    f"tr=w-{image_size},h-{image_size},"
                                    f"q-{quality},f-auto,pr-true,lo-true"
                                )
                                if '?' in uploaded_url:
                                    return f"{uploaded_url}&{optimization_params}"
                                else:
                                    return f"{uploaded_url}?{optimization_params}"
                            else:
                                return uploaded_url
                except Exception as e:
                    logger.error(f"Error uploading default image for {product_name}: {e}")
                    continue
        
        # Priority 4: Generate optimized image as last resort
        logger.warning(f"No existing images found for {product_name}, generating optimized placeholder")
        try:
            image_data = self.create_optimized_product_image(
                product_name, 
                product_type, 
                size=image_size, 
                quality=quality
            )
            
            if image_data and use_imagekit:
                image_filename = f"product_{product_name_clean}_generated.png"
                
                uploaded_url = upload_to_imagekit(
                    image_data,
                    f"products/{image_filename}",
                    {
                        'product': product_name,
                        'type': 'product_image',
                        'product_type': product_type,
                        'generated': 'true',
                        'size': f"{image_size}x{image_size}",
                        'quality': str(quality)
                    }
                )
                
                if uploaded_url:
                    if 'imagekit.io' in uploaded_url:
                        optimization_params = (
                            f"tr=w-{image_size},h-{image_size},"
                            f"q-{quality},f-auto,pr-true,lo-true"
                        )
                        if '?' in uploaded_url:
                            return f"{uploaded_url}&{optimization_params}"
                        else:
                            return f"{uploaded_url}?{optimization_params}"
                    else:
                        return uploaded_url
                
        except Exception as e:
            logger.error(f"Error creating/uploading generated image for {product_name}: {e}")
        
        # Fallback to default
        return '/products/default.png'