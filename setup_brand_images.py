#!/usr/bin/env python3
"""
Setup Brand Images Script
Creates optimized brand images in media/brand directory for production server
"""

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def create_optimized_brand_image(brand_name, size=150):
    """Create a highly optimized brand image"""
    try:
        # Create clean professional image
        image = Image.new('RGB', (size, size), color='#f8fafc')
        draw = ImageDraw.Draw(image)
        
        # Subtle gradient
        for y in range(size):
            color_value = int(248 + (7 * y / size))
            color = (color_value, color_value, color_value + 5)
            draw.line([(0, y), (size, y)], fill=color)
        
        # Brand initial in circle
        initial = brand_name[0].upper()
        circle_size = size // 2.5
        circle_x = (size - circle_size) // 2
        circle_y = (size - circle_size) // 2
        
        # Shadow effect
        shadow_offset = 2
        draw.ellipse(
            [circle_x + shadow_offset, circle_y + shadow_offset, 
             circle_x + circle_size + shadow_offset, circle_y + circle_size + shadow_offset],
            fill='#e2e8f0'
        )
        
        # Main circle
        draw.ellipse(
            [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
            fill='#3b82f6',
            outline='#1d4ed8',
            width=2
        )
        
        # Add initial
        try:
            font_size = circle_size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), initial, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = circle_x + (circle_size - text_width) // 2
        text_y = circle_y + (circle_size - text_height) // 2
        
        draw.text((text_x, text_y), initial, fill='white', font=font)
        
        # Add brand name
        try:
            name_font_size = max(8, size // 20)
            name_font = ImageFont.truetype("arial.ttf", name_font_size)
        except:
            name_font = ImageFont.load_default()
        
        display_name = brand_name if len(brand_name) <= 12 else brand_name[:9] + "..."
        
        name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (size - name_width) // 2
        name_y = size - size // 6
        
        draw.text((name_x, name_y), display_name, fill='#475569', font=name_font)
        
        # Optimize for web
        output = BytesIO()
        image = image.convert('P', palette=Image.ADAPTIVE, colors=64)
        image.save(output, format='PNG', optimize=True)
        return output.getvalue()
        
    except Exception as e:
        print(f"❌ Error creating image for {brand_name}: {e}")
        return None

def create_default_image(size=150):
    """Create a default brand image"""
    try:
        image = Image.new('RGB', (size, size), color='#f1f5f9')
        draw = ImageDraw.Draw(image)
        
        # Simple design for default
        circle_size = size // 2
        circle_x = (size - circle_size) // 2
        circle_y = (size - circle_size) // 2
        
        draw.ellipse(
            [circle_x, circle_y, circle_x + circle_size, circle_y + circle_size],
            fill='#94a3b8',
            outline='#64748b',
            width=2
        )
        
        # Question mark for default
        try:
            font_size = circle_size // 2
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), "?", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = circle_x + (circle_size - text_width) // 2
        text_y = circle_y + (circle_size - text_height) // 2
        
        draw.text((text_x, text_y), "?", fill='white', font=font)
        
        output = BytesIO()
        image = image.convert('P', palette=Image.ADAPTIVE, colors=32)
        image.save(output, format='PNG', optimize=True)
        return output.getvalue()
        
    except Exception as e:
        print(f"❌ Error creating default image: {e}")
        return None

def main():
    print("🚀 Setting up optimized brand images...")
    
    # Create media/brand directory
    try:
        os.makedirs('media/brand', exist_ok=True)
        print("✅ Created media/brand directory")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        sys.exit(1)
    
    # Create default image
    try:
        default_image_data = create_default_image()
        if default_image_data:
            with open('media/brand/default.png', 'wb') as f:
                f.write(default_image_data)
            print("✅ Created default.png")
        else:
            print("❌ Failed to create default image")
    except Exception as e:
        print(f"❌ Error saving default image: {e}")
    
    # Load brand data and create images
    try:
        with open('products/data/brand.json', 'r', encoding='utf-8') as f:
            brands = json.load(f)
        
        print(f"📦 Processing {len(brands)} brands...")
        
        success_count = 0
        for i, brand_info in enumerate(brands, 1):
            brand_name = brand_info.get('name', '').strip()
            if not brand_name:
                continue
            
            try:
                # Create optimized image
                image_data = create_optimized_brand_image(brand_name)
                if image_data:
                    filename = f"{brand_name.lower().replace(' ', '_').replace('&', 'and')}.png"
                    filepath = f"media/brand/{filename}"
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    success_count += 1
                    print(f"✅ [{i}/{len(brands)}] Created: {filename} ({len(image_data)} bytes)")
                else:
                    print(f"⚠️ [{i}/{len(brands)}] Failed to create image for: {brand_name}")
            
            except Exception as e:
                print(f"❌ [{i}/{len(brands)}] Error processing {brand_name}: {e}")
        
        print(f"\n🎉 Setup completed!")
        print(f"✅ Successfully created {success_count} brand images")
        print(f"📁 Images saved in: media/brand/")
        print(f"📊 Total file size optimized for web delivery")
        
        # Set proper permissions
        try:
            os.chmod('media/brand', 0o755)
            for filename in os.listdir('media/brand'):
                os.chmod(f"media/brand/{filename}", 0o644)
            print("✅ Set proper file permissions")
        except Exception as e:
            print(f"⚠️ Could not set permissions: {e}")
        
    except FileNotFoundError:
        print("❌ brand.json file not found in products/data/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error processing brands: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
