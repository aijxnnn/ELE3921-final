from django.urls import path
from django.contrib import admin
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.index, name="index"),
    path('product/<str:name>/', views.product_view, name='product_view'),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
    path('remove_item/', views.remove_item, name='remove_item'),
    path('cart/', views.view_cart, name= 'cart'),
    path('admin/', admin.site.urls),
    
]