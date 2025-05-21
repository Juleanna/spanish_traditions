from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse

def page_image_upload_to(instance, filename):
    return f'pages/{instance.slug}/{filename}'


class Page(models.Model):
    title = models.CharField(_("Заголовок"), max_length=255)
    slug = models.SlugField(_("URL"), unique=True, allow_unicode=True)
    content = CKEditor5Field(_("Контент"))
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="children", verbose_name=_("Родительская страница")
    )
    menu_order = models.PositiveIntegerField(_("Порядок в меню"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)
    meta_description = models.TextField(_("Метаописание"), blank=True, null=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)
    image = models.ImageField(_("Изображение страницы"), upload_to=page_image_upload_to, blank=True, null=True)

    class Meta:
        ordering = ['menu_order']
        verbose_name = _("Страница")
        verbose_name_plural = _("Страницы")

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'slug': self.slug})


def gallery_upload_to(instance, filename):
    return f'gallery/{instance.title}_{filename}'


class GalleryItem(models.Model):
    title = models.CharField(_("Название"), max_length=255)
    image = models.ImageField(_("Изображение"), upload_to=gallery_upload_to)
    description = models.TextField(_("Описание"), blank=True, null=True)
    category = models.CharField(_("Категория"), max_length=255, blank=True, null=True)
    tags = TaggableManager(_("Теги"), blank=True)
    display_order = models.PositiveIntegerField(_("Порядок отображения"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = _("Элемент галереи")
        verbose_name_plural = _("Элементы галереи")

    def __str__(self):
        return self.title


def news_upload_to(instance, filename):
    return f'news/{instance.title}_{filename}'


class News(models.Model):
    title = models.CharField(_("Заголовок"), max_length=255)
    slug = models.SlugField(_("URL"), unique=True, allow_unicode=True)
    content = models.TextField(_("Контент"))
    image = models.ImageField(_("Изображение"), upload_to=news_upload_to, blank=True, null=True)
    tags = TaggableManager(_("Теги"), blank=True)
    published_date = models.DateTimeField(_("Дата публикации"), auto_now_add=True)
    is_active = models.BooleanField(_("Активна"), default=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        ordering = ['-published_date']
        verbose_name = _("Новость")
        verbose_name_plural = _("Новости")

    def __str__(self):
        return self.title


def icon_upload_to(instance, filename):
    return f'icons/{instance.title}_{filename}'


class Section(models.Model):
    title = models.CharField(_("Название"), max_length=255)
    display_order = models.PositiveIntegerField(_("Порядок отображения"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Секция")
        verbose_name_plural = _("Секции")

    def __str__(self):
        return self.title or "Секция без названия"


class Card(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="cards", verbose_name=_("Секция"))
    title = models.CharField(_("Заголовок"), max_length=255)
    icon = models.ImageField(_("Иконка"), upload_to=icon_upload_to)
    description = CKEditor5Field(_("Описание"))
    link = models.URLField(_("Ссылка"), blank=True, null=True)
    link_text = models.CharField(_("Текст ссылки"), max_length=255, default="Дізнатись більше")
    display_order = models.PositiveIntegerField(_("Порядок отображения"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = _("Карточка")
        verbose_name_plural = _("Карточки")

    def __str__(self):
        return self.title

def logo_upload_to(instance, filename):
    return f'partners/{instance.name}_{filename}'

class Partner(models.Model):
    name = models.CharField(_("Название партнера"), max_length=255)
    website = models.URLField(_("Сайт партнера"), blank=True, null=True)
    logo = models.ImageField(_("Логотип"), upload_to=logo_upload_to, blank=True, null=True)
    description = models.TextField(_("Описание"), blank=True, null=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)
    display_order = models.PositiveIntegerField(_("Порядок отображения"), default=0)

    class Meta:
        verbose_name = _("Партнер")
        verbose_name_plural = _("Партнеры")
        ordering = ['name']

    def __str__(self):
        return self.name
    

class ContactInfo(models.Model):
    store_name = models.CharField(_("Название магазина"), max_length=255, default="Мой магазин")
    address = models.TextField(_("Адрес"), blank=True, null=True)
    phone = models.CharField(_("Телефон"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Электронная почта"), blank=True, null=True)
    working_hours = models.CharField(_("Рабочие часы"), max_length=255, blank=True, null=True)
    facebook = models.URLField(_("Facebook"), blank=True, null=True)
    instagram = models.URLField(_("Instagram"), blank=True, null=True)
    twitter = models.URLField(_("Twitter"), blank=True, null=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Контактная информация")
        verbose_name_plural = _("Контактная информация")

    def __str__(self):
        return self.store_name

class MenuItem(models.Model):
    title = models.CharField(_("Заголовок"), max_length=255)
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Страница"))
    url = models.CharField(_("Ссылка"), max_length=255, blank=True, null=True, help_text=_("Если указана, будет использоваться эта ссылка вместо страницы"))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children', verbose_name=_("Родитель"))
    menu_order = models.PositiveIntegerField(_("Порядок"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        ordering = ['menu_order']
        verbose_name = _("Пункт меню")
        verbose_name_plural = _("Пункты меню")

    def __str__(self):
        return self.title

    def get_url(self):
        if self.url:
            return self.url
        elif self.page:
            return self.page.get_absolute_url()  # Нужно реализовать get_absolute_url в Page
        else:
            return '#'
