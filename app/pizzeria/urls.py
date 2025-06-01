from django.urls import path
from django.contrib import admin
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.index, name="index"),
    path('product/<str:name>/', views.product_view, name='product_view'),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path('cart/', views.view_cart, name= 'view_cart'),
    path('admin/', admin.site.urls),
]