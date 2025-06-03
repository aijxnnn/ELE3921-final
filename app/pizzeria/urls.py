from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.index, name="index"),
    path('product/<str:name>/', views.product_view, name='product_view'),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path('cart/', views.view_cart, name= 'cart'),
    path('clear-cart/', views.clear_cart, name= 'clear_cart'),
    path('remove-item/', views.remove_item, name= 'remove_item'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('register/', views.register, name='register'),

]