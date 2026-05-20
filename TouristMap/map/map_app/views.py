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
def api_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            if not username or not email or not password:
                return JsonResponse({'status': 'error', 'message': 'Заполните все поля'}, status=400)
            # проверка занятости email
            if User.objects.filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Этот email уже зарегистрирован'}, status=400)

            # используем create_user, чтобы Django автоматически захешировал пароль
            user = User.objects.create_user(username=username, email=email, password=password)
            # Автоматически авторизуем пользователя сразу после регистрации
            login(request, user)

            return JsonResponse({
                'status': 'ok',
                'message': 'Регистрация прошла успешно',
                'username': user.username
            })

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Некорректный формат данных (JSON)'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)

@csrf_exempt
def api_toggle_favorite(request):
    if not request.user.is_authenticated:
        if request.method == 'GET':
            return JsonResponse([], safe=False)
        return JsonResponse({'status': 'error', 'message': 'Требуется авторизация'}, status=401)
    
    user = request.user
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
                'region': " ",
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

            user = request.user if request.user.is_authenticated else User.objects.first()
            
            # 1. Проверяем избранное по внешнему ID места
            existing_fav = Favorite.objects.filter(user=user, place__external_id=external_id).first()

            if existing_fav:
                existing_fav.delete()
                return JsonResponse({'status': 'removed'})

            # 2. Обработка координат (более надежная)
            coord_raw = data.get('coordinate', '')
            try:
                # Извлекаем все числа (включая отрицательные и дробные)
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", coord_raw)
                if len(coords) >= 2:
                    # Wikidata отдает Longitude Latitude. Django Point(x, y) ждет так же.
                    point = Point(float(coords[0]), float(coords[1]))
                else:
                    raise ValueError("Недостаточно данных для координат")
            except Exception:
                point = Point(39.71, 47.24)

            category, _ = Category.objects.get_or_create(name="Культура", defaults={'slug': 'culture'})
            city_name = data.get('city')
            city, _ = City.objects.get_or_create(name=city_name)

            # 4. Создаем или обновляем Место
            # Используем .truncate() или срезаем строку, если имя слишком длинное для БД
            name = data.get('title', 'Без названия')[:250] 

            place, _ = Place.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'name': name,
                    'category': category,
                    'city': city,
                    'location': point,
                    'address': data.get('address', 'Адрес не указан')[:250],
                }
            )

            # 5. Картинка
            image_url = data.get('image_url')
            if image_url:
                PlaceImage.objects.update_or_create(
                    place=place,
                    is_main=True,
                    defaults={'image': image_url}
                )

            # 6. Создаем избранное (используем get_or_create во избежание дублей)
            Favorite.objects.get_or_create(user=user, place=place)
            
            return JsonResponse({'status': 'added'})

        except Exception as e:
            # Выводим ошибку в консоль сервера, чтобы вы видели, что именно пошло не так
            print(f"Ошибка в api_toggle_favorite: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)