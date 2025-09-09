import os
import json
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Brand
from accounts.models import upload_to_imagekit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed Brand data from brand.json with optimized ImageKit images'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing brands before seeding',
        )
        parser.add_argument(
            '--use-imagekit',
            action='store_true',
            help='Upload images to ImageKit (recommended)',
        )
        parser.add_argument(
            '--image-size',
            type=int,
            default=200,
            help='Image size in pixels (default: 200x200)',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='Image quality for optimization (default: 85)',
        )

    def handle(self, *args, **options):
        # Get or create admin user
        admin_user = self.get_admin_user()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('No admin user found. Please create one first.')
            )
            return

        # Clear existing brands if requested
        if options['clear']:
            Brand.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('✅ Cleared existing brands')
            )

        # Load brand data
        brand_data = self.load_brand_data()
        if not brand_data:
            return

        # Process brands
        success_count = 0
        error_count = 0
        
        self.stdout.write(f"🚀 Processing {len(brand_data)} brands...")
        
        for brand_info in brand_data:
            try:
                brand = self.create_brand(
                    brand_info, 
                    admin_user, 
                    options['use_imagekit'],
                    options['image_size'],
                    options['quality']
                )
                if brand:
                    success_count += 1
                    self.stdout.write(f"✅ Created: {brand.name}")
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating brand {brand_info.get('name', 'Unknown')}: {str(e)}")
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Brand seeding completed!\n"
                f"✅ Successfully created: {success_count} brands\n"
                f"❌ Errors: {error_count} brands\n"
                f"📊 Total brands in database: {Brand.objects.count()}"
            )
        )

    def get_admin_user(self):
        """Get or create admin user"""
        try:
            return User.objects.filter(is_superuser=True).first()
        except Exception as e:
            logger.error(f"Error getting admin user: {e}")
            return None

    def load_brand_data(self):
        """Load brand data from JSON file"""
        json_file_path = os.path.join('products', 'data', 'brand.json')
        
        if not os.path.exists(json_file_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Brand data file not found: {json_file_path}')
            )
            return None

        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Loaded {len(data)} brands from {json_file_path}')
                )
                return data
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error loading brand data: {str(e)}')
            )
            return None

    def create_optimized_brand_image(self, brand_name, size=200, quality=85):
        """Create an optimized brand image"""
        try:
            # Create a professional brand image
            image = Image.new('RGB', (size, size), color='#ffffff')
            draw = ImageDraw.Draw(image)
            
            # Add gradient background
            for y in range(size):
                # Create a subtle gradient from light blue to white
                color_value = int(240 + (15 * y / size))
                color = (color_value, color_value + 5, 255)
                draw.line([(0, y), (size, y)], fill=color)
            
            # Add brand initial in a circle
            initial = brand_name[0].upper()
            circle_size = size // 3
            circle_x = (size - circle_size) // 2
            circle_y = (size - circle_size) // 2
            
            # Draw circle background
            draw.ellipse(
                [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
                fill='#4f46e5',  # Professional blue
                outline='#3730a3',
                width=3
            )
            
            # Add brand initial
            try:
                # Try to use a good font
                font_size = circle_size // 2
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Get text size and center it
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
            
            # Add brand name at bottom
            try:
                name_font = ImageFont.truetype("arial.ttf", size // 15)
            except:
                name_font = ImageFont.load_default()
            
            # Truncate long names
            display_name = brand_name if len(brand_name) <= 15 else brand_name[:12] + "..."
            
            name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (size - name_width) // 2
            name_y = size - size // 8
            
            draw.text(
                (name_x, name_y),
                display_name,
                fill='#374151',  # Dark gray
                font=name_font
            )
            
            # Optimize and return as bytes
            output = BytesIO()
            image.save(output, format='PNG', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating image for {brand_name}: {e}")
            return None

    def create_brand(self, brand_info, admin_user, use_imagekit=True, image_size=200, quality=85):
        """Create a brand with optimized image"""
        brand_name = brand_info.get('name', '').strip()
        
        if not brand_name:
            logger.warning("Brand name is empty, skipping...")
            return None

        # Check if brand already exists
        if Brand.objects.filter(name=brand_name).exists():
            logger.info(f"Brand '{brand_name}' already exists, skipping...")
            return Brand.objects.get(name=brand_name)

        # Generate optimized image
        image_url = '/brand/default.png'  # Fallback
        
        if use_imagekit:
            try:
                # Create optimized image
                image_data = self.create_optimized_brand_image(
                    brand_name, 
                    size=image_size, 
                    quality=quality
                )
                
                if image_data:
                    # Upload to ImageKit with optimization
                    image_filename = f"brand_{brand_name.lower().replace(' ', '_').replace('&', 'and')}.png"
                    
                    uploaded_url = upload_to_imagekit(
                        image_data,
                        f"brands/{image_filename}",
                        {
                            'brand': brand_name,
                            'type': 'brand_logo',
                            'optimized': 'true',
                            'size': f"{image_size}x{image_size}"
                        }
                    )
                    
                    if uploaded_url:
                        # Add optimization parameters to ImageKit URL
                        if 'imagekit.io' in uploaded_url:
                            # Add ImageKit transformations for web optimization
                            optimization_params = f"tr=w-{image_size},h-{image_size},q-{quality},f-webp"
                            if '?' in uploaded_url:
                                image_url = f"{uploaded_url}&{optimization_params}"
                            else:
                                image_url = f"{uploaded_url}?{optimization_params}"
                        else:
                            image_url = uploaded_url
                        
                        logger.info(f"✅ Uploaded optimized image for {brand_name}")
                    else:
                        logger.warning(f"⚠️ ImageKit upload failed for {brand_name}, using default")
                else:
                    logger.warning(f"⚠️ Image generation failed for {brand_name}")
                    
            except Exception as e:
                logger.error(f"❌ ImageKit upload error for {brand_name}: {e}")

        # Create brand
        try:
            brand = Brand.objects.create(
                name=brand_name,
                image=image_url,
                created_by=admin_user
            )
            
            logger.info(f"✅ Created brand: {brand_name} with image: {image_url}")
            return brand
            
        except Exception as e:
            logger.error(f"❌ Error creating brand {brand_name}: {e}")
            return None
