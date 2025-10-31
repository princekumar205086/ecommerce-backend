#!/bin/bash
# Quick fix script for production brand issue

echo "=== Production Brand Fix Script ==="
echo "This will approve and publish all pending brands in production"
echo ""

# Check current status
echo "Current status:"
python manage.py debug_brands

echo ""
echo "Fixing brands..."

# First, try the safe approach - dry run
echo "1. Dry run check:"
python manage.py fix_brand_status --approve-pending --dry-run

echo ""
read -p "Do you want to proceed with approving and publishing all pending brands? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying fix..."
    python manage.py fix_brand_status --approve-pending
    
    echo ""
    echo "Verifying fix..."
    python manage.py debug_brands
    
    echo ""
    echo "Testing API endpoint..."
    curl -s "https://backend.okpuja.in/api/public/products/brands/" | python -m json.tool | head -20
else
    echo "Operation cancelled."
fi