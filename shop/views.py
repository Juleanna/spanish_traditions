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


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http import HttpResponseRedirect
from django.urls import reverse

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

    # Отримуємо список товарів у wishlist для поточного користувача
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))
    
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
        'wishlist_product_ids': wishlist_product_ids,
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

@login_required
def order_success(request, order_number):
    """Сторінка успішного оформлення замовлення"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Перевіряємо, чи користувач має доступ до цього замовлення
    if order.user != request.user and not request.user.is_staff:
        if not order.email == request.user.email:
            messages.error(request, _('Ви не маєте доступу до цього замовлення'))
            return redirect('shop:order_list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_success.html', context)


@login_required
def order_list(request):
    """Список замовлень користувача"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Пагінація
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
    }
    
    return render(request, 'shop/order_list.html', context)


@login_required
def order_detail(request, order_number):
    """Детальна інформація про замовлення"""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        order_number=order_number
    )
    
    # Перевіряємо доступ
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, _('Ви не маєте доступу до цього замовлення'))
        return redirect('shop:order_list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_detail.html', context)


@login_required
@require_POST
def cancel_order(request, order_number):
    """Скасування замовлення"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.status not in ['pending', 'confirmed']:
        messages.error(request, _('Це замовлення не можна скасувати'))
        return redirect('shop:order_detail', order_number=order_number)
    
    # Повертаємо товари на склад
    for item in order.items.all():
        if item.product.track_stock:
            item.product.stock = F('stock') + item.quantity
            item.product.save(update_fields=['stock'])
    
    # Оновлюємо статус замовлення
    order.status = 'cancelled'
    order.save()
    
    messages.success(request, _('Замовлення успішно скасовано'))
    return redirect('shop:order_detail', order_number=order_number)


@login_required
def wishlist(request):
    """Список бажань користувача"""
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product__category').prefetch_related('product__images')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    
    return render(request, 'shop/wishlist.html', context)


@login_required
@require_POST
def add_to_wishlist(request):
    """Додавання/видалення товару зі списку бажань"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'message': _('Товар видалено зі списку бажань'),
                'action': 'removed'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': _('Товар додано до списку бажань'),
                'action': 'added'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при роботі зі списком бажань')
        })


@login_required
@require_POST
def remove_from_wishlist(request):
    """Видалення товару зі списку бажань"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        wishlist_item = get_object_or_404(
            Wishlist, 
            user=request.user, 
            product_id=product_id
        )
        
        wishlist_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': _('Товар видалено зі списку бажань')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })


@login_required
@require_POST
def clear_wishlist(request):
    """Очищення списку бажань"""
    Wishlist.objects.filter(user=request.user).delete()
    
    return JsonResponse({
        'success': True,
        'message': _('Список бажань очищено')
    })


@login_required
@require_POST
def add_review(request, product_slug):
    """Додавання відгуку до товару"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Перевіряємо, чи користувач вже залишав відгук
    existing_review = Review.objects.filter(
        product=product, 
        user=request.user
    ).first()
    
    if existing_review:
        messages.error(request, _('Ви вже залишили відгук для цього товару'))
        return redirect('shop:product_detail', slug=product_slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            
            # Перевіряємо, чи користувач купував цей товар
            has_purchased = OrderItem.objects.filter(
                order__user=request.user,
                product=product,
                order__status='delivered'
            ).exists()
            
            review.is_verified_purchase = has_purchased
            review.save()
            
            messages.success(request, _('Відгук додано. Після модерації він з\'явиться на сайті.'))
        else:
            messages.error(request, _('Помилка при додаванні відгуку'))
    
    return redirect('shop:product_detail', slug=product_slug)


@login_required
@require_POST
def edit_review(request, review_id):
    """Редагування відгуку"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.is_approved = False  # Потребує повторної модерації
            review.save()
            
            messages.success(request, _('Відгук оновлено. Після модерації він з\'явиться на сайті.'))
        else:
            messages.error(request, _('Помилка при оновленні відгуку'))
    
    return redirect('shop:product_detail', slug=review.product.slug)


@login_required
@require_POST
def delete_review(request, review_id):
    """Видалення відгуку"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_slug = review.product.slug
    review.delete()
    
    messages.success(request, _('Відгук видалено'))
    return redirect('shop:product_detail', slug=product_slug)


@require_POST
def clear_cart(request):
    """Очищення кошика"""
    cart = get_cart(request)
    cart.items.all().delete()
    
    return JsonResponse({
        'success': True,
        'message': _('Кошик очищено')
    })


def search_autocomplete(request):
    """Автозаповнення для пошуку"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query and len(query) >= 2:
        # Шукаємо товари
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(brand__icontains=query),
            is_active=True
        ).values('name', 'slug')[:10]
        
        for product in products:
            results.append({
                'type': 'product',
                'name': product['name'],
                'url': reverse('shop:product_detail', kwargs={'slug': product['slug']})
            })
        
        # Шукаємо категорії
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        ).values('name', 'slug')[:5]
        
        for category in categories:
            results.append({
                'type': 'category',
                'name': category['name'],
                'url': reverse('shop:category_detail', kwargs={'slug': category['slug']})
            })
    
    return JsonResponse({'results': results})


def compare_products(request):
    """Порівняння товарів"""
    compare_ids = request.session.get('compare_products', [])
    products = Product.objects.filter(
        id__in=compare_ids, 
        is_active=True
    ).select_related('category').prefetch_related('images')
    
    # Групуємо характеристики для порівняння
    comparison_data = {}
    for product in products:
        comparison_data[product.id] = {
            'product': product,
            'specs': {
                'Ціна': product.get_price,
                'Категорія': product.category.name,
                'Бренд': product.brand or '-',
                'Країна': product.country_origin or '-',
                'Вага': f"{product.weight} кг" if product.weight else '-',
                'Об\'єм': f"{product.volume} л" if product.volume else '-',
                'Рейтинг': f"{product.rating}/5" if product.rating else '-',
                'В наявності': 'Так' if product.is_in_stock() else 'Ні',
            }
        }
    
    context = {
        'products': products,
        'comparison_data': comparison_data,
    }
    
    return render(request, 'shop/compare.html', context)


@require_POST
def add_to_compare(request):
    """Додавання товару до порівняння"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        compare_products = request.session.get('compare_products', [])
        
        if product_id in compare_products:
            return JsonResponse({
                'success': False,
                'message': _('Товар вже додано до порівняння')
            })
        
        if len(compare_products) >= 4:
            return JsonResponse({
                'success': False,
                'message': _('Максимум 4 товари для порівняння')
            })
        
        compare_products.append(product_id)
        request.session['compare_products'] = compare_products
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': _('Товар додано до порівняння'),
            'count': len(compare_products)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })


@require_POST
def remove_from_compare(request):
    """Видалення товару з порівняння"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        compare_products = request.session.get('compare_products', [])
        
        if product_id in compare_products:
            compare_products.remove(product_id)
            request.session['compare_products'] = compare_products
            request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': _('Товар видалено з порівняння'),
            'count': len(compare_products)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })


@require_POST
def clear_compare(request):
    """Очищення списку порівняння"""
    request.session['compare_products'] = []
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'message': _('Список порівняння очищено')
    })


def check_product_stock(request, product_id):
    """Перевірка наявності товару (API)"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        return JsonResponse({
            'success': True,
            'in_stock': product.is_in_stock(),
            'stock': product.stock if product.track_stock else None,
            'available': product.is_available
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Товар не знайдено')
        })


def get_cart_count(request):
    """Отримання кількості товарів в кошику (API)"""
    cart = get_cart(request)
    
    return JsonResponse({
        'success': True,
        'count': cart.total_items,
        'total_price': float(cart.total_price)
    })


@require_POST
def calculate_shipping(request):
    """Розрахунок вартості доставки (API)"""
    try:
        data = json.loads(request.body)
        city = data.get('city')
        total_amount = Decimal(data.get('total_amount', 0))
        
        # Проста логіка розрахунку доставки
        if total_amount >= 1000:
            shipping_cost = 0
        elif city and city.lower() in ['київ', 'kyiv']:
            shipping_cost = 30
        else:
            shipping_cost = 50
        
        return JsonResponse({
            'success': True,
            'shipping_cost': shipping_cost,
            'free_shipping_threshold': 1000
        })
        
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            'success': False,
            'message': _('Некоректні дані')
        })


def product_quick_view(request, product_id):
    """Швидкий перегляд товару (для модального вікна)"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Базова інформація для швидкого перегляду
    data = {
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'description': product.short_description,
            'price': float(product.price),
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'in_stock': product.is_in_stock(),
            'category': product.category.name,
            'brand': product.brand,
            'rating': float(product.rating) if product.rating else None,
            'images': [
                {'url': img.image.url, 'alt': img.alt_text}
                for img in product.images.all()[:3]
            ]
        }
    }
    
    return JsonResponse(data)


def filter_products_ajax(request):
    """AJAX фільтрація товарів"""
    # Отримуємо параметри фільтрації
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    brands = request.GET.getlist('brand')
    in_stock = request.GET.get('in_stock') == 'true'
    sort_by = request.GET.get('sort', 'created_at')
    
    # Базовий запит
    products = Product.objects.filter(is_active=True)
    
    # Застосовуємо фільтри
    if category_id:
        products = products.filter(category_id=category_id)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    if brands:
        products = products.filter(brand__in=brands)
    
    if in_stock:
        products = products.filter(
            Q(track_stock=False, is_available=True) |
            Q(track_stock=True, stock__gt=0, is_available=True)
        )
    
    # Сортування
    sort_options = {
        'name': 'name',
        'price_low': 'price',
        'price_high': '-price',
        'rating': '-rating',
        'created_at': '-created_at'
    }
    
    if sort_by in sort_options:
        products = products.order_by(sort_options[sort_by])
    
    # Пагінація
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Формуємо відповідь
    products_data = []
    for product in page_obj:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image': product.images.first().image.url if product.images.exists() else None,
            'rating': float(product.rating) if product.rating else None,
            'in_stock': product.is_in_stock(),
            'is_featured': product.is_featured,
            'url': product.get_absolute_url()
        })
    
    return JsonResponse({
        'success': True,
        'products': products_data,
        'total_count': paginator.count,
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous()
    })


@require_POST
def validate_coupon(request):
    """Валідація промокоду"""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip()
        
        # Тут можна додати логіку валідації промокодів
        # Наразі просто демонстраційний код
        valid_coupons = {
            'SAVE10': {'discount': 10, 'type': 'percentage'},
            'SAVE50': {'discount': 50, 'type': 'fixed'},
            'FREESHIP': {'discount': 0, 'type': 'free_shipping'}
        }
        
        if coupon_code.upper() in valid_coupons:
            coupon = valid_coupons[coupon_code.upper()]
            return JsonResponse({
                'success': True,
                'message': _('Промокод застосовано'),
                'discount': coupon['discount'],
                'type': coupon['type']
            })
        else:
            return JsonResponse({
                'success': False,
                'message': _('Недійсний промокод')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _('Некоректний формат даних')
        })


def track_order(request, order_number):
    """Відстеження замовлення"""
    try:
        order = Order.objects.get(order_number=order_number)
        
        # Дозволяємо відстеження без входу, якщо є email
        if request.method == 'POST':
            email = request.POST.get('email')
            if email == order.email:
                context = {
                    'order': order,
                    'tracking_allowed': True
                }
                return render(request, 'shop/track_order.html', context)
            else:
                messages.error(request, _('Невірний email'))
        
        context = {
            'order_number': order_number,
            'tracking_allowed': False
        }
        
    except Order.DoesNotExist:
        messages.error(request, _('Замовлення не знайдено'))
        return redirect('shop:product_list')
    
    return render(request, 'shop/track_order.html', context)


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


def cart_data_api(request):
    """API для отримання даних кошика для віджета"""
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').prefetch_related('product__images').all()
    
    items_data = []
    for item in cart_items:
        # Отримуємо перше зображення товару
        image_url = None
        if item.product.images.exists():
            image_url = item.product.images.first().image.url
        elif hasattr(item.product, 'image') and item.product.image:
            image_url = item.product.image.url
            
        items_data.append({
            'id': item.id,
            'product_id': item.product.id,  # ДОДАНО: ID товару
            'name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
            'total_price': float(item.total_price),
            'image': image_url,
            'url': item.product.get_absolute_url() if hasattr(item.product, 'get_absolute_url') else '#',  # ДОДАНО: посилання на товар
        })
    
    return JsonResponse({
        'success': True,  # ДОДАНО: індикатор успіху
        'total_items': cart.total_items,
        'total_price': float(cart.total_price),
        'items': items_data,
        'cart_id': cart.id,  # ДОДАНО: ID корзини
    })

@require_POST
def add_to_cart(request):
    """Додавання товару до кошика"""
    try:
        # Підтримуємо як JSON, так і FormData
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'message': _('Не вказано товар')
            })
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Перевіряємо наявність товару
        if product.track_stock and product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': _('Недостатньо товару на складі. Доступно: ') + str(product.stock)
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
                    'message': _('Недостатньо товару на складі. Доступно: ') + str(product.stock)
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # ВИПРАВЛЕННЯ: Оновлюємо дані корзини після додавання
        cart.refresh_from_db()
        
        # Отримуємо оновлені дані корзини для віджета
        cart_items = cart.items.select_related('product').prefetch_related('product__images').all()
        items_data = []
        for item in cart_items:
            image_url = None
            if item.product.images.exists():
                image_url = item.product.images.first().image.url
            elif hasattr(item.product, 'image') and item.product.image:
                image_url = item.product.image.url
                
            items_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'name': item.product.name,
                'quantity': item.quantity,
                'price': float(item.price),
                'total_price': float(item.total_price),
                'image': image_url,
            })
        
        return JsonResponse({
            'success': True,
            'message': _('Товар додано до кошика'),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price),
            'cart_items': items_data,  # ДОДАНО: список товарів для оновлення dropdown
            'added_product': {
                'id': product.id,
                'name': product.name,
                'quantity': quantity
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': _('Неправильний формат даних')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при додаванні товару: ') + str(e)
        })

def cart_detail(request):
    """Сторінка кошика"""
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    
    return render(request, 'shop/cart_detail.html', context)


@require_POST
def update_cart_item(request):
    """Оновлення кількості товару в кошику"""
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
                'cart_total_price': float(cart.total_price)
            })
        
        # Перевіряємо наявність товару
        if cart_item.product.track_stock and cart_item.product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': _('Недостатньо товару на складі')
            })
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Кошик оновлено'),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price),
            'item_total_price': float(cart_item.total_price)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при оновленні кошика')
        })


@require_POST
def remove_from_cart(request):
    """Видалення товару з кошика"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart = get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': _('Товар видалено з кошика'),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при видаленні товару')
        })

def cart_detail(request):
    """Детальна сторінка кошика"""
    cart = get_cart(request)
    cart_items = cart.items.select_related('product__category').prefetch_related('product__images').all()
    
    # Отримуємо рекомендовані товари
    related_products = []
    if cart_items:
        # Збираємо категорії товарів у кошику
        categories = set()
        for item in cart_items:
            categories.add(item.product.category)
        
        # Отримуємо товари з тих же категорій
        cart_product_ids = [item.product.id for item in cart_items]
        related_products = Product.objects.filter(
            category__in=categories,
            is_active=True,
            is_available=True
        ).exclude(
            id__in=cart_product_ids
        ).select_related('category').prefetch_related('images').order_by('?')[:8]
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'related_products': related_products,
    }
    
    return render(request, 'shop/cart_detail.html', context)