from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
import json
from .models import Place, Favorite, Category, City, PlaceImage
import re
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
import requests
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.core.mail import send_mail
from django.core.signing import Signer

CATEGORY_MAPPING = {
    'Q11742': 'VALUES ?type { wd:Q11742 wd:Q22698 wd:Q126877 wd:Q1496967 } ?place wdt:P31 ?type.',
    'Q862454': 'VALUES ?type { wd:Q862454 wd:Q15631416 wd:Q3840711 } ?place wdt:P31 ?type.',
    'Q33506': 'VALUES ?type { wd:Q33506 wd:Q205391 wd:Q54173 wd:Q833017 wd:Q7075 } ?place wdt:P31 ?type.',
    'Q24354': 'VALUES ?type { wd:Q11635 wd:Q153562 wd:Q1060165 wd:Q47928 wd:Q11812394 wd:Q16889960 } ?place wdt:P31 ?type.',
    'Q2035041': 'VALUES ?type { wd:Q8502 } ?place wdt:P31 ?type.'
}

# Create your views here.
def index(request):
    return render(request,'map_app/index.html')

@ensure_csrf_cookie
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            # явная проверка существования, пароля и активации почты
            try:
                user = User.objects.get(username=username)
                
                # Проверяем правильность пароля
                if user.check_password(password):
                    # Если пароль верный, но почта НЕ подтверждена
                    if not user.is_active:
                        return JsonResponse({
                            'status': 'error', 
                            'message': 'Ваш аккаунт еще не активирован! Пожалуйста, подтвердите Email по ссылке из письма.'
                        }, status=403) # 403 Forbidden
                    
                    # Если активен — авторизуем в сессии
                    login(request, user)
                    return JsonResponse({'status': 'ok', 'username': user.username})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Неверное имя пользователя или пароль'}, status=401)
                    
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Неверное имя пользователя или пароль'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Ошибка данных'}, status=400)
            
    return JsonResponse({'status': 'waiting_for_post'})

@csrf_exempt
def api_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'status': 'ok', 'message': 'Вы успешно вышли из системы'})
    
    return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)

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
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Пользователь с таким именем уже существует. Пожалуйста, придумайте другое имя.'
                }, status=400)
            
            # проверка занятости email
            if User.objects.filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Этот email уже зарегистрирован'}, status=400)

            # используем create_user, чтобы Django автоматически захешировал пароль
            user = User.objects.create_user(username=username, email=email, password=password, is_active=False)

            # Генерация временного токена (с отметкой времени)
            from django.core.signing import TimestampSigner
            signer = TimestampSigner()
            token = signer.sign(username)
            activation_url = f"http://127.0.0.1:5173/verify-email?token={token}"

            # Отправка письма (настройки SMTP/Resend берутся из settings.py)
            send_mail(
                subject="Подтверждение регистрации в ВикиТурист",
                message=f"Для подтверждения регистрации перейдите по ссылке: {activation_url}",
                from_email="ВикиТурист <onboarding@resend.dev>",
                recipient_list=[email],
                html_message=f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
                        <h3 style="color: #333;">Добро пожаловать в ВикиТурист!</h3>
                        <p style="color: #666;">Спасибо за регистрацию в нашем сервисе. Для активации вашего аккаунта и подтверждения адреса электронной почты нажмите на кнопку ниже:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{activation_url}" style="background-color: #4AAE8A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                Подтвердить Email
                            </a>
                        </div>
                        <p style="font-size: 12px; color: #999; text-align: center;">Ссылка действительна в течение 24 часов.</p>
                    </div>
                """,
            )


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
def api_verify_email(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            
            if not token:
                return JsonResponse({'status': 'error', 'message': 'Токен подтверждения отсутствует'}, status=400)
            
            from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
            signer = TimestampSigner()
            
            try:
                # Проверяем подпись токена и его возраст (86400 секунд = 24 часа)
                username = signer.unsign(token, max_age=86400)
            except SignatureExpired:
                return JsonResponse({'status': 'error', 'message': 'Срок действия ссылки подтверждения истек'}, status=400)
            except BadSignature:
                return JsonResponse({'status': 'error', 'message': 'Недействительный или поврежденный токен'}, status=400)
            
            try:
                user = User.objects.get(username=username)
                
                if user.is_active:
                    return JsonResponse({'status': 'ok', 'message': 'Аккаунт уже был успешно активирован ранее'})
                
                # Активируем пользователя
                user.is_active = True
                user.save()
                
                # Автоматически авторизуем пользователя в сессии после успешной активации
                login(request, user)
                
                return JsonResponse({
                    'status': 'ok',
                    'message': 'Электронная почта успешно подтверждена. Вход выполнен.',
                    'username': user.username
                })
                
            except User.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Пользователь, связанный с этим токеном, не найден'}, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Ошибка чтения формата данных JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Внутренняя ошибка при верификации: {str(e)}'}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)

@csrf_exempt
def api_toggle_favorite(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Требуется авторизация'}, status=401)
    
    user = request.user
    # Получение всех избранных мест пользователя
    if request.method == 'GET':
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
            
            # Проверяем избранное по внешнему ID места
            existing_fav = Favorite.objects.filter(user=user, place__external_id=external_id).first()

            if existing_fav:
                existing_fav.delete()
                return JsonResponse({'status': 'removed'})

            # Обработка координат
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

            # Создаем или обновляем Место
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
            image_url = data.get('image_url')
            if image_url:
                PlaceImage.objects.update_or_create(
                    place=place,
                    is_main=True,
                    defaults={'image': image_url}
                )
            # Создаем избранное (используем get_or_create во избежание дублей)
            Favorite.objects.get_or_create(user=user, place=place)
            
            return JsonResponse({'status': 'added'})

        except Exception as e:
            # Выводим ошибку в консоль сервера, чтобы вы видели, что именно пошло не так
            print(f"Ошибка в api_toggle_favorite: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
@require_GET
@cache_page(60 * 60 * 24)
def get_wikidata_places(request):
    class_qid = request.GET.get('classQID')
    
    if not class_qid or class_qid not in CATEGORY_MAPPING:
        return JsonResponse({'error': 'Неверный или отсутствующий параметр classQID'}, status=400)
    
    category_filter = CATEGORY_MAPPING[class_qid]
    
    # Формируем SPARQL запрос
    sparql_query = f"""
    SELECT DISTINCT ?place ?placeLabel ?coord ?image ?cityLabel WHERE {{
      ?place wdt:P17 wd:Q159 . 
      ?place wdt:P625 ?coord .
      {category_filter}
      ?place wdt:P18 ?image . 
      OPTIONAL {{ ?place wdt:P131 ?city. }}
      FILTER NOT EXISTS {{ ?place wdt:P576 ?demolished. }}
      FILTER NOT EXISTS {{ ?place wdt:P31/wdt:P279* wd:Q12269557. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ru". }}
    }}
    """
    
    wikidata_url = "https://query.wikidata.org/sparql"
    headers = {
        # Замени на данные своего проекта, чтобы Wikidata не банила запросы
        'User-Agent': 'TouristMapApp/1.0 (konstantin@example.com)' 
    }
    params = {
        'query': sparql_query,
        'format': 'json'
    }
    
    try:
        response = requests.get(wikidata_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 429:
            return JsonResponse({'error': 'Слишком много запросов к Wikidata'}, status=429)
            
        response.raise_for_status()
        raw_data = response.json()
        
        # Парсим и «выпрямляем» сложную структуру Wikidata в плоский JSON для фронтенда
        bindings = raw_data.get('results', {}).get('bindings', [])
        cleaned_places = []
        
        for item in bindings:
            cleaned_places.append({
                'id': item.get('place', {}).get('value', '').split('/')[-1],
                'name': item.get('placeLabel', {}).get('value', 'Без названия'),
                'coord': item.get('coord', {}).get('value', ''),
                'image': item.get('image', {}).get('value', ''),
                'city': item.get('cityLabel', {}).get('value', '')
            })
            
        return JsonResponse(cleaned_places, safe=False, json_dumps_params={'ensure_ascii': False})
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Wikidata: {e}")
        return JsonResponse({'error': 'Ошибка сервера при получении данных'}, status=500)