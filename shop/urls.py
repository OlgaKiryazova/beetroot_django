from django.urls import path
from . views import index, shop, single_product


urlpatterns = [
    path('', index, name='index'),
    path('shop/', shop, name='shop'),
    path('single_product/', single_product, name='single_product'),
]
