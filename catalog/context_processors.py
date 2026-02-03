from .models import Category


def categories_processor(request):
    """
    Контекст-процессор для передачи всех категорий с подкатегориями во все шаблоны
    """
    categories = Category.objects.prefetch_related('subcategories').order_by('order')
    return {
        'all_categories': categories
    }