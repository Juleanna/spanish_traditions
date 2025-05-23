from modeltranslation.translator import translator, TranslationOptions
from core.models import News 

class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'content') 

translator.register(News, NewsTranslationOptions)