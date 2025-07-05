"""
URL configuration for iwi_web_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views import register, get_hapus, get_hapus_htmx, login_view, dashboard, logout_view, home, profile, password_reset_request, password_reset_confirm
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', password_reset_request, name='password_reset_request'),
    path('reset-password/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    path('', home, name='home'),
    path('consultations/', include('consultation.urls')),
    path('api/get_hapus/', get_hapus, name='get_hapus'),
    path('api/get_hapus_htmx/', get_hapus_htmx, name='get_hapus_htmx'),
    path('usermgmt/', include('usermgmt.urls')),
    path('iwimgmt/', include('iwimgmt.urls')),
    path('dashboard/', dashboard, name='dashboard'),
    path('notices/', include('notice.urls')),
    path('events/', include('events.urls')),
    path('profile/', profile, name='profile'),
    path('hapumgmt/', include('hapumgmt.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
