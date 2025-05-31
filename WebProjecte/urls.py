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
    path('how-to-play/', views.how_to_play, name='how_to_play'), 
    path('profile/', views.profile_view, name='profile'),
    path('collection/', views.collection_view, name='collection'),
    path('api/cards/', views.api_cards, name='api_cards'),  
    path('api/my-cards/', views.user_cards_api, name='user_cards_api'),
    path('add-card/', views.add_card, name='add_card'),
    path('friends/', views.friends_list, name='friends_list'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('friends/send_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friends/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('select-pack/', views.pack_selector_view, name='select_pack'),
    path('open-pack/<int:set_id>/', views.open_pack_view, name='open_pack'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
