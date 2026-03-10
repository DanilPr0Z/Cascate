from .models import Cart


def cart_processor(request):
    """Передает данные корзины во все шаблоны"""
    cart_count = 0
    cart = None

    if request.user.is_authenticated:
        # Для авторизованных пользователей
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            pass
    elif request.session.session_key:
        # Для анонимных пользователей с активной сессией
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            pass

    return {
        'cart': cart,
        'cart_count': cart_count,
    }
