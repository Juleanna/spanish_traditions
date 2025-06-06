from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Min, Max, F, Case, When, BooleanField
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from decimal import Decimal
import json

from .models import (
    Category, Product, ProductImage, Cart, CartItem, 
    Order, OrderItem, Review, Wishlist
)
from .forms import ReviewForm, CheckoutForm


def product_list(request):
    """Покращений список всіх товарів з фільтрацією та пагінацією"""
    
    # Базовий запит з оптимізацією
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'reviews')
    
    # Отримуємо категорії з кількістю товарів
    categories = Category.objects.filter(
        is_active=True, 
        parent__isnull=True
    ).annotate(
        products_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('display_order', 'name')
    
    # Параметри фільтрації
    category_slug = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'created_at')
    only_available = request.GET.get('available') == '1'
    only_featured = request.GET.get('featured') == '1'
    only_discounted = request.GET.get('discounted') == '1'
    
    # Фільтрація по категорії
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    
    # Пошук
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__name__icontains=search_query)
        ).distinct()
    
    # Фільтрація по ціні
    if min_price:
        try:
            min_price_decimal = Decimal(min_price)
            products = products.filter(
                Q(discount_price__gte=min_price_decimal) | 
                Q(discount_price__isnull=True, price__gte=min_price_decimal)
            )
        except (ValueError, TypeError):
            pass
    
    if max_price:
        try:
            max_price_decimal = Decimal(max_price)
            products = products.filter(
                Q(discount_price__lte=max_price_decimal) | 
                Q(discount_price__isnull=True, price__lte=max_price_decimal)
            )
        except (ValueError, TypeError):
            pass
    
    # Додаткові фільтри
    if only_available:
        products = products.filter(
            Q(track_stock=False, is_available=True) |
            Q(track_stock=True, stock__gt=0, is_available=True)
        )
    
    if only_featured:
        products = products.filter(is_featured=True)
    
    if only_discounted:
        products = products.filter(discount_price__isnull=False)
    
    # Анотуємо продукти додатковою інформацією
    products = products.annotate(
        # Актуальна ціна для сортування
        actual_price=Case(
            When(discount_price__isnull=False, then=F('discount_price')),
            default=F('price'),
            output_field=models.DecimalField()
        ),
        # Чи є товар в наявності
        in_stock=Case(
            When(track_stock=False, is_available=True, then=True),
            When(track_stock=True, stock__gt=0, is_available=True, then=True),
            default=False,
            output_field=BooleanField()
        ),
        # Середній рейтинг (оновлений)
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        # Кількість відгуків
        total_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
    )
    
    # Сортування
    sort_options = {
        'name': 'name',
        'price_low': 'actual_price',
        'price_high': '-actual_price',
        'rating': '-avg_rating',
        'created_at': '-created_at',
        'popularity': '-total_reviews'
    }
    
    if sort_by in sort_options:
        # Спочатку товари в наявності, потім сортування
        if sort_by in ['price_low', 'price_high']:
            products = products.order_by('-in_stock', sort_options[sort_by], 'name')
        else:
            products = products.order_by('-in_stock', sort_options[sort_by])
    else:
        products = products.order_by('-in_stock', '-created_at')
    
    # Отримуємо діапазон цін для фільтра
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=Min(
            Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price')
            )
        ),
        max_price=Max(
            Case(
                When(discount_price__isnull=False, then=F('discount_price')),
                default=F('price')
            )
        )
    )
    
    # Пагінація з адаптивною кількістю товарів
    items_per_page = 12
    if request.GET.get('per_page'):
        try:
            items_per_page = min(int(request.GET.get('per_page')), 48)  # Максимум 48
        except ValueError:
            pass
    
    paginator = Paginator(products, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Контекст для шаблону
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'price_range': price_range,
        'current_sort': sort_by,
        'filters': {
            'min_price': min_price,
            'max_price': max_price,
            'only_available': only_available,
            'only_featured': only_featured,
            'only_discounted': only_discounted,
        },
        'total_products': paginator.count,
        'items_per_page': items_per_page,
    }
    
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    """Покращена детальна сторінка товару"""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'reviews__user'),
        slug=slug, 
        is_active=True
    )
    
    # Зображення товару
    images = product.images.all().order_by('display_order')
    main_image = images.filter(is_main=True).first()
    if not main_image and images.exists():
        main_image = images.first()
    
    # Відгуки з пагінацією
    reviews = product.reviews.filter(
        is_approved=True
    ).select_related('user').order_by('-created_at')
    
    reviews_paginator = Paginator(reviews, 5)  # 5 відгуків на сторінку
    reviews_page = request.GET.get('reviews_page')
    reviews_page_obj = reviews_paginator.get_page(reviews_page)
    
    # Схожі товари (покращена логіка)
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id).annotate(
        in_stock=Case(
            When(track_stock=False, is_available=True, then=True),
            When(track_stock=True, stock__gt=0, is_available=True, then=True),
            default=False,
            output_field=BooleanField()
        )
    ).order_by('-in_stock', '-is_featured', '?')[:4]
    
    # Перевіряємо, чи товар у списку бажань користувача
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user, 
            product=product
        ).exists()
    
    # Форма для відгуку
    review_form = ReviewForm()
    
    # Перевіряємо, чи користувач вже залишав відгук
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    # Статистика відгуків
    review_stats = product.reviews.filter(is_approved=True).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id'),
        five_stars=Count('id', filter=Q(rating=5)),
        four_stars=Count('id', filter=Q(rating=4)),
        three_stars=Count('id', filter=Q(rating=3)),
        two_stars=Count('id', filter=Q(rating=2)),
        one_star=Count('id', filter=Q(rating=1)),
    )
    
    # Перевіряємо наявність товару
    is_in_stock = product.is_in_stock() if hasattr(product, 'is_in_stock') else (
        (not product.track_stock and product.is_available) or 
        (product.track_stock and product.stock > 0 and product.is_available)
    )
    
    context = {
        'product': product,
        'main_image': main_image,
        'images': images,
        'reviews': reviews_page_obj,
        'related_products': related_products,
        'is_in_wishlist': is_in_wishlist,
        'review_form': review_form,
        'user_review': user_review,
        'review_stats': review_stats,
        'is_in_stock': is_in_stock,
    }
    
    return render(request, 'shop/product_detail.html', context)


