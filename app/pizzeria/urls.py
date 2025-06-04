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
    path('my-account/', views.account_view, name='account'),
    path('edit-account/', views.edit_account_view, name='edit_account'),
    path('edit-account/change-password', auth_views.PasswordChangeView.as_view(template_name='pizzeria/change_password.html',success_url='/account/'), name='change_password'),
    path('cart/order/', views.order, name='order'),
    path('order-history/', views.my_orders, name='my_orders'),
    path('manage_orders/', views.manage_orders, name='manage_orders'),
]