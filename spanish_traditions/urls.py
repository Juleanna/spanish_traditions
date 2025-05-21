from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include, re_path
from core import views  
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('gallery/', views.gallery, name='gallery'),
    path('news/', views.news, name='news'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^news/(?P<slug>[\w\-]+)/$', views.news_detail, name='news_detail'),
    re_path(r'^(?P<slug>[\w\-]+)/$', views.page_detail, name='page_detail'),
]

if settings.DEBUG:  # Только в режиме отладки
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)