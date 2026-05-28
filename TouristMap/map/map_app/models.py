from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

class Place(models.Model):
    """
    Локальное расширение для объектов из Wikidata.
    Используется для хранения уникальных данных нашего сервиса (например, рейтинга).
    """
    wikidata_id = models.CharField(max_length=50, unique=True, verbose_name="Идентификатор Wikidata (QID)")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название")
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)], 
                               verbose_name="Средний рейтинг")
    review_count = models.IntegerField(default=0, verbose_name="Количество оценок")

    class Meta:
        verbose_name = "Культурный объект"
        verbose_name_plural = "Культурные объекты"
        indexes = [
            models.Index(fields=['wikidata_id']),
        ]

    def __str__(self):
        return f"{self.name or self.wikidata_id} (★ {self.rating})"


class Favorite(models.Model):
    """Избраное"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    wikidata_id = models.CharField(max_length=50, help_text="Идентификатор объекта (QID)")
    
    # Кэш для быстрого рендеринга страницы профиля во Vue
    place_label = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name="Местность/Город")
    image_url = models.URLField(max_length=500, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        # один и тот же пользователь не может добавить одно место дважды
        unique_together = ('user', 'wikidata_id')
        indexes = [
            models.Index(fields=['user', 'wikidata_id']),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.wikidata_id}"