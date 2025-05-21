from django.shortcuts import render
from datetime import datetime
from .models import Section, News, GalleryItem, Partner,ContactInfo, Page
from django.shortcuts import get_object_or_404


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
    return render(request, 'core/gallery.html', {})

def news(request):
    return render(request, 'core/news.html', {})


def news_detail(request, slug):
    news_item = get_object_or_404(News, slug=slug, is_active=True)
    return render(request, 'core/news_detail.html', {'news': news_item})

def page_detail(request, slug):
    """
    Отображение конкретной страницы по ее slug.
    """
    page = get_object_or_404(Page, slug=slug, is_active=True)
    return render(request, 'core/page_detail.html', {'page': page})