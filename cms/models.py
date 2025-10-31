# cms/models.py
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Page(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    TEMPLATE_CHOICES = (
        ('default', 'Default Template'),
        ('full_width', 'Full Width'),
        ('sidebar_left', 'Sidebar Left'),
        ('sidebar_right', 'Sidebar Right'),
        ('medical', 'Medical Template'),
        ('pathology', 'Pathology Template'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    template = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default='default'
    )
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_pages'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_pages'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    show_in_nav = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = _('Page')
        verbose_name_plural = _('Pages')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('cms:page-detail', kwargs={'slug': self.slug})

    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError(_('A page cannot be its own parent.'))

        if self.parent and self.parent.status != 'published':
            raise ValidationError(_('Parent page must be published.'))

    def save(self, *args, **kwargs):
        if not self.seo_title:
            self.seo_title = self.title

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)


class Banner(models.Model):
    POSITION_CHOICES = (
        ('home_top', 'Homepage Top'),
        ('home_middle', 'Homepage Middle'),
        ('home_bottom', 'Homepage Bottom'),
        ('category_top', 'Category Top'),
        ('product_top', 'Product Top'),
    )

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='banners/')
    mobile_image = models.ImageField(
        upload_to='banners/mobile/',
        null=True,
        blank=True
    )
    link = models.URLField(max_length=500, blank=True)
    text = models.TextField(blank=True)
    button_text = models.CharField(max_length=50, blank=True)
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        default='home_top'
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'order']
        verbose_name = _('Banner')
        verbose_name_plural = _('Banners')

    def __str__(self):
        return self.title

    def is_active_now(self):
        now = timezone.now()
        if self.end_date and now > self.end_date:
            return False
        return self.is_active


class BlogPost(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    featured_image = models.ImageField(
        upload_to='blog/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blog_posts'
    )
    categories = models.ManyToManyField(
        'BlogCategory',
        related_name='blog_posts',
        blank=True
    )
    tags = models.ManyToManyField(
        'BlogTag',
        related_name='blog_posts',
        blank=True
    )
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at']
        verbose_name = _('Blog Post')
        verbose_name_plural = _('Blog Posts')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('cms:blog-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.seo_title:
            self.seo_title = self.title

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)


class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Blog Category')
        verbose_name_plural = _('Blog Categories')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cms:blog-category', kwargs={'slug': self.slug})


class BlogTag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Blog Tag')
        verbose_name_plural = _('Blog Tags')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cms:blog-tag', kwargs={'slug': self.slug})


class FAQ(models.Model):
    CATEGORY_CHOICES = (
        ('general', 'General'),
        ('ordering', 'Ordering'),
        ('payments', 'Payments'),
        ('shipping', 'Shipping'),
        ('returns', 'Returns'),
        ('products', 'Products'),
        ('pathology', 'Pathology Products'),
        ('medical', 'Medical Products'),
    )

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    author_name = models.CharField(max_length=100)
    author_title = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    image = models.ImageField(
        upload_to='testimonials/',
        null=True,
        blank=True
    )
    rating = models.PositiveIntegerField(
        default=5,
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = _('Testimonial')
        verbose_name_plural = _('Testimonials')

    def __str__(self):
        return f"Testimonial by {self.author_name}"


@receiver(pre_save, sender=Page)
@receiver(pre_save, sender=BlogPost)
@receiver(pre_save, sender=BlogCategory)
@receiver(pre_save, sender=BlogTag)
def generate_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        base_slug = slugify(instance.title if hasattr(instance, 'title') else instance.name)
        instance.slug = base_slug
        counter = 1
        while sender.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{base_slug}-{counter}"
            counter += 1
            
class CarouselBanner(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='carousel_banners/')
    link = models.URLField(max_length=500, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = _('Carousel Banner')
        verbose_name_plural = _('Carousel Banners')

    def __str__(self):
        return self.title