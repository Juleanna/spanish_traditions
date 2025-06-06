from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField

def product_image_upload_to(instance, filename):
    product_slug = instance.product.slug if instance.product and instance.product.slug else 'no-slug'
    return f'products/{product_slug}/{filename}'


class Category(models.Model):
    name = models.CharField(_("Назва категорії"), max_length=255)
    slug = models.SlugField(_("URL"), unique=True, allow_unicode=True)
    description = RichTextUploadingField(_("Опис"), blank=True, null=True)
    image = models.ImageField(_("Зображення"), upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name=_("Батьківська категорія")
    )
    is_active = models.BooleanField(_("Активна"), default=True)
    display_order = models.PositiveIntegerField(_("Порядок відображення"), default=0)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Категорія")
        verbose_name_plural = _("Категорії")
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    name = models.CharField(_("Назва товару"), max_length=255)
    slug = models.SlugField(_("URL"), unique=True, allow_unicode=True)
    description = RichTextUploadingField(_("Опис"))
    short_description = models.CharField(_("Короткий опис"), max_length=500, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name=_("Категорія"))
    price = models.DecimalField(_("Ціна"), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    discount_price = models.DecimalField(_("Знижкова ціна"), max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Інвентар
    stock = models.PositiveIntegerField(_("Кількість на складі"), default=0)
    is_available = models.BooleanField(_("Доступний"), default=True)
    track_stock = models.BooleanField(_("Відстежувати запаси"), default=True)
    
    # SEO та метадані
    meta_title = models.CharField(_("SEO заголовок"), max_length=255, blank=True)
    meta_description = models.CharField(_("SEO опис"), max_length=255, blank=True)
    
    # Технічні характеристики
    weight = models.DecimalField(_("Вага (кг)"), max_digits=6, decimal_places=3, blank=True, null=True)
    volume = models.DecimalField(_("Об'єм (л)"), max_digits=6, decimal_places=3, blank=True, null=True)
    country_origin = models.CharField(_("Країна походження"), max_length=100, blank=True)
    brand = models.CharField(_("Бренд"), max_length=100, blank=True)
    
    # Статус та дати
    is_featured = models.BooleanField(_("Рекомендований"), default=False)
    is_active = models.BooleanField(_("Активний"), default=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)
    
    # Рейтинг
    rating = models.DecimalField(_("Рейтинг"), max_digits=3, decimal_places=2, default=0.00,
                                validators=[MinValueValidator(0), MaxValueValidator(5)])
    reviews_count = models.PositiveIntegerField(_("Кількість відгуків"), default=0)

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товари")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    @property
    def get_price(self):
        """Повертає актуальну ціну (знижкову або звичайну)"""
        return self.discount_price if self.discount_price else self.price

    @property
    def has_discount(self):
        """Перевіряє, чи є знижка на товар"""
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percentage(self):
        """Обчислює відсоток знижки"""
        if self.has_discount:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0

    def is_in_stock(self):
        """Перевіряє, чи є товар в наявності"""
        if not self.track_stock:
            return self.is_available
        return self.stock > 0 and self.is_available

    @property
    def get_price(self):
        """Повертає актуальну ціну (знижкову або звичайну)"""
        return self.discount_price if self.discount_price else self.price

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_("Товар"))
    image = models.ImageField(_("Зображення"), upload_to=product_image_upload_to)
    alt_text = models.CharField(_("Альтернативний текст"), max_length=255, blank=True)
    is_main = models.BooleanField(_("Основне зображення"), default=False)
    display_order = models.PositiveIntegerField(_("Порядок відображення"), default=0)

    class Meta:
        verbose_name = _("Зображення товару")
        verbose_name_plural = _("Зображення товарів")
        ordering = ['display_order']

    def __str__(self):
        return f"{self.product.name} - {self.display_order}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Користувач"))
    session_key = models.CharField(_("Ключ сесії"), max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Кошик")
        verbose_name_plural = _("Кошики")

    def __str__(self):
        return f"Кошик {self.id}"

    @property
    def total_items(self):
        """Загальна кількість товарів у кошику"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Загальна вартість кошика"""
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name=_("Кошик"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Товар"))
    quantity = models.PositiveIntegerField(_("Кількість"), default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(_("Ціна за одиницю"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Товар у кошику")
        verbose_name_plural = _("Товари у кошику")
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        """Загальна вартість цієї позиції"""
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Зберігаємо актуальну ціну товару при додаванні в кошик
        if not self.price:
            self.price = self.product.get_price
        super().save(*args, **kwargs)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Очікує підтвердження')),
        ('confirmed', _('Підтверджено')),
        ('processing', _('Обробляється')),
        ('shipped', _('Відправлено')),
        ('delivered', _('Доставлено')),
        ('cancelled', _('Скасовано')),
        ('refunded', _('Повернуто')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Очікує оплати')),
        ('paid', _('Оплачено')),
        ('failed', _('Помилка оплати')),
        ('refunded', _('Повернуто')),
    ]

    # Інформація про замовлення
    order_number = models.CharField(_("Номер замовлення"), max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Користувач"))
    
    # Контактна інформація
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Телефон"), max_length=20)
    first_name = models.CharField(_("Ім'я"), max_length=100)
    last_name = models.CharField(_("Прізвище"), max_length=100)
    
    # Адреса доставки
    address_line1 = models.CharField(_("Адреса (рядок 1)"), max_length=255)
    address_line2 = models.CharField(_("Адреса (рядок 2)"), max_length=255, blank=True)
    city = models.CharField(_("Місто"), max_length=100)
    state = models.CharField(_("Область"), max_length=100)
    postal_code = models.CharField(_("Поштовий код"), max_length=20)
    country = models.CharField(_("Країна"), max_length=100, default="Україна")
    
    # Фінансова інформація
    subtotal = models.DecimalField(_("Сума без доставки"), max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(_("Вартість доставки"), max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Сума податку"), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Загальна сума"), max_digits=10, decimal_places=2)
    
    # Статуси
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(_("Статус оплати"), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Додаткова інформація
    notes = models.TextField(_("Примітки"), blank=True)
    
    # Дати
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)
    shipped_at = models.DateTimeField(_("Дата відправки"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Дата доставки"), null=True, blank=True)

    class Meta:
        verbose_name = _("Замовлення")
        verbose_name_plural = _("Замовлення")
        ordering = ['-created_at']

    def __str__(self):
        return f"Замовлення {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Генеруємо унікальний номер замовлення
            import uuid
            self.order_number = f"ES-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_("Замовлення"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Товар"))
    product_name = models.CharField(_("Назва товару"), max_length=255)  # Зберігаємо назву на момент замовлення
    quantity = models.PositiveIntegerField(_("Кількість"))
    price = models.DecimalField(_("Ціна за одиницю"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("Загальна вартість"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("Товар у замовленні")
        verbose_name_plural = _("Товари у замовленні")

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Автоматично обчислюємо загальну вартість
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name=_("Товар"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Користувач"))
    rating = models.PositiveIntegerField(_("Оцінка"), validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(_("Заголовок відгуку"), max_length=255)
    comment = models.TextField(_("Коментар"))
    is_verified_purchase = models.BooleanField(_("Підтверджена покупка"), default=False)
    is_approved = models.BooleanField(_("Схвалено"), default=False)
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Оновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Відгук")
        verbose_name_plural = _("Відгуки")
        ordering = ['-created_at']
        unique_together = ('product', 'user')  # Один відгук від користувача на товар

    def __str__(self):
        return f"{self.product.name} - {self.rating}/5 від {self.user.username}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Користувач"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Товар"))
    created_at = models.DateTimeField(_("Створено"), auto_now_add=True)

    class Meta:
        verbose_name = _("Список бажань")
        verbose_name_plural = _("Списки бажань")
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"