from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('catalog/<slug:slug>/', views.category_detail, name='category_detail'),
    path('catalog/<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('rate-product/<int:product_id>/', views.rate_product, name='rate_product'),
    path('ajax/form_demo/', views.form_demo, name='form_demo'),
]

