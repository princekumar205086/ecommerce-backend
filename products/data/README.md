# Category Seeder Documentation

This directory contains tools to seed ProductCategory data from the `category.json` file into your Django database.

## Files

- `seed_categories.py` - Django management command
- `../seed_categories_simple.py` - Standalone Python script
- `category.json` - Source data file with category information

## Usage

### Method 1: Django Management Command (Recommended)

```bash
# Basic usage
python manage.py seed_categories

# With custom options
python manage.py seed_categories --admin-email admin@yoursite.com --clear

# Custom JSON file path
python manage.py seed_categories --file products/data/custom_categories.json
```

**Options:**
- `--file`: Path to JSON file (default: `products/data/category.json`)
- `--admin-email`: Admin email for created_by field (default: `admin@medixmall.com`)
- `--clear`: Clear existing categories before seeding

### Method 2: Standalone Script

```bash
# From project root directory
python seed_categories_simple.py
```

## Image Path Configuration

The seeder automatically configures image paths for the `media/categories/` directory:

### Parent Categories
- Use their specified images from the JSON file
- Paths are mapped to `/media/categories/[filename]`
- Example: `/categories/medicine.png` → `/media/categories/medicine.png`

### Child Categories (Subcategories)
- Use `default.png` placeholder image
- You can manually update these later with specific images
- This allows you to focus on parent category images first

### Image Path Mapping Rules

1. **Direct categories path**: `/categories/image.png` → `/media/categories/image.png`
2. **Images/categories path**: `/images/categories/default.png` → `/media/categories/default.png`
3. **Other paths**: Extract filename and place in `/media/categories/`
4. **Missing paths**: Use appropriate default image

## Category Structure

The seeder handles hierarchical categories:

1. **First Pass**: Creates all parent categories (where `parent` is `null`)
2. **Second Pass**: Creates child categories with proper parent relationships

## Data Format

The `category.json` file should follow this structure:

```json
[
  {
    "id": 1,
    "name": "Category Name",
    "parent": null,
    "status": "active",
    "is_publish": true,
    "icon": null,
    "icon_file": "/categories/image.png"
  }
]
```

### Fields Mapping

- `id`: Used for parent-child relationships (not saved as DB ID)
- `name`: Category name (must be unique)
- `parent`: ID of parent category (null for top-level)
- `status`: Category status (pending, active, etc.)
- `is_publish`: Whether category is published
- `icon_file`: Image file path (processed automatically)

## Prerequisites

1. **Admin User**: Must exist in database before running seeder
   ```bash
   python manage.py createsuperuser
   ```

2. **Media Directory**: Ensure `media/categories/` directory exists with images

3. **Database**: Run migrations if needed
   ```bash
   python manage.py makemigrations products
   python manage.py migrate
   ```

## Current Category Structure

Based on `category.json`, this seeder creates:

### Parent Categories (7):
1. **Medicines** - `/media/categories/medicine.png`
2. **Doctor Equipment** - `/media/categories/medical equipment.png`
3. **Pathology & Laboratory** - `/media/categories/pathology.png`
4. **Healthcare & Wellness** - `/media/categories/healthcare.png`
5. **Personal Care & Hygiene** - `/media/categories/personal care.png`
6. **Surgical & Medical Supplies** - `/media/categories/surgical.png`
7. **Diagnostics & Monitoring** - `/media/categories/diagnostics.png`

### Child Categories (73):
- All use `/media/categories/default.png` initially
- Update manually with specific images later

## Troubleshooting

### Common Issues

1. **Admin user not found**
   ```bash
   python manage.py createsuperuser
   # or update --admin-email parameter
   ```

2. **JSON file not found**
   - Check file path: `products/data/category.json`
   - Use `--file` parameter for custom path

3. **Image not displaying**
   - Ensure images exist in `media/categories/`
   - Check `MEDIA_URL` and `MEDIA_ROOT` in settings
   - Verify web server serves media files

4. **Categories already exist**
   - Use `--clear` flag to remove existing categories
   - Or manually delete via Django admin

### Verification

After seeding, verify the results:

```python
# In Django shell
python manage.py shell

>>> from products.models import ProductCategory
>>> ProductCategory.objects.count()  # Should show total count
>>> ProductCategory.objects.filter(parent=None).count()  # Parent categories
>>> ProductCategory.objects.exclude(parent=None).count()  # Child categories
```

## Next Steps

1. **Run the seeder** using your preferred method
2. **Verify categories** in Django admin or shell
3. **Update child category images** manually as needed
4. **Set appropriate permissions** for category management
5. **Test frontend display** of categories with images

## Support

For issues or questions:
1. Check Django logs for detailed error messages
2. Verify database connection and migrations
3. Ensure all prerequisites are met
4. Test with a small subset of data first
