from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('catalog/<slug:slug>/', views.category_detail, name='category_detail'),
    path('catalog/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]

