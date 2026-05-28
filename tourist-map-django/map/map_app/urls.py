from django.urls import path
from .views import api_toggle_favorite, index, api_login, get_wikidata_places

urlpatterns = [
    path('', index, name='index'),
    path('api/login/', api_login, name='api_login'),
    path('api/favorites/', api_toggle_favorite, name='favorite-add'),
    path('api/wikidata-places/', get_wikidata_places, name='wikidata-places'),
]