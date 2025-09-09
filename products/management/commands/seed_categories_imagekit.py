import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from products.models import ProductCategory
from accounts.models import upload_to_imagekit

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed ProductCategory data from category.json file with ImageKit integration'

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
            '--upload-images',
            action='store_true',
            help='Upload local images to ImageKit and use URLs (requires existing images in media/categories/)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        admin_email = options['admin_email']
        clear_existing = options['clear']
        upload_images = options['upload_images']

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
            category = self._create_category(category_data, admin_user, None, upload_images)
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

            category = self._create_category(category_data, admin_user, parent_category, upload_images)
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

    def _create_category(self, category_data, admin_user, parent_category=None, upload_images=False):
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
            icon_url = self._process_image_path(
                category_data.get('icon_file', ''), 
                parent_category is None, 
                upload_images
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

    def _process_image_path(self, icon_file, is_parent_category, upload_images):
        """Process the image path - upload to ImageKit if requested, otherwise use static paths"""
        
        # For child categories, always use default
        if not is_parent_category:
            if upload_images:
                return self._upload_default_image()
            else:
                return '/categories/default.png'
        
        # For parent categories, process the icon_file
        if not icon_file:
            if upload_images:
                return self._upload_default_image()
            else:
                return '/categories/default.png'

        # Extract filename from icon_file path
        filename = self._extract_filename(icon_file)
        
        if upload_images:
            return self._upload_category_image(filename)
        else:
            # Return path that matches your existing ImageKit structure
            return f'/categories/{filename}'

    def _extract_filename(self, icon_file):
        """Extract filename from various path formats"""
        if not icon_file:
            return 'default.png'
            
        # Clean the path - remove leading slash if present
        clean_path = icon_file.lstrip('/')
        
        # Extract just the filename
        if '/' in clean_path:
            filename = clean_path.split('/')[-1]
        else:
            filename = clean_path
            
        return filename

    def _upload_category_image(self, filename):
        """Upload a category image to ImageKit"""
        try:
            # Path to the local image file
            local_image_path = os.path.join(settings.MEDIA_ROOT, 'categories', filename)
            
            if not os.path.exists(local_image_path):
                self.stdout.write(
                    self.style.WARNING(f'Local image not found: {local_image_path}, using default')
                )
                return self._upload_default_image()
            
            # Read the image file
            with open(local_image_path, 'rb') as f:
                file_bytes = f.read()
            
            # Upload to ImageKit
            image_url = upload_to_imagekit(file_bytes, filename, folder="categories")
            
            if image_url:
                self.stdout.write(f'✓ Uploaded {filename} to ImageKit')
                return image_url
            else:
                self.stdout.write(
                    self.style.WARNING(f'Failed to upload {filename}, using default')
                )
                return self._upload_default_image()
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error uploading {filename}: {str(e)}, using default')
            )
            return self._upload_default_image()

    def _upload_default_image(self):
        """Upload the default category image to ImageKit"""
        try:
            default_path = os.path.join(settings.MEDIA_ROOT, 'categories', 'default.png')
            
            if not os.path.exists(default_path):
                self.stdout.write(
                    self.style.WARNING(f'Default image not found: {default_path}')
                )
                return '/categories/default.png'
            
            # Read the default image file
            with open(default_path, 'rb') as f:
                file_bytes = f.read()
            
            # Upload to ImageKit
            image_url = upload_to_imagekit(file_bytes, 'default.png', folder="categories")
            
            if image_url:
                return image_url
            else:
                return '/categories/default.png'
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error uploading default image: {str(e)}')
            )
            return '/categories/default.png'
