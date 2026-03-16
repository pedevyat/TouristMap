from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return render(request,'map_app/index.html')

def about(request):
    return HttpResponse("Здесь будет информация о проекте")

def user(request):
    return HttpResponse("Здесь будет личный кабинет")