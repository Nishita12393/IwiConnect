import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwi_web_app.settings')
    django.setup()
    from core.models import CustomUser

    email = 'admin@example.com'
    password = 'admin1234'
    if not CustomUser.objects.filter(email=email).exists():
        admin = CustomUser.objects.create_superuser(email=email, password=password, full_name='Admin User')
        admin.state = 'VERIFIED'
        admin.save()
        print('Admin user created.')
    else:
        print('Admin user already exists.')

if __name__ == '__main__':
    main() 