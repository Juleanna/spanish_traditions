from django.urls import path, re_path
from . import views

app_name = 'shop'

urlpatterns = [
    # Головна сторінка магазину
    path('', views.product_list, name='product_list'),
    
    # Товари
    path('products/', views.product_list, name='product_list'),
    re_path(r'^product/(?P<slug>[\w\-]+)/', views.product_detail, name='product_detail'),
    
    # Категорії - використовуємо re_path для підтримки Unicode
    re_path(r'^category/(?P<slug>[\w\-]+)/', views.category_detail, name='category_detail'),
    
    # Кошик
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    
    # Оформлення замовлення
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    
    # Замовлення користувача
    path('orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Список бажань
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    
    # Відгуки
    re_path(r'^product/(?P<product_slug>[\w\-]+)/review/', views.add_review, name='add_review'),
    
    # Пошук
    path('search/', views.search, name='search'),
]