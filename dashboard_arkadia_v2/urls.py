from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('funds_and_strategies.urls')),
    path('users/', include('users.urls')),
    path('', views.home, name='home'),
    path('__debug__/', include('debug_toolbar.urls')),
]
