# ewaste_backend/core/urls.py

from django.urls import path
from core import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include # <--- Make sure 'include' is here

urlpatterns = [
    # 🏠 Static pages
    path('', views.homepage, name='homepage'),
    path('services/', views.services, name='services'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    path('contact/', views.contact, name='contact'),

    # User authentication
    # Consider renaming views.login/signup to avoid conflicts, e.g., views.user_login
    path('login/', views.login, name='login'), # If these are your custom login/signup views
    path('signup/', views.signup, name='signup'),

    # Service-specific pages
    path('data-destruction/', views.data_destruction, name='data_destruction'),
    path('refurbishment/', views.refurbishment, name='refurbishment'),

    # 📦 Pickup request
    path('pickup/', views.pickup, name='pickup'),
    # If reqs is a custom admin-like page, you might need to reconsider its placement.
    # For now, if views.reqs exists, keep it. Otherwise, remove this line.
    path('reqs/', views.reqs, name='reqs'), # Make sure views.reqs exists in views.py

    # 🤖 Chatbot API
    path('api/chatbot/', views.chatbot_response, name='chatbot_response'),

    # Removed: 'admin/pickups/' and 'admin/pickup/' - these should be handled by admin.site.urls
    # or be distinct user-facing pages if not part of the Django Admin.
]