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
    help = 'Seed Brand data from brand.json with optimized ImageKit images (Production Ready)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing brands before seeding',
        )
        parser.add_argument(
            '--use-imagekit',
            action='store_true',
            help='Upload images to ImageKit (recommended for production)',
        )
        parser.add_argument(
            '--image-size',
            type=int,
            default=150,  # Smaller optimized size
            help='Image size in pixels (default: 150x150 for optimization)',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=80,  # Lower quality for smaller file size
            help='Image quality for optimization (default: 80)',
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

        # Create media directory if using static images
        if not options['use_imagekit']:
            self.create_media_directory()

        # Process brands
        success_count = 0
        error_count = 0
        
        self.stdout.write(f"🚀 Processing {len(brand_data)} brands...")
        
        for i, brand_info in enumerate(brand_data, 1):
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
                    self.stdout.write(f"✅ [{i}/{len(brand_data)}] Created: {brand.name}")
                else:
                    error_count += 1
                    self.stdout.write(f"⚠️ [{i}/{len(brand_data)}] Skipped: {brand_info.get('name', 'Unknown')}")
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ [{i}/{len(brand_data)}] Error creating brand {brand_info.get('name', 'Unknown')}: {str(e)}")
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

    def create_media_directory(self):
        """Create media/brand directory for static images"""
        try:
            media_dir = os.path.join('media', 'brand')
            os.makedirs(media_dir, exist_ok=True)
            self.stdout.write(f"✅ Created media directory: {media_dir}")
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️ Could not create media directory: {e}")
            )

    def create_optimized_brand_image(self, brand_name, size=150, quality=80):
        """Create a highly optimized brand image with smaller file size"""
        try:
            # Create a clean, professional brand image
            image = Image.new('RGB', (size, size), color='#f8fafc')  # Light gray background
            draw = ImageDraw.Draw(image)
            
            # Add subtle gradient background
            for y in range(size):
                # Very subtle gradient
                color_value = int(248 + (7 * y / size))
                color = (color_value, color_value, color_value + 5)
                draw.line([(0, y), (size, y)], fill=color)
            
            # Brand initial in a modern circle
            initial = brand_name[0].upper()
            circle_size = size // 2.5  # Smaller circle for optimization
            circle_x = (size - circle_size) // 2
            circle_y = (size - circle_size) // 2
            
            # Draw modern circle with shadow effect
            # Shadow
            shadow_offset = 2
            draw.ellipse(
                [circle_x + shadow_offset, circle_y + shadow_offset, 
                 circle_x + circle_size + shadow_offset, circle_y + circle_size + shadow_offset],
                fill='#e2e8f0'  # Light shadow
            )
            
            # Main circle
            draw.ellipse(
                [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
                fill='#3b82f6',  # Modern blue
                outline='#1d4ed8',
                width=2
            )
            
            # Add brand initial
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
            
            # Add brand name at bottom (smaller font)
            try:
                name_font_size = max(8, size // 20)  # Smaller font
                name_font = ImageFont.truetype("arial.ttf", name_font_size)
            except:
                name_font = ImageFont.load_default()
            
            # Truncate long names for optimization
            display_name = brand_name if len(brand_name) <= 12 else brand_name[:9] + "..."
            
            name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (size - name_width) // 2
            name_y = size - size // 6
            
            draw.text(
                (name_x, name_y),
                display_name,
                fill='#475569',  # Gray text
                font=name_font
            )
            
            # Optimize for web with aggressive compression
            output = BytesIO()
            
            # Convert to P mode (palette) for smaller PNG files
            image = image.convert('P', palette=Image.ADAPTIVE, colors=64)
            image.save(output, format='PNG', optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating optimized image for {brand_name}: {e}")
            return None

    def save_static_image(self, brand_name, image_data):
        """Save image to media/brand directory"""
        try:
            filename = f"{brand_name.lower().replace(' ', '_').replace('&', 'and')}.png"
            filepath = os.path.join('media', 'brand', filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return f"/brand/{filename}"
        except Exception as e:
            logger.error(f"Error saving static image for {brand_name}: {e}")
            return None

    def create_brand(self, brand_info, admin_user, use_imagekit=True, image_size=150, quality=80):
        """Create a brand with highly optimized image"""
        brand_name = brand_info.get('name', '').strip()
        
        if not brand_name:
            logger.warning("Brand name is empty, skipping...")
            return None

        # Check if brand already exists
        if Brand.objects.filter(name=brand_name).exists():
            logger.info(f"Brand '{brand_name}' already exists, skipping...")
            return Brand.objects.get(name=brand_name)

        # Generate highly optimized image
        image_url = '/brand/default.png'  # Fallback
        
        try:
            # Create optimized image
            image_data = self.create_optimized_brand_image(
                brand_name, 
                size=image_size, 
                quality=quality
            )
            
            if image_data:
                if use_imagekit:
                    # Upload to ImageKit with aggressive optimization
                    image_filename = f"brand_{brand_name.lower().replace(' ', '_').replace('&', 'and')}.png"
                    
                    uploaded_url = upload_to_imagekit(
                        image_data,
                        f"brands/{image_filename}",
                        {
                            'brand': brand_name,
                            'type': 'brand_logo',
                            'optimized': 'true',
                            'size': f"{image_size}x{image_size}",
                            'quality': str(quality)
                        }
                    )
                    
                    if uploaded_url:
                        # Add aggressive ImageKit optimizations
                        if 'imagekit.io' in uploaded_url:
                            # Multiple optimization parameters
                            optimization_params = (
                                f"tr=w-{image_size},h-{image_size},"
                                f"q-{quality},f-webp,pr-true,lo-true"
                            )
                            if '?' in uploaded_url:
                                image_url = f"{uploaded_url}&{optimization_params}"
                            else:
                                image_url = f"{uploaded_url}?{optimization_params}"
                        else:
                            image_url = uploaded_url
                        
                        logger.info(f"✅ Uploaded optimized image for {brand_name} (Size: {len(image_data)} bytes)")
                    else:
                        logger.warning(f"⚠️ ImageKit upload failed for {brand_name}, trying static save")
                        # Fallback to static image
                        static_url = self.save_static_image(brand_name, image_data)
                        if static_url:
                            image_url = static_url
                else:
                    # Save as static image
                    static_url = self.save_static_image(brand_name, image_data)
                    if static_url:
                        image_url = static_url
                        logger.info(f"✅ Saved static image for {brand_name}")
            else:
                logger.warning(f"⚠️ Image generation failed for {brand_name}")
                    
        except Exception as e:
            logger.error(f"❌ Image processing error for {brand_name}: {e}")

        # Create brand
        try:
            brand = Brand.objects.create(
                name=brand_name,
                image=image_url,
                created_by=admin_user
            )
            
            logger.info(f"✅ Created brand: {brand_name} with optimized image: {image_url}")
            return brand
            
        except Exception as e:
            logger.error(f"❌ Error creating brand {brand_name}: {e}")
            return None
