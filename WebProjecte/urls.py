from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from DjangoProjectWeb import settings
from . import views
from .views import profile_view

urlpatterns = [
    path('',views.home,name='home'),
    path('login/',auth_views.LoginView.as_view(template_name='login.html'),name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('como-jugar/', views.como_jugar, name='como_jugar'),
    path('card/', views.card, name='card'),
    path('profile/', views.profile_view, name='profile'),
    path('cards/', views.cards, name='cards'),
    path('api/cartas/', views.api_cartas, name='api_cartas'),
    path('add-card/', views.add_card, name='add_card'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