def category_detail(request, slug):
    """Покращена сторінка категорії"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Товари категорії з оптимізацією
    products = Product.objects.filter(
        category=category, 
        is_active=True
    ).select_related('category').prefetch_related('images').annotate(
        in_stock=Case(
            When(track_stock=False, is_available=True, then=True),
            When(track_stock=True, stock__gt=0, is_available=True, then=True),
            default=False,
            output_field=BooleanField()
        ),
        actual_price=Case(
            When(discount_price__isnull=False, then=F('discount_price')),
            default=F('price'),
            output_field=models.DecimalField()
        )
    ).order_by('-in_stock', '-is_featured', 'name')
    
    # Підкategорії
    subcategories = category.children.filter(is_active=True).annotate(
        products_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('display_order', 'name')
    
    # Сортування
    sort_by = request.GET.get('sort', 'created_at')
    sort_options = {
        'name': 'name',
        'price_low': 'actual_price',
        'price_high': '-actual_price',
        'rating': '-rating',
        'created_at': '-created_at'
    }
    
    if sort_by in sort_options:
        products = products.order_by('-in_stock', sort_options[sort_by])
    
    # Пагінація
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'subcategories': subcategories,
        'current_sort': sort_by,
    }
    
    return render(request, 'shop/category_detail.html', context)


def get_cart(request):
    """Отримуємо або створюємо кошик для користувача"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    return cart


