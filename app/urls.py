from django.contrib import admin
from django.urls import path, include  # <--- include é importante

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('busapp.urls')),  # <-- aqui incluímos as URLs do app
]
