from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie
import json

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