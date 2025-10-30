from django.core.management.base import BaseCommand
from products.models import Brand

class Command(BaseCommand):
    help = 'Debug brand status in database'

    def handle(self, *args, **options):
        self.stdout.write("=== Brand Debug Information ===")
        
        total_brands = Brand.objects.count()
        self.stdout.write(f"Total brands: {total_brands}")
        
        if total_brands == 0:
            self.stdout.write(self.style.WARNING("No brands found in database!"))
            return
        
        # Check status distribution
        status_counts = {}
        for brand in Brand.objects.all():
            key = f"{brand.status}|{brand.is_publish}"
            status_counts[key] = status_counts.get(key, 0) + 1
        
        self.stdout.write("\nStatus distribution:")
        for key, count in status_counts.items():
            status, is_publish = key.split('|')
            self.stdout.write(f"  {status} + is_publish={is_publish}: {count}")
        
        # Check what the public query returns
        public_brands = Brand.objects.filter(status__in=['approved', 'published'], is_publish=True)
        self.stdout.write(f"\nBrands matching public filter: {public_brands.count()}")
        
        if public_brands.count() > 0:
            self.stdout.write("\nFirst 5 public brands:")
            for brand in public_brands[:5]:
                self.stdout.write(f"  - {brand.name} (status: {brand.status}, published: {brand.is_publish})")
        
        # Check field types and values
        sample_brand = Brand.objects.first()
        if sample_brand:
            self.stdout.write(f"\nSample brand field types:")
            self.stdout.write(f"  status: {type(sample_brand.status).__name__} = '{sample_brand.status}'")
            self.stdout.write(f"  is_publish: {type(sample_brand.is_publish).__name__} = {sample_brand.is_publish}")
        
        # Check if there are any filtering issues
        try:
            approved_count = Brand.objects.filter(status='approved', is_publish=True).count()
            published_count = Brand.objects.filter(status='published', is_publish=True).count()
            self.stdout.write(f"\nDirect filter counts:")
            self.stdout.write(f"  approved + is_publish=True: {approved_count}")
            self.stdout.write(f"  published + is_publish=True: {published_count}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error in filtering: {e}"))