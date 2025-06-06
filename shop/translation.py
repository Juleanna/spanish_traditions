from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Product


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'short_description', 'meta_title', 'meta_description')


translator.register(Category, CategoryTranslationOptions)
translator.register(Product, ProductTranslationOptions)