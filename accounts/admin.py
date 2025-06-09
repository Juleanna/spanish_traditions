from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Вбудована форма профілю користувача"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Профіль')
    fieldsets = (
        (_('Контактна інформація'), {
            'fields': ('phone', 'birth_date')
        }),
        (_('Адреса доставки'), {
            'fields': ('default_address_line1', 'default_address_line2', 
                      'default_city', 'default_postal_code')
        }),
        (_('Налаштування'), {
            'fields': ('email_notifications', 'sms_notifications', 
                      'newsletter_subscription')
        }),
        (_('Статистика'), {
            'fields': ('total_orders', 'total_spent'),
            'classes': ('collapse',)
        }),
        (_('Додаткова інформація'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('total_orders', 'total_spent')


# Розширюємо стандартний UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 
                   'is_staff', 'date_joined', 'get_total_orders')
    list_filter = BaseUserAdmin.list_filter + ('date_joined',)
    search_fields = ('username', 'first_name', 'last_name', 'email',
                    'profile__phone')
    
    def get_total_orders(self, obj):
        """Отримати кількість замовлень користувача"""
        if hasattr(obj, 'profile'):
            return obj.profile.total_orders
        return 0
    get_total_orders.short_description = _('Замовлень')
    get_total_orders.admin_order_field = 'profile__total_orders'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Адміністрування профілів окремо"""
    list_display = ('user', 'phone', 'get_full_name', 'total_orders', 
                   'total_spent', 'created_at')
    list_filter = ('email_notifications', 'sms_notifications', 
                  'newsletter_subscription', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name',
                    'user__last_name', 'phone')
    readonly_fields = ('total_orders', 'total_spent', 'created_at', 'updated_at')
    
    fieldsets = (
        (_('Користувач'), {
            'fields': ('user',)
        }),
        (_('Контактна інформація'), {
            'fields': ('phone', 'birth_date')
        }),
        (_('Адреса доставки'), {
            'fields': ('default_address_line1', 'default_address_line2',
                      'default_city', 'default_postal_code')
        }),
        (_('Налаштування повідомлень'), {
            'fields': ('email_notifications', 'sms_notifications',
                      'newsletter_subscription')
        }),
        (_('Статистика'), {
            'fields': ('total_orders', 'total_spent')
        }),
        (_('Додаткова інформація'), {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def get_full_name(self, obj):
        """Повне ім'я користувача"""
        return obj.get_full_name()
    get_full_name.short_description = _('Повне ім\'я')
    
    actions = ['update_statistics']
    
    def update_statistics(self, request, queryset):
        """Оновити статистику для вибраних профілів"""
        for profile in queryset:
            profile.update_statistics()
        self.message_user(request, 
            _('Статистика оновлена для {} профілів').format(queryset.count()))
    update_statistics.short_description = _('Оновити статистику')


# Перереєструємо User з новим UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)