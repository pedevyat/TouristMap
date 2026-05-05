from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
import json
from .models import Place, Favorite, Category, City, PlaceImage
import re
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User

# Create your views here.
def index(request):
    return render(request,'map_app/index.html')

def about(request):
    return HttpResponse("Здесь будет информация о проекте")

def user(request):
    return HttpResponse("Здесь будет личный кабинет")

@ensure_csrf_cookie
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = authenticate(username=data.get('username'), password=data.get('password'))
            if user is not None:
                login(request, user)
                return JsonResponse({'status': 'ok', 'username': user.username})
            return JsonResponse({'status': 'error', 'message': 'Неверные данные'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Ошибка данных'}, status=400)
            
    # ОБЯЗАТЕЛЬНО возвращаем ответ для GET запроса (чтобы установилась куки)
    return JsonResponse({'status': 'waiting_for_post'})

@csrf_exempt
def api_toggle_favorite(request):
    # Получение всех избранных мест пользователя
    if request.method == 'GET':
        # Берем текущего пользователя или первого из базы (для тестов)
        user = request.user if request.user.is_authenticated else User.objects.first()
        if not user:
            return JsonResponse([], safe=False)

        # Подгружаем связанные данные через select_related для оптимизации
        favorites = Favorite.objects.filter(user=user).select_related('place', 'place__city')
        
        results = []
        for fav in favorites:
            main_image = fav.place.images.filter(is_main=True).first()
            image_path = main_image.image if main_image else None
            results.append({
                'id': fav.place.external_id,      # QID из Wikidata
                'name': fav.place.name,           # Название
                'city': fav.place.city.name,      # Город
                'region': "",
                'date': fav.added_at.strftime("%d.%m.%Y"), 
                'image': image_path,
                'coordinate': f"{fav.place.location.x}, {fav.place.location.y}"
            })
        return JsonResponse(results, safe=False)

    # Добавление или удаление из избранного
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            external_id = data.get('place_id')
            
            if not external_id:
                return JsonResponse({'status': 'error', 'message': 'No place_id provided'}, status=400)

            # 1. Проверяем, есть ли уже это место в избранном у пользователя
            user = request.user if request.user.is_authenticated else User.objects.first()
            existing_fav = Favorite.objects.filter(user=user, place__external_id=external_id).first()

            if existing_fav:
                # Если есть — удаляем (тоггл)
                existing_fav.delete()
                return JsonResponse({'status': 'removed'})

            # Если места нет в базе Place, создаем его
            # Сначала подготовим категорию и город (базовые заглушки)
            category, _ = Category.objects.get_or_create(name="Культура", defaults={'slug': 'culture'})
            city, _ = City.objects.get_or_create(name=data.get('city', 'Ростов-на-Дону'))

            # Парсим координаты из строки "Point(39.71 47.24)" или просто чисел
            coord_raw = data.get('coordinate', '0 0')
            coords = re.findall(r"[-+]?\d*\.\d+|\d+", coord_raw)
            point = Point(float(coords[0]), float(coords[1]))

            place, _ = Place.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'name': data.get('title', 'Без названия'),
                    'category': category,
                    'city': city,
                    'location': point,
                    'address': data.get('address', 'Адрес не указан'),
                }
            )
            image_url = data.get('image_url')
            if image_url:
                # Создаем или обновляем главную картинку
                PlaceImage.objects.update_or_create(
                    place=place,
                    is_main=True,
                    defaults={'image': image_url}
                )
            # Создаем запись в избранном
            Favorite.objects.create(user=user, place=place)
            return JsonResponse({'status': 'added'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)