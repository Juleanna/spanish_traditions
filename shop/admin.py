from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from modeltranslation.admin import TabbedTranslationAdmin
from .models import (
    Category, Product, ProductImage, Cart, CartItem, 
    Order, OrderItem, Review, Wishlist
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_main', 'display_order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Немає зображення"
    image_preview.short_description = "Попередній перегляд"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'display_order', 'products_count', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ('is_active', 'display_order')
    ordering = ('display_order', 'name')

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = "Кількість товарів"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'is_available', 
                   'is_featured', 'rating', 'reviews_count', 'created_at')
    list_filter = ('category', 'is_available', 'is_featured', 'track_stock', 'country_origin', 'brand')
    search_fields = ('name', 'description', 'short_description', 'brand')
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ('price', 'discount_price', 'stock', 'is_available', 'is_featured')
    inlines = [ProductImageInline]
    readonly_fields = ('reviews_count', 'rating', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'slug', 'category', 'description', 'short_description')
        }),
        ('Ціни та наявність', {
            'fields': ('price', 'discount_price', 'stock', 'is_available', 'track_stock')
        }),
        ('Характеристики', {
            'fields': ('weight', 'volume', 'country_origin', 'brand'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Статус', {
            'fields': ('is_featured', 'is_active', 'rating', 'reviews_count')
        }),
        ('Дати', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'session_key')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'total_price')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'email', 'status', 'payment_status', 
                   'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at', 'country')
    search_fields = ('order_number', 'email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Інформація про замовлення', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Контактна інформація', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Адреса доставки', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Фінансова інформація', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        ('Додаткова інформація', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Дати', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']

    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_as_confirmed.short_description = "Позначити як підтверджені"

    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='shipped', shipped_at=timezone.now())
    mark_as_shipped.short_description = "Позначити як відправлені"

    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_as_delivered.short_description = "Позначити як доставлені"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_verified_purchase', 
                   'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product', 'user')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'product')


# Додатковий адмін для ProductImage, якщо потрібен окремий доступ
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'is_main', 'display_order')
    list_filter = ('is_main', 'product__category')
    search_fields = ('product__name', 'alt_text')
    list_editable = ('is_main', 'display_order')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Немає зображення"
    image_preview.short_description = "Попередній перегляд"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product')