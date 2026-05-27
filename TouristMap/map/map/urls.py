"""
URL configuration for map project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from map_app import views
from django.conf import settings
from django.conf.urls.static import static
from map_app.views import index, api_login, api_toggle_favorite

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('map_app.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/favorites/', api_toggle_favorite, name='favorite-add'),
    path('api/verify-email/', views.api_verify_email, name='api_verify_email'),
]
