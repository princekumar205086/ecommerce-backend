#!/usr/bin/env python3
"""
Create default category images for production server
This script creates the media/categories directory and generates default images
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_media_structure():
    """Create the media directory structure on server"""
    print("📁 Creating media directory structure...")
    
    base_dir = Path('/srv/backend')
    media_dir = base_dir / 'media'
    categories_dir = media_dir / 'categories'
    
    # Create directories
    categories_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created: {categories_dir}")
    return categories_dir

def create_default_image(categories_dir):
    """Create a default.png image"""
    print("🎨 Creating default.png...")
    
    # Create a simple default image
    img = Image.new('RGB', (200, 200), color='#E0E0E0')
    draw = ImageDraw.Draw(img)
    
    # Try to use a simple font
    try:
        # Try to find a font (may not work on all servers)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Add text
    text = "Default\nCategory"
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (200 - text_width) // 2
    y = (200 - text_height) // 2
    
    draw.text((x, y), text, fill='#757575', font=font, align='center')
    
    # Save
    default_path = categories_dir / 'default.png'
    img.save(default_path)
    
    print(f"✓ Created: {default_path}")

def create_category_images(categories_dir):
    """Create specific category images"""
    print("🎨 Creating category images...")
    
    categories = {
        'medicine.png': ('#4CAF50', 'Medicine'),
        'medical equipment.png': ('#2196F3', 'Medical\nEquipment'),
        'pathology.png': ('#FF9800', 'Pathology'),
        'healthcare.png': ('#9C27B0', 'Healthcare'),
        'personal care.png': ('#E91E63', 'Personal\nCare'),
        'surgical.png': ('#F44336', 'Surgical'),
        'diagnostics.png': ('#00BCD4', 'Diagnostics'),
    }
    
    for filename, (color, text) in categories.items():
        img = Image.new('RGB', (200, 200), color=color)
        draw = ImageDraw.Draw(img)
        
        # Try to use a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            except:
                font = ImageFont.load_default()
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (200 - text_width) // 2
        y = (200 - text_height) // 2
        
        # Draw white text with black outline for better visibility
        for adj in range(-1, 2):
            for adj2 in range(-1, 2):
                if adj != 0 or adj2 != 0:
                    draw.text((x+adj, y+adj2), text, fill='black', font=font, align='center')
        
        draw.text((x, y), text, fill='white', font=font, align='center')
        
        # Save
        img_path = categories_dir / filename
        img.save(img_path)
        
        print(f"✓ Created: {img_path}")

def set_permissions(categories_dir):
    """Set proper permissions for web server access"""
    print("🔐 Setting permissions...")
    
    try:
        # Make sure the web server can read these files
        os.chmod(categories_dir, 0o755)
        
        for img_file in categories_dir.glob('*.png'):
            os.chmod(img_file, 0o644)
        
        print("✓ Permissions set")
    except Exception as e:
        print(f"⚠️  Permission setting failed: {e}")
        print("   You may need to run: chmod 755 /srv/backend/media/categories/")
        print("   And: chmod 644 /srv/backend/media/categories/*.png")

def main():
    print("🖼️  Category Images Setup for Production Server")
    print("=" * 60)
    
    try:
        # Create directory structure
        categories_dir = create_media_structure()
        
        # Create default image
        create_default_image(categories_dir)
        
        # Create category-specific images
        create_category_images(categories_dir)
        
        # Set permissions
        set_permissions(categories_dir)
        
        print("\n🎉 SUCCESS!")
        print("✓ All category images created successfully")
        print("✓ Ready to run category seeder")
        
        print(f"\n📋 Next steps:")
        print(f"1. Run: python manage.py seed_categories_production")
        print(f"2. Or: python manage.py seed_categories_production --use-imagekit")
        print(f"3. Verify: python test_categories.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you're running this on the production server as a user with write access to /srv/backend/")

if __name__ == '__main__':
    main()
