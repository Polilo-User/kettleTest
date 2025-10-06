from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    data = {
        'title': '123'
    }
    return render(request, 'main/index.html', data)