from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from ckeditor_uploader.fields import RichTextUploadingField
from django.urls import reverse

def page_image_upload_to(instance, filename):
    return f'pages/{instance.slug}/{filename}'

class Page(models.Model):
    title = models.CharField(_("Заголовок"), max_length=255)
    slug = models.SlugField(_("URL"), unique=True, allow_unicode=True)
    content = RichTextUploadingField(_("Зміст"), config_name='default')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="children", verbose_name=_("Батьківська сторінка")
    )
    is_active = models.BooleanField(_("Активна"), default=True)
    meta_description = models.TextField(_("Метаопис"), blank=True, null=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)
    
    class Meta:
        ordering = ['menu_order']
        verbose_name = _("Сторінка")
        verbose_name_plural = _("Сторінки")

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'slug': self.slug})


def gallery_upload_to(instance, filename):
    return f'gallery/{instance.title}_{filename}'


class GalleryItem(models.Model):
    title = models.CharField(_("Назва"), max_length=255)
    image = models.ImageField(_("Зображення"), upload_to=gallery_upload_to)
    description = RichTextUploadingField(_("Опис"), blank=True, null=True)
    category = models.CharField(_("Категорія"), max_length=255, blank=True, null=True)
    tags = TaggableManager(_("Теги"), blank=True)
    display_order = models.PositiveIntegerField(_("Порядок відображення"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        ordering = ['display_order']
        verbose_name = _("Елемент галереї")
        verbose_name_plural = _("Елементи галереї")

    def __str__(self):
        return self.title


def news_upload_to(instance, filename):
    return f'news/{instance.title}_{filename}'


class News(models.Model):
    title = models.CharField(_("Заголовок"), max_length=255)
    slug = models.SlugField(_("URL"), unique=True, allow_unicode=True)
    content = RichTextUploadingField(_("Контент"), config_name='default')
    image = models.ImageField(_("Зображення"), upload_to=news_upload_to, blank=True, null=True)
    tags = TaggableManager(_("Теги"), blank=True)
    published_date = models.DateTimeField(_("Дата публікації"), auto_now_add=True)
    is_active = models.BooleanField(_("Активна"), default=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        ordering = ['-published_date']
        verbose_name = _("Новина")
        verbose_name_plural = _("Новини")

    def __str__(self):
        return self.title


def icon_upload_to(instance, filename):
    return f'icons/{instance.title}_{filename}'


class Section(models.Model):
    title = models.CharField(_("Назва"), max_length=255)
    display_order = models.PositiveIntegerField(_("Порядок відображення"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Секція")
        verbose_name_plural = _("Секції")

    def __str__(self):
        return self.title or _("Секція без назви")


class Card(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="cards", verbose_name=_("Секція"))
    title = models.CharField(_("Заголовок"), max_length=255)
    icon = models.ImageField(_("Значок"), upload_to=icon_upload_to)
    description = RichTextUploadingField(_("Опис"))
    link = models.URLField(_("Посилання"), blank=True, null=True)
    link_text = models.CharField(_("Текст посилання"), max_length=255, default="Дізнатись більше")
    display_order = models.PositiveIntegerField(_("Порядок відображення"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Сторінка"))

    class Meta:
        ordering = ['display_order']
        verbose_name = _("Карточка")
        verbose_name_plural = _("Карточки")

    def save(self, *args, **kwargs):
        # Если указана страница и поле `link` пустое, задаем ссылку на страницу
        if self.page and not self.link:
            self.link = self.page.get_absolute_url()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


def logo_upload_to(instance, filename):
    return f'partners/{instance.name}_{filename}'

class Partner(models.Model):
    name = models.CharField(_("Назва партнера"), max_length=255)
    website = models.URLField(_("Сайт партнера"), blank=True, null=True)
    logo = models.ImageField(_("Логотип"), upload_to=logo_upload_to, blank=True, null=True)
    description = RichTextUploadingField(_("Опис"), blank=True, null=True)
    is_active = models.BooleanField(_("Активний"), default=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)
    display_order = models.PositiveIntegerField(_("Порядок відображення"), default=0)

    class Meta:
        verbose_name = _("Партнер")
        verbose_name_plural = _("Партнеры")
        ordering = ['name']

    def __str__(self):
        return self.name
    

class ContactInfo(models.Model):
    store_name = models.CharField(_("Назва магазину"), max_length=255, default="Мій магазин")
    address = models.TextField(_("Адреса"), blank=True, null=True)
    phone = models.CharField(_("Телефон"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Електронна пошта"), blank=True, null=True)
    working_hours = models.CharField(_("Робочий годинник"), max_length=255, blank=True, null=True)
    facebook = models.URLField(_("Facebook"), blank=True, null=True)
    instagram = models.URLField(_("Instagram"), blank=True, null=True)
    twitter = models.URLField(_("Twitter"), blank=True, null=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Контактна інформація")
        verbose_name_plural = _("Контактна інформація")

    def __str__(self):
        return self.store_name

class MenuItem(models.Model):
    title = models.CharField(_("Заголовок"), max_length=255)
    page = models.ForeignKey(Page, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Сторінка"))
    url = models.CharField(_("Посилання"), max_length=255, blank=True, null=True, help_text=_("Якщо вказано, використовуватиметься це посилання замість сторінки"))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children', verbose_name=_("Батько"))
    menu_order = models.PositiveIntegerField(_("Порядок"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        ordering = ['menu_order']
        verbose_name = _("Пункт меню")
        verbose_name_plural = _("Пункти меню")

    def __str__(self):
        return self.title

    def get_url(self):
        if self.url:
            return self.url
        elif self.page:
            return self.page.get_absolute_url()  
        else:
            return '#'
