from modeltranslation.translator import register, TranslationOptions
from core.models import News

@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)  # поля, которые нужно переводить
