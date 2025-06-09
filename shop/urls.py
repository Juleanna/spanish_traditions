from django.urls import path, re_path
from . import views

app_name = 'shop'

urlpatterns = [
    # Головна сторінка магазину та каталог
    path('', views.product_list, name='product_list'),
    path('catalog/', views.product_list, name='catalog'),
    
    # Товари
    path('products/', views.product_list, name='product_list'),
    re_path(r'^product/(?P<slug>[\w\-]+)/$', views.product_detail, name='product_detail'),
    
    # Категорії - використовуємо re_path для підтримки Unicode
    re_path(r'^category/(?P<slug>[\w\-]+)/$', views.category_detail, name='category_detail'),
    
    # Кошик та керування ним
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/data/', views.cart_data_api, name='cart_data'),  
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    
    # Оформлення замовлення
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    
    # Замовлення користувача
    path('orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),  
    
    # Список бажань
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'), 
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),  
    
    # Відгуки
    re_path(r'^product/(?P<product_slug>[\w\-]+)/review/add/$', views.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),  
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),  
    
    # Пошук
    path('search/', views.search, name='search'),
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),  
    
    # Порівняння товарів (додаткова функція)
    path('compare/', views.compare_products, name='compare_products'),
    path('compare/add/', views.add_to_compare, name='add_to_compare'),
    path('compare/remove/', views.remove_from_compare, name='remove_from_compare'),
    path('compare/clear/', views.clear_compare, name='clear_compare'),
    
    # API для AJAX запитів
    path('api/product/<int:product_id>/stock/', views.check_product_stock, name='check_product_stock'),
    path('api/cart/count/', views.get_cart_count, name='get_cart_count'),
    path('api/shipping/calculate/', views.calculate_shipping, name='calculate_shipping'),
    
    # Швидкий перегляд товару (modal)
    path('api/product/<int:product_id>/quick-view/', views.product_quick_view, name='product_quick_view'),
    
    # Фільтри та сортування (AJAX)
    path('api/products/filter/', views.filter_products_ajax, name='filter_products_ajax'),
    
    # Знижки та промокоди
    path('api/coupon/validate/', views.validate_coupon, name='validate_coupon'),
    
    # Відстеження замовлення
    path('track/<str:order_number>/', views.track_order, name='track_order'),

    path('cart/data/', views.cart_data_api, name='cart_data_api'),

    path('validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
]