from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Аутентифікація
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Особистий кабінет
    path('', views.profile_dashboard, name='profile_dashboard'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('change-password/', views.change_password, name='change_password'),
    
   
    # Порівняння товарів
    path('comparison/', views.product_comparison, name='product_comparison'),
    path('comparison/add/<int:product_id>/', views.add_to_comparison, name='add_to_comparison'),
    path('comparison/remove/<int:product_id>/', views.remove_from_comparison, name='remove_from_comparison'),
    
    # Відстеження товарів
    path('tracking/', views.tracking_list, name='tracking_list'),
]