@require_POST
def add_to_cart(request):
    """Покращене додавання товару до кошика"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': _('Некоректна кількість товару')
            })
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Перевіряємо наявність товару
        if not product.is_available:
            return JsonResponse({
                'success': False,
                'message': _('Товар недоступний для замовлення')
            })
        
        if product.track_stock and product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': _('Недостатньо товару на складі. Доступно: {} шт.').format(product.stock)
            })
        
        cart = get_cart(request)
        
        # Перевіряємо, чи товар вже є в кошику
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': product.get_price}
        )
        
        if not created:
            # Якщо товар вже є, збільшуємо кількість
            new_quantity = cart_item.quantity + quantity
            if product.track_stock and product.stock < new_quantity:
                return JsonResponse({
                    'success': False,
                    'message': _('Недостатньо товару на складі. У кошику: {} шт., доступно: {} шт.').format(
                        cart_item.quantity, product.stock
                    )
                })
            cart_item.quantity = new_quantity
            cart_item.price = product.get_price  # Оновлюємо ціну
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Товар додано до кошика'),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price),
            'item_quantity': cart_item.quantity
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при додаванні товару')
        })


def cart_detail(request):
    """Покращена сторінка кошика"""
    cart = get_cart(request)
    cart_items = cart.items.select_related('product__category').prefetch_related('product__images').all()
    
    # Перевіряємо наявність товарів у кошику
    unavailable_items = []
    for item in cart_items:
        if not item.product.is_available or (
            item.product.track_stock and item.product.stock < item.quantity
        ):
            unavailable_items.append(item)
    
    # Рекомендовані товари для кошика
    if cart_items.exists():
        categories = set(item.product.category for item in cart_items)
        recommended_products = Product.objects.filter(
            category__in=categories,
            is_active=True,
            is_available=True
        ).exclude(
            id__in=[item.product.id for item in cart_items]
        ).annotate(
            in_stock=Case(
                When(track_stock=False, is_available=True, then=True),
                When(track_stock=True, stock__gt=0, is_available=True, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).filter(in_stock=True).order_by('-is_featured', '?')[:4]
    else:
        recommended_products = []
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'unavailable_items': unavailable_items,
        'recommended_products': recommended_products,
        'shipping_cost': Decimal('50.00'),  # Можна зробити динамічним
    }
    
    return render(request, 'shop/cart_detail.html', context)


@require_POST
def update_cart_item(request):
    """Покращене оновлення кількості товару в кошику"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity'))
        
        cart = get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'message': _('Товар видалено з кошика'),
                'cart_total_items': cart.total_items,
                'cart_total_price': float(cart.total_price),
                'item_removed': True
            })
        
        # Перевіряємо наявність товару
        if not cart_item.product.is_available:
            return JsonResponse({
                'success': False,
                'message': _('Товар більше недоступний')
            })
        
        if cart_item.product.track_stock and cart_item.product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': _('Недостатньо товару на складі. Доступно: {} шт.').format(
                    cart_item.product.stock
                )
            })
        
        cart_item.quantity = quantity
        cart_item.price = cart_item.product.get_price  # Оновлюємо ціну
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Кошик оновлено'),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price),
            'item_total_price': float(cart_item.total_price),
            'item_quantity': cart_item.quantity
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при оновленні кошика')
        })


@require_POST
def remove_from_cart(request):
    """Покращене видалення товару з кошика"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart = get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product_name = cart_item.product.name
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': _('"{}" видалено з кошика').format(product_name),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при видаленні товару')
        })


def checkout(request):
    """Покращене оформлення замовлення"""
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items.exists():
        messages.warning(request, _('Ваш кошик порожній'))
        return redirect('shop:cart_detail')
    
    # Перевіряємо наявність всіх товарів
    unavailable_items = []
    for item in cart_items:
        if not item.product.is_available or (
            item.product.track_stock and item.product.stock < item.quantity
        ):
            unavailable_items.append(item)
    
    if unavailable_items:
        for item in unavailable_items:
            messages.error(
                request, 
                _('Товар "{}" недоступний у потрібній кількості').format(item.product.name)
            )
        return redirect('shop:cart_detail')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Ще раз перевіряємо наявність перед створенням замовлення
            for item in cart_items:
                if item.product.track_stock and item.product.stock < item.quantity:
                    messages.error(
                        request,
                        _('Товар "{}" більше недоступний у потрібній кількості').format(
                            item.product.name
                        )
                    )
                    return redirect('shop:cart_detail')
            
            # Розрахунок вартості доставки (можна зробити динамічним)
            shipping_cost = Decimal('50.00')
            if cart.total_price >= Decimal('1000.00'):  # Безкоштовна доставка від 1000 грн
                shipping_cost = Decimal('0.00')
            
            # Створюємо замовлення
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                address_line1=form.cleaned_data['address_line1'],
                address_line2=form.cleaned_data['address_line2'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                postal_code=form.cleaned_data['postal_code'],
                country=form.cleaned_data['country'],
                subtotal=cart.total_price,
                shipping_cost=shipping_cost,
                total_amount=cart.total_price + shipping_cost,
                notes=form.cleaned_data.get('notes', '')
            )
            
            # Створюємо елементи замовлення
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    price=cart_item.price
                )
                
                # Зменшуємо кількість на складі
                if cart_item.product.track_stock:
                    cart_item.product.stock = F('stock') - cart_item.quantity
                    cart_item.product.save(update_fields=['stock'])
            
            # Очищуємо кошик
            cart_items.delete()
            
            # Відправляємо email підтвердження
            try:
                send_mail(
                    subject=f'Підтвердження замовлення {order.order_number}',
                    message=f'Дякуємо за ваше замовлення!\n\nНомер замовлення: {order.order_number}\nСума: {order.total_amount} ₴\n\nМи зв\'яжемося з вами найближчим часом.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.email],
                    fail_silently=True,
                )
            except:
                pass  # Не зупиняємо процес при помилці відправки email
            
            messages.success(request, _('Замовлення успішно оформлено!'))
            return redirect('shop:order_success', order_number=order.order_number)
    else:
        # Попередньо заповнюємо форму даними користувача
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        form = CheckoutForm(initial=initial_data)
    
    # Розрахунок вартості доставки для відображення
    shipping_cost = Decimal('50.00')
    free_shipping_threshold = Decimal('1000.00')
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'shipping_cost': shipping_cost,
        'free_shipping_threshold': free_shipping_threshold,
        'amount_for_free_shipping': max(Decimal('0'), free_shipping_threshold - cart.total_price),
    }
    
    return render(request, 'shop/checkout.html', context)


def search(request):
    """Покращений пошук товарів"""
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    
    if query and len(query) >= 2:  # Мінімум 2 символи для пошуку
        # Розширений пошук з вагою релевантності
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__icontains=query),
            is_active=True
        ).select_related('category').prefetch_related('images').annotate(
            # Додаємо поле релевантності (простий варіант)
            relevance=Case(
                When(name__iexact=query, then=10),
                When(name__icontains=query, then=8),
                When(short_description__icontains=query, then=6),
                When(brand__icontains=query, then=5),
                When(category__name__icontains=query, then=4),
                When(description__icontains=query, then=3),
                default=1
            ),
            in_stock=Case(
                When(track_stock=False, is_available=True, then=True),
                When(track_stock=True, stock__gt=0, is_available=True, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).distinct().order_by('-in_stock', '-relevance', '-is_featured', 'name')
    
    # Сортування
    sort_by = request.GET.get('sort', 'relevance')
    if sort_by and products.exists():
        sort_options = {
            'relevance': '-relevance',
            'name': 'name',
            'price_low': 'price',
            'price_high': '-price',
            'rating': '-rating',
            'created_at': '-created_at'
        }
        
        if sort_by in sort_options:
            products = products.order_by('-in_stock', sort_options[sort_by])
    
    # Пагінація
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Пропозиції для пошуку (якщо немає результатів)
    suggestions = []
    if not products.exists() and query:
        # Простий алгоритм пропозицій
        all_products = Product.objects.filter(is_active=True).values_list('name', flat=True)[:100]
        for product_name in all_products:
            if query.lower() in product_name.lower():
                suggestions.append(product_name)
                if len(suggestions) >= 5:
                    break
    
    context = {
        'products': page_obj,
        'query': query,
        'total_results': products.count() if products else 0,
        'current_sort': sort_by,
        'suggestions': suggestions,
    }
    
    return render(request, 'shop/search_results.html', context)