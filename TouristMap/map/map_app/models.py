from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# Create your models here.
class City(models.Model):
    """Город"""
    name = models.CharField(max_length = 100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Tag(models.Model):
    """Нужен для блока 'Вам также может понравиться'"""
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Place(models.Model):
    """Место (достопримечательность)"""
    name = models.CharField(max_length = 100)
    description = models.TextField()
    category = models.ForeignKey('Category',on_delete=models.PROTECT)
    city = models.ForeignKey('City', on_delete=models.CASCADE, related_name='places')

    # геоданные
    location = models.PointField(srid=4326)
    address = models.CharField(max_length=500)

    # API
    external_id = models.CharField(max_length = 100, unique=True, null=True)
    rating = models.FloatField(default = 0)

    # прочая информация о месте
    working_hours = models.JSONField(null=True)
    website = models.URLField(null=True)

    # Связь для рекомендаций
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Возвращает URL-aдpec для доступа к определенному экземпляру книги.
        return reverse('book-detail', args=[str(self.id)])

class Category(models.Model):
    """Категория достопримечательности (музей, театр, памятник, парк и т.д)"""
    name = models.CharField(max_length = 100)
    slug = models.SlugField(unique=True, max_length = 100)
    icon_name = models.CharField(max_length = 100)

    def __str__(self):
        return self.name

class Favorite(models.Model):
    """Избранные места"""
    user = models.ForeignKey('auth.User',on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class PlaceImage(models.Model):
    """Галерея фото места"""
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='places/')
    is_main = models.BooleanField(default=False)

