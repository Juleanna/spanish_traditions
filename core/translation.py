from modeltranslation.translator import translator, TranslationOptions
from .models import Page, GalleryItem, News, Card, Partner, ContactInfo, MenuItem
from core.models import News


class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'content') 

class PageTranslationOptions(TranslationOptions):
    fields = ('title', 'content')
    # Для CKEditor5Field нужно добавить специальный обработчик
    class TranslationMeta:
        fields = ('content',)  # Поля, требующие особой обработки 

class GalleryItemTranslationOptions(TranslationOptions):
    fields = ('title', 'description') 

class CardTranslationOptions(TranslationOptions):
    fields = ('title', 'description','link_text') 

class PartnerTranslationOptions(TranslationOptions):
    fields = ('name', 'description') 

class ContactInfoTranslationOptions(TranslationOptions):
    fields = ('store_name', 'address') 

class MenuItemTranslationOptions(TranslationOptions):
    fields = ('title',) 

translator.register(News, NewsTranslationOptions)
translator.register(Page, PageTranslationOptions)
translator.register(GalleryItem, GalleryItemTranslationOptions)
translator.register(Card, CardTranslationOptions)
translator.register(Partner, PartnerTranslationOptions)
translator.register(ContactInfo, ContactInfoTranslationOptions)
translator.register(MenuItem, MenuItemTranslationOptions)