from django.shortcuts import render

def index(request):
    context = {}
    return render(request, 'index.html', context)

def shop(request):
    context = {}
    return render(request, 'shop.html', context)

def single_product(request):
    context = {}
    return render(request, 'single_product.html', context)
