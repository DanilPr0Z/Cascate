from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from .models import Category, Product, SubCategory, FilterCategory, FilterValue


def catalog_view(request):
    """Главная страница каталога со всеми категориями"""
    categories = Category.objects.all().annotate(
        products_count=Count('products')
    )
    context = {
        'categories': categories,
    }
    return render(request, 'catalog/catalog.html', context)


def category_detail(request, slug):
    """Страница категории с товарами и фильтрами"""
    category = get_object_or_404(Category, slug=slug)
    
    # Получаем все фильтры
    filter_categories = FilterCategory.objects.prefetch_related('values').all()
    
    # Фильтрация по подкатегории, если указана
    subcategory_slug = request.GET.get('subcategory')
    products = Product.objects.filter(category=category)
    if subcategory_slug:
        try:
            subcategory = SubCategory.objects.get(category=category, slug=subcategory_slug)
            products = products.filter(subcategory=subcategory)
        except SubCategory.DoesNotExist:
            pass
    
    # Применяем фильтры
    filter_params = request.GET.getlist('filter')
    if filter_params:
        products = products.filter(filter_values__slug__in=filter_params).distinct()
    
    # Фильтр по наличию
    availability = request.GET.get('availability')
    if availability:
        products = products.filter(availability=availability)
    
    # Поиск
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(materials__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', 'availability')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:  # availability
        products = products.order_by('-availability', 'name')
    
    # Подсчет товаров по категориям фильтров (для текущей выборки)
    # Используем базовую выборку с учетом подкатегории
    base_products = Product.objects.filter(category=category)
    if subcategory_slug:
        try:
            subcategory = SubCategory.objects.get(category=category, slug=subcategory_slug)
            base_products = base_products.filter(subcategory=subcategory)
        except SubCategory.DoesNotExist:
            pass
    
    filter_stats = {}
    for filter_cat in filter_categories:
        filter_stats[filter_cat.slug] = {
            'category': filter_cat,
            'values': []
        }
        for value in filter_cat.values.all():
            # Подсчитываем для товаров текущей подкатегории
            count = base_products.filter(filter_values=value).count()
            if count > 0:
                filter_stats[filter_cat.slug]['values'].append({
                    'value': value,
                    'count': count,
                    'is_active': value.slug in filter_params
                })
    
    # Получаем подкатегории для фильтрации
    # Считаем только товары, где category товара совпадает с category подкатегории
    subcategories = SubCategory.objects.filter(category=category).annotate(
        products_count=Count('products', filter=Q(products__category=category))
    )
    
    context = {
        'category': category,
        'products': products,
        'filter_categories': filter_categories,
        'filter_stats': filter_stats,
        'current_filters': filter_params,
        'availability_filter': availability,
        'search_query': search_query,
        'sort_by': sort_by,
        'subcategories': subcategories,
        'selected_subcategory': subcategory_slug,
    }
    return render(request, 'catalog/category_detail.html', context)


def subcategory_detail(request, category_slug, subcategory_slug):
    """Страница подкатегории"""
    category = get_object_or_404(Category, slug=category_slug)
    subcategory = get_object_or_404(SubCategory, category=category, slug=subcategory_slug)
    
    products = Product.objects.filter(subcategory=subcategory)
    
    # Аналогичная логика фильтров как в category_detail
    filter_categories = FilterCategory.objects.prefetch_related('values').all()
    
    filter_params = request.GET.getlist('filter')
    if filter_params:
        products = products.filter(filter_values__slug__in=filter_params).distinct()
    
    availability = request.GET.get('availability')
    if availability:
        products = products.filter(availability=availability)
    
    sort_by = request.GET.get('sort', 'availability')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-availability', 'name')
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'products': products,
        'filter_categories': filter_categories,
        'current_filters': filter_params,
        'availability_filter': availability,
        'sort_by': sort_by,
    }
    return render(request, 'catalog/subcategory_detail.html', context)


def product_detail(request, slug):
    """Детальная страница товара"""
    product = get_object_or_404(Product.objects.prefetch_related('images', 'filter_values'), slug=slug)

    # Увеличиваем счетчик просмотров
    product.views_count += 1
    product.save(update_fields=['views_count'])

    # Похожие товары - сначала пытаемся найти из той же подкатегории
    related_products = None
    if product.subcategory:
        # Если есть подкатегория, берем товары из нее
        related_products = Product.objects.filter(
            subcategory=product.subcategory
        ).exclude(id=product.id)[:4]

    # Если нет подкатегории или нашлось мало товаров, берем из категории
    if not related_products or related_products.count() < 4:
        related_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'catalog/product_detail.html', context)

