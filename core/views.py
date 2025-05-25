from django.shortcuts import render
from datetime import datetime
from .models import Section, News, GalleryItem, Partner,ContactInfo, Page
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail

def home(request):
    sections = Section.objects.filter(is_active=True).prefetch_related('cards').order_by('display_order')
    latest_news = News.objects.filter(is_active=True).order_by('-published_date')[:4]
    latest_photos = GalleryItem.objects.filter(is_active=True).order_by('-created_at')[:6]
    partners = Partner.objects.filter(is_active=True).order_by('display_order')[:4]
    contact_info = ContactInfo.objects.filter(is_active=True).first()
    return render(request, 'core/home.html', {
        'year': datetime.now().year,
        'sections': sections,
        'latest_news': latest_news,
        'latest_photos': latest_photos,
        'partners': partners,
        'contact_info': contact_info,
    })


def gallery(request):
    images = GalleryItem.objects.all()
    return render(request, 'core/gallery.html', {'images': images})


def news_list(request):
    news = News.objects.filter(is_active=True).order_by('-published_date') 
    return render(request, 'core/news/news.html', {'news': news})


def news_detail(request, slug):
    news_item = get_object_or_404(News, slug=slug, is_active=True)  
    return render(request, 'core/news/news_detail.html', {'news_item': news_item})

def page_detail(request, slug):
    """
    Отображение конкретной страницы по ее slug.
    """
    page = get_object_or_404(Page, slug=slug, is_active=True)
    return render(request, 'core/page_detail.html', {'page': page})


def contact_page_view(request):
    success_message = None  # Сообщение об успехе или ошибке

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
        
        if name and email and message:
            try:
                send_mail(
                    subject=f"Новое сообщение от {name}",
                    message=f"Имя: {name}\nEmail: {email}\nТелефон: {phone}\nСообщение:\n{message}",
                    from_email=email,
                    recipient_list=['your_email@gmail.com'],  # Ваш email
                )
                success_message = "Ваше сообщение успешно отправлено!"
            except Exception as e:
                success_message = f"Ошибка при отправке сообщения: {str(e)}"
        else:
            success_message = "Все поля должны быть заполнены!"
    
    return render(request, "core/contact_page.html", {'success_message': success_message})

