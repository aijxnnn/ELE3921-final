from django.urls import path
from django.contrib import admin
from . import views
from django.conf import settings

urlpatterns = [
      path('admin/', admin.site.urls),
]