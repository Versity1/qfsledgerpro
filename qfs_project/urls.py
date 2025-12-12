
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('superadmin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('pwa.urls')),  # You MUST use an empty string as the URL prefix
]
