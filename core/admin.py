from django.contrib import admin
from .models import Page, GalleryItem, News, Section, Card, Partner, ContactInfo, MenuItem
from modeltranslation.admin import TabbedTranslationAdmin

@admin.register(Page)
class PageAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'slug', 'is_active', 'menu_order', 'parent', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at', 'parent')
    search_fields = ('title', 'content', 'slug')
    ordering = ('menu_order',)
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ('is_active', 'menu_order')


@admin.register(GalleryItem)
class GalleryItemAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'category', 'is_active', 'display_order', 'created_at', 'updated_at')
    list_filter = ('is_active', 'category', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'category')
    ordering = ('display_order',)
    list_editable = ('is_active', 'display_order')

@admin.register(News)
class NewsAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'slug', 'is_active', 'published_date', 'created_at', 'updated_at')
    list_filter = ('is_active', 'published_date', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'slug')
    ordering = ('-published_date',)
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ('is_active',)
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content (short)'


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_order', 'is_active')  # добавь нужные поля

@admin.register(Card)
class CardAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'section', 'is_active', 'display_order', 'page', 'link')
    list_filter = ('section', 'is_active')
    fields = ('section', 'title', 'icon', 'description', 'page', 'link', 'link_text', 'display_order', 'is_active')
    search_fields = ('title', 'description')

@admin.register(Partner)
class PartnerAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'website', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(ContactInfo)
class ContactInfoAdmin(TabbedTranslationAdmin):
    list_display = ('store_name', 'phone', 'email', 'updated_at')
    search_fields = ('store_name', 'address', 'phone', 'email')


@admin.register(MenuItem)
class MenuItemAdmin(TabbedTranslationAdmin):
    list_display = ('title', 'page', 'url', 'parent', 'menu_order', 'is_active')
    list_filter = ('is_active',)
    ordering = ('menu_order',)