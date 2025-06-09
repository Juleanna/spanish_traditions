from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include, re_path
from core import views  
from django.conf.urls.i18n import i18n_patterns
from ckeditor_uploader import views as ckeditor_views
urlpatterns = [
    path('rosetta/', include('rosetta.urls')),
       
]

urlpatterns += i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),  
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('shop/', include('shop.urls')), 
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact_page_view, name='contact_form'),
    path('news/', views.news_list, name='news'),
    path('accounts/', include('accounts.urls')),
    re_path(r'^news/(?P<slug>[\w\-]+)/$', views.news_detail, name='news_detail'),
    re_path(r'^(?P<slug>[\w\-]+)/$', views.page_detail, name='page_detail'),
    path("ckeditor/", include("ckeditor_uploader.urls")),  
    path('ckeditor/upload/', ckeditor_views.upload, name='ckeditor_upload'),
    path('ckeditor/browse/', ckeditor_views.browse, name='ckeditor_browse'),
    
)

if settings.DEBUG:  # Только в режиме отладки
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)