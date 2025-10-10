import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ecommerce.settings')
django.setup()
from django.contrib.auth import get_user_model
User=get_user_model()
email='duplicate@example.com'
u=User.objects.filter(email=email).first()
if not u:
    u=User.objects.create_user(email=email,password='Dup@12345',full_name='Dup User',contact='9999999999')
    u.email_verified=True
    u.save()
    print('Created duplicate user with contact 9999999999')
else:
    print('Duplicate user exists', u.contact)
print('Primary user contact:', User.objects.filter(email='user@example.com').first().contact)
