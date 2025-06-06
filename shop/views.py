from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Min, Max
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
import json

from .models import (
    Category, Product, ProductImage, Cart, CartItem, 
    Order, OrderItem, Review, Wishlist
)
from .forms import ReviewForm, CheckoutForm


def product_list(request):
    """Список всіх товарів з фільтрацією та пагінацією"""
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.filter(is_active=True, parent__isnull=True)
    
    # Фільтрація
    category_slug = request.GET.get('category')
    search_query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'created_at')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
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
    
    # Отримуємо діапазон цін для фільтра
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Пагінація
    paginator = Paginator(products, 12)  # 12 товарів на сторінку
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'price_range': price_range,
        'current_sort': sort_by,
    }
    
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    """Детальна сторінка товару"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Зображення товару
    images = product.images.all().order_by('display_order')
    main_image = images.filter(is_main=True).first()
    if not main_image and images.exists():
        main_image = images.first()
    
    # Відгуки
    reviews = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
    
    # Схожі товари
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Перевіряємо, чи товар у списку бажань користувача
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Форма для відгуку
    review_form = ReviewForm()
    
    # Перевіряємо, чи користувач вже залишав відгук
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
    
    context = {
        'product': product,
        'main_image': main_image,
        'images': images,
        'reviews': reviews,
        'related_products': related_products,
        'is_in_wishlist': is_in_wishlist,
        'review_form': review_form,
        'user_review': user_review,
    }
    
    return render(request, 'shop/product_detail.html', context)


def category_detail(request, slug):
    """Сторінка категорії"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    
    # Підкategorії
    subcategories = category.children.filter(is_active=True)
    
    # Пагінація
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'subcategories': subcategories,
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
    """Додавання товару до кошика"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Перевіряємо наявність товару
        if product.track_stock and product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': _('Недостатньо товару на складі')
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
                    'message': _('Недостатньо товару на складі')
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': _('Товар додано до кошика'),
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при додаванні товару')
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


def checkout(request):
    """Оформлення замовлення"""
    cart = get_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items.exists():
        messages.warning(request, _('Ваш кошик порожній'))
        return redirect('shop:cart_detail')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
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
                shipping_cost=Decimal('50.00'),
                total_amount=cart.total_price + Decimal('50.00'),
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
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()
            
            # Очищуємо кошик
            cart_items.delete()
            
            # Відправляємо email підтвердження
            try:
                send_mail(
                    subject=f'Підтвердження замовлення {order.order_number}',
                    message=f'Дякуємо за ваше замовлення! Номер замовлення: {order.order_number}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[order.email],
                    fail_silently=True,
                )
            except:
                pass
            
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
    
    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'shipping_cost': Decimal('50.00'),
    }
    
    return render(request, 'shop/checkout.html', context)


def order_success(request, order_number):
    """Сторінка успішного оформлення замовлення"""
    order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_success.html', context)


@login_required
def order_list(request):
    """Список замовлень користувача"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'shop/order_list.html', context)


@login_required
def order_detail(request, order_number):
    """Детальна інформація про замовлення"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_detail.html', context)


@login_required
@require_POST
def add_to_wishlist(request):
    """Додавання товару до списку бажань"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return JsonResponse({
                'success': True,
                'message': _('Товар додано до списку бажань'),
                'action': 'added'
            })
        else:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'message': _('Товар видалено зі списку бажань'),
                'action': 'removed'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('Помилка при роботі зі списком бажань')
        })


@login_required
def wishlist(request):
    """Список бажань користувача"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    
    return render(request, 'shop/wishlist.html', context)


@login_required
@require_POST
def add_review(request, product_slug):
    """Додавання відгуку про товар"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Перевіряємо, чи користувач вже залишав відгук
    if Review.objects.filter(user=request.user, product=product).exists():
        messages.error(request, _('Ви вже залишили відгук для цього товару'))
        return redirect('shop:product_detail', slug=product_slug)
    
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        
        # Перевіряємо, чи користувач купував цей товар
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()
        review.is_verified_purchase = has_purchased
        
        review.save()
        
        # Оновлюємо рейтинг товару
        avg_rating = Review.objects.filter(product=product, is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        if avg_rating:
            product.rating = round(avg_rating, 2)
            product.reviews_count = Review.objects.filter(product=product, is_approved=True).count()
            product.save()
        
        messages.success(request, _('Відгук додано. Після модерації він з\'явиться на сайті.'))
    else:
        messages.error(request, _('Помилка при додаванні відгуку'))
    
    return redirect('shop:product_detail', slug=product_slug)


def search(request):
    """Пошук товарів"""
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').distinct()
    
    # Пагінація
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
        'total_results': products.count(),
    }
    
    return render(request, 'shop/search_results.html', context)