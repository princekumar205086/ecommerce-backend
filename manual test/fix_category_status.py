#!/usr/bin/env python3
"""
Fix category.json to use published status instead of active
"""

import json
import re

def main():
    # Read the category.json file
    with open('products/data/category.json', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace all 'active' with 'published' in status fields
    updated_content = content.replace('"status": "active"', '"status": "published"')

    # Write back to file
    with open('products/data/category.json', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print('✅ Updated category.json: changed all status from active to published')

    # Verify the change
    with open('products/data/category.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    active_count = sum(1 for item in data if item.get('status') == 'active')
    published_count = sum(1 for item in data if item.get('status') == 'published')

    print(f'Verification: {published_count} published, {active_count} active')

if __name__ == "__main__":
    main()
