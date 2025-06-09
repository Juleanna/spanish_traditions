from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from shop.models import Order, OrderItem, Product, Wishlist, Cart, CartItem
from .forms import UserProfileForm, UserRegistrationForm, UserUpdateForm
from .models import UserProfile

@login_required
def profile_dashboard(request):
    """Головна сторінка особистого кабінету"""
    user_profile = request.user.profile
    
    # Останні замовлення
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Статистика
    stats = {
        'total_orders': Order.objects.filter(user=request.user).count(),
        'pending_orders': Order.objects.filter(user=request.user, status='pending').count(),
        'wishlist_count': Wishlist.objects.filter(user=request.user).count(),
        'cart_items': CartItem.objects.filter(
            cart__user=request.user
        ).aggregate(total=Sum('quantity'))['total'] or 0
    }
    
    context = {
        'user_profile': user_profile,
        'recent_orders': recent_orders,
        'stats': stats,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_settings(request):
    """Налаштування профілю"""
    user_profile = request.user.profile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Профіль успішно оновлено!'))
            return redirect('accounts:profile_settings')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile_settings.html', context)


@login_required
def change_password(request):
    """Зміна пароля"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Ваш пароль успішно змінено!'))
            
            # Для AJAX запитів
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('accounts:profile_dashboard')
        else:
            # Для AJAX запитів
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': form.errors.as_text()
                })
    else:
        form = PasswordChangeForm(request.user)
    
    # Додаємо CSS класи до полів форми
    form.fields['old_password'].widget.attrs['class'] = 'form-control'
    form.fields['new_password1'].widget.attrs['class'] = 'form-control'
    form.fields['new_password2'].widget.attrs['class'] = 'form-control'
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def product_comparison(request):
    """Порівняння товарів"""
    # Отримуємо ID товарів для порівняння з сесії
    comparison_ids = request.session.get('comparison_products', [])
    products = Product.objects.filter(id__in=comparison_ids).prefetch_related('images')
    
    # Групуємо характеристики для порівняння
    if products:
        # Тут можна додати логіку для витягування та групування характеристик товарів
        pass
    
    context = {
        'products': products,
    }
    return render(request, 'accounts/product_comparison.html', context)


@login_required
@require_POST
def add_to_comparison(request, product_id):
    """Додати товар до порівняння"""
    product = get_object_or_404(Product, id=product_id)
    comparison_products = request.session.get('comparison_products', [])
    
    if product_id not in comparison_products:
        if len(comparison_products) >= 4:  # Максимум 4 товари для порівняння
            return JsonResponse({
                'success': False,
                'message': _('Максимум 4 товари для порівняння')
            })
        
        comparison_products.append(product_id)
        request.session['comparison_products'] = comparison_products
        message = _('Товар додано до порівняння')
        success = True
    else:
        message = _('Товар вже у порівнянні')
        success = False
    
    return JsonResponse({
        'success': success,
        'message': str(message),
        'comparison_count': len(comparison_products)
    })


@login_required
@require_POST
def remove_from_comparison(request, product_id):
    """Видалити товар з порівняння"""
    comparison_products = request.session.get('comparison_products', [])
    
    if product_id in comparison_products:
        comparison_products.remove(product_id)
        request.session['comparison_products'] = comparison_products
        message = _('Товар видалено з порівняння')
        success = True
    else:
        message = _('Товар не знайдено у порівнянні')
        success = False
    
    return JsonResponse({
        'success': success,
        'message': str(message),
        'comparison_count': len(comparison_products)
    })


@login_required
def tracking_list(request):
    """Список відстежуваних товарів"""
    # Тут можна реалізувати функціонал відстеження товарів
    # Наприклад, товари, які користувач хоче відстежувати на наявність або зміну ціни
    
    context = {
        'tracked_products': [],  # Заглушка для майбутнього функціоналу
    }
    return render(request, 'accounts/tracking_list.html', context)


def register(request):
    """Реєстрація нового користувача"""
    if request.user.is_authenticated:
        return redirect('accounts:profile_dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            
            # Автоматичний вхід після реєстрації
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, _('Вітаємо! Ваш акаунт успішно створено.'))
            return redirect('shop:product_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """Вхід користувача"""
    if request.user.is_authenticated:
        return redirect('accounts:profile_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Якщо не вибрано "Запам'ятати мене", сесія закінчиться при закритті браузера
            if not remember_me:
                request.session.set_expiry(0)
            
            messages.success(request, _('Ви успішно увійшли!'))
            
            # Перенаправлення на сторінку, з якої прийшов користувач
            next_page = request.POST.get('next', request.GET.get('next', 'shop:product_list'))
            return redirect(next_page)
        else:
            messages.error(request, _('Невірне ім\'я користувача або пароль.'))
    
    return render(request, 'accounts/login.html')

def user_logout(request):
    """Вихід користувача"""
    logout(request)
    messages.info(request, _('Ви вийшли з акаунту.'))
    return redirect('shop:product_list')
    """Вихід користувача"""
    logout(request)
    messages.success(request, _('Ви успішно вийшли!'))
    return redirect('home')