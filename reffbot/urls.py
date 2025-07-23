# File: reffbot/urls.py

from django.contrib import admin
from django.urls import path
from bot.views import telegram_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', telegram_webhook),  # <- endpoint webhook Telegram
]
