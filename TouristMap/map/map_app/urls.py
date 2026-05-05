from django.urls import path
from .views import api_toggle_favorite, index, api_login 

urlpatterns = [
    path('', index, name='index'),
    path('api/login/', api_login, name='api_login'),
    path('api/favorites/', api_toggle_favorite, name='favorite-add'),
]