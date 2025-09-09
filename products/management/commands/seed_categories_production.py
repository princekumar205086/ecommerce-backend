import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from products.models import ProductCategory
from accounts.models import upload_to_imagekit
from PIL import Image
from io import BytesIO

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed ProductCategory data for production server with generated images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='products/data/category.json',
            help='Path to the category JSON file (default: products/data/category.json)'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@example.com',
            help='Admin email to assign as created_by (default: admin@example.com)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before seeding'
        )
        parser.add_argument(
            '--use-imagekit',
            action='store_true',
            help='Upload generated images to ImageKit (requires ImageKit credentials)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        admin_email = options['admin_email']
        clear_existing = options['clear']
        use_imagekit = options['use_imagekit']

        # Get the admin user
        try:
            admin_user = User.objects.get(email=admin_email)
            self.stdout.write(
                self.style.SUCCESS(f'Found admin user: {admin_user.email}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Admin user with email {admin_email} not found. Please create an admin user first.')
            )
            return

        # Clear existing categories if requested
        if clear_existing:
            self.stdout.write('Clearing existing categories...')
            ProductCategory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing categories cleared.'))

        # Load data from JSON file
        json_file_path = os.path.join(settings.BASE_DIR, file_path)
        
        if not os.path.exists(json_file_path):
            self.stdout.write(
                self.style.ERROR(f'Category JSON file not found at: {json_file_path}')
            )
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading JSON file: {str(e)}')
            )
            return

        self.stdout.write(f'Found {len(categories_data)} categories to process...')

        if use_imagekit:
            self.stdout.write('ImageKit mode: Will generate and upload images to ImageKit')
        else:
            self.stdout.write('Static mode: Will use static image paths')

        # Track created categories to handle parent relationships
        created_categories = {}
        parent_categories = []
        child_categories = []

        # Separate parent and child categories
        for category_data in categories_data:
            if category_data.get('parent') is None:
                parent_categories.append(category_data)
            else:
                child_categories.append(category_data)

        # Create parent categories first
        self.stdout.write('Creating parent categories...')
        for category_data in parent_categories:
            category = self._create_category(category_data, admin_user, None, use_imagekit)
            if category:
                created_categories[category_data['id']] = category
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created parent category: {category.name}')
                )

        # Create child categories
        self.stdout.write('Creating child categories...')
        for category_data in child_categories:
            parent_id = category_data.get('parent')
            parent_category = created_categories.get(parent_id)
            
            if not parent_category:
                self.stdout.write(
                    self.style.WARNING(f'Parent category with ID {parent_id} not found for {category_data["name"]}')
                )
                continue

            category = self._create_category(category_data, admin_user, parent_category, use_imagekit)
            if category:
                created_categories[category_data['id']] = category
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created child category: {category.name} (parent: {parent_category.name})')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(created_categories)} categories!')
        )

        # Summary
        total_parent = len(parent_categories)
        total_child = len(child_categories)
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'- Parent categories: {total_parent}')
        self.stdout.write(f'- Child categories: {total_child}')
        self.stdout.write(f'- Total categories: {len(created_categories)}')
        
        if use_imagekit:
            self.stdout.write(f'- Images uploaded to ImageKit')
        else:
            self.stdout.write(f'- Using static image paths')

    def _create_category(self, category_data, admin_user, parent_category=None, use_imagekit=False):
        """Create a single category from the data"""
        try:
            # Check if category already exists
            existing_category = ProductCategory.objects.filter(
                name=category_data['name']
            ).first()
            
            if existing_category:
                self.stdout.write(
                    self.style.WARNING(f'Category "{category_data["name"]}" already exists, skipping...')
                )
                return existing_category

            # Process icon/image path
            icon_url = self._get_image_url(
                category_data.get('icon_file', ''), 
                category_data['name'],
                parent_category is None, 
                use_imagekit
            )

            # Create the category
            category = ProductCategory.objects.create(
                name=category_data['name'],
                icon=icon_url,
                parent=parent_category,
                created_by=admin_user,
                is_publish=category_data.get('is_publish', True),
                status=category_data.get('status', 'pending')
            )

            return category

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating category "{category_data["name"]}": {str(e)}')
            )
            return None

    def _get_image_url(self, icon_file, category_name, is_parent_category, use_imagekit):
        """Get image URL - either generate and upload to ImageKit or use static path"""
        
        if use_imagekit:
            # Generate and upload image to ImageKit
            return self._generate_and_upload_image(category_name, is_parent_category)
        else:
            # Use static paths that will be handled by your frontend/static serving
            filename = self._extract_filename(icon_file)
            if is_parent_category and filename != 'default.png':
                # For parent categories, try to use specific filename from JSON
                return f'/media/categories/{filename}'
            else:
                # For child categories or when no specific image, use default
                return '/media/categories/default.png'

    def _extract_filename(self, icon_file):
        """Extract filename from icon_file path"""
        if not icon_file:
            return 'default.png'
            
        # Clean the path and extract filename
        clean_path = icon_file.lstrip('/')
        if '/' in clean_path:
            filename = clean_path.split('/')[-1]
        else:
            filename = clean_path
            
        return filename

    def _generate_and_upload_image(self, category_name, is_parent_category):
        """Generate a simple image and upload to ImageKit"""
        try:
            # Create a simple colored image based on category
            colors = {
                'Medicines': '#4CAF50',           # Green
                'Doctor Equipment': '#2196F3',   # Blue  
                'Pathology': '#FF9800',          # Orange
                'Healthcare': '#9C27B0',         # Purple
                'Personal Care': '#E91E63',      # Pink
                'Surgical': '#F44336',           # Red
                'Diagnostics': '#00BCD4',        # Cyan
            }
            
            # Choose color based on category name or parent category
            color = '#757575'  # Default gray
            for key, cat_color in colors.items():
                if key.lower() in category_name.lower():
                    color = cat_color
                    break
            
            # Create image
            size = (200, 200) if is_parent_category else (150, 150)
            img = Image.new('RGB', size, color=color)
            
            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            
            # Generate filename
            safe_name = "".join(c for c in category_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            filename = f"{safe_name}.png"
            
            # Upload to ImageKit
            image_url = upload_to_imagekit(img_bytes, filename, folder="categories")
            
            if image_url:
                self.stdout.write(f'✓ Generated and uploaded image: {filename}')
                return image_url
            else:
                self.stdout.write(
                    self.style.WARNING(f'Failed to upload generated image for {category_name}')
                )
                return '/media/categories/default.png'
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error generating image for {category_name}: {str(e)}')
            )
            return '/media/categories/default.png'
