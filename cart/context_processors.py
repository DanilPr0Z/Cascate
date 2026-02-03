from .models import Cart


def cart_processor(request):
    """Передает данные корзины во все шаблоны"""
    cart_count = 0
    cart = None

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            pass

    return {
        'cart': cart,
        'cart_count': cart_count,
    }
