// Функционал корзины

// CSRF Token для Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Добавить товар в корзину
function addToCart(productId, buttonElement) {
    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновить счетчик корзины
            updateCartCount(data.cart_count);

            // Визуальная обратная связь
            if (buttonElement) {
                const originalText = buttonElement.textContent;
                const originalBg = buttonElement.style.backgroundColor;

                buttonElement.textContent = 'ДОБАВЛЕНО!';
                buttonElement.style.backgroundColor = '#28a745';

                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.style.backgroundColor = originalBg;
                }, 2000);
            }

            // Показать уведомление
            showNotification(data.message, 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка при добавлении товара', 'error');
    });
}

// Обновить счетчик корзины в навигации
function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        cartBadge.textContent = count;
        if (count > 0) {
            cartBadge.style.display = 'flex';
        } else {
            cartBadge.style.display = 'none';
        }
    } else if (count > 0) {
        // Создать badge если его нет
        const cartIcon = document.querySelector('.cart-icon');
        if (cartIcon) {
            const badge = document.createElement('span');
            badge.className = 'cart-badge';
            badge.textContent = count;
            cartIcon.appendChild(badge);
        }
    }
}

// Показать уведомление
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.classList.add('show'), 10);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Удалить товар из корзины
function removeFromCart(itemId) {
    const modal = document.getElementById('deleteModal');
    const confirmBtn = document.getElementById('confirmDelete');
    const cancelBtn = document.getElementById('cancelDelete');

    // Показать модальное окно
    modal.classList.add('show');

    // Обработчик подтверждения
    const handleConfirm = function() {
        modal.classList.remove('show');

        fetch(`/cart/remove/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Удалить строку из таблицы
                const row = document.querySelector(`#cart-item-${itemId}`);
                if (row) {
                    row.remove();
                }

                // Обновить итоги
                updateCartCount(data.cart_count);
                updateCartTotal(data.total_price);

                // Если корзина пуста - перезагрузить страницу
                if (data.cart_count === 0) {
                    location.reload();
                }

                showNotification('Товар удален из корзины', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Ошибка при удалении товара', 'error');
        });

        // Удалить обработчики
        confirmBtn.removeEventListener('click', handleConfirm);
        cancelBtn.removeEventListener('click', handleCancel);
        modal.removeEventListener('click', handleOutsideClick);
    };

    // Обработчик отмены
    const handleCancel = function() {
        modal.classList.remove('show');
        confirmBtn.removeEventListener('click', handleConfirm);
        cancelBtn.removeEventListener('click', handleCancel);
        modal.removeEventListener('click', handleOutsideClick);
    };

    // Обработчик клика вне модального окна
    const handleOutsideClick = function(e) {
        if (e.target === modal) {
            handleCancel();
        }
    };

    // Добавить обработчики
    confirmBtn.addEventListener('click', handleConfirm);
    cancelBtn.addEventListener('click', handleCancel);
    modal.addEventListener('click', handleOutsideClick);
}

// Изменить количество
function updateQuantity(itemId, quantity) {
    const formData = new FormData();
    formData.append('quantity', quantity);

    fetch(`/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        },
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновить сумму товара
            const itemTotalElement = document.querySelector(`#item-total-${itemId}`);
            if (itemTotalElement) {
                itemTotalElement.textContent = `${formatPrice(data.item_total)} ₽`;
            }

            // Обновить общие итоги
            updateCartCount(data.cart_count);
            updateCartTotal(data.total_price);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка при обновлении количества', 'error');
    });
}

// Обновить общую сумму
function updateCartTotal(totalPrice) {
    const totalElement = document.querySelector('.cart-total-price');
    if (totalElement) {
        totalElement.textContent = `${formatPrice(totalPrice)} ₽`;
    }
}

// Форматировать цену
function formatPrice(price) {
    return Math.round(price).toLocaleString('ru-RU');
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Все кнопки "Добавить в корзину"
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            if (productId) {
                addToCart(productId, this);
            }
        });
    });

    // Кнопки +/- количества
    document.querySelectorAll('.qty-minus').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.nextElementSibling;
            const itemId = this.dataset.itemId;
            let quantity = parseInt(input.value) - 1;
            if (quantity >= 1) {
                input.value = quantity;
                updateQuantity(itemId, quantity);
            }
        });
    });

    document.querySelectorAll('.qty-plus').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const itemId = this.dataset.itemId;
            let quantity = parseInt(input.value) + 1;
            input.value = quantity;
            updateQuantity(itemId, quantity);
        });
    });

    // Прямое изменение в input
    document.querySelectorAll('.qty-input').forEach(input => {
        input.addEventListener('change', function() {
            const itemId = this.dataset.itemId;
            let quantity = parseInt(this.value);
            if (quantity < 1 || isNaN(quantity)) {
                quantity = 1;
                this.value = 1;
            }
            updateQuantity(itemId, quantity);
        });

        // Также отслеживать событие blur (потеря фокуса)
        input.addEventListener('blur', function() {
            const itemId = this.dataset.itemId;
            let quantity = parseInt(this.value);
            if (quantity < 1 || isNaN(quantity)) {
                quantity = 1;
                this.value = 1;
                updateQuantity(itemId, quantity);
            }
        });
    });

    // Кнопки удалить
    document.querySelectorAll('.btn-remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            removeFromCart(itemId);
        });
    });

    // Модальное окно оформления заказа
    const checkoutBtn = document.getElementById('checkoutBtn');
    const orderModal = document.getElementById('orderModal');
    const orderModalClose = document.getElementById('orderModalClose');
    const cancelOrder = document.getElementById('cancelOrder');
    const orderForm = document.getElementById('orderForm');
    const orderSuccess = document.getElementById('orderSuccess');
    const phoneInput = document.getElementById('phone');

    if (checkoutBtn && orderModal) {
        // Открыть модальное окно
        checkoutBtn.addEventListener('click', function() {
            orderModal.classList.add('show');
        });

        // Закрыть модальное окно
        const closeModal = function() {
            orderModal.classList.remove('show');
            orderForm.style.display = 'block';
            orderSuccess.style.display = 'none';
            orderForm.reset();
        };

        orderModalClose.addEventListener('click', closeModal);
        cancelOrder.addEventListener('click', closeModal);

        // Закрытие при клике вне модального окна
        orderModal.addEventListener('click', function(e) {
            if (e.target === orderModal) {
                closeModal();
            }
        });

        // Маска для телефона
        if (phoneInput) {
            phoneInput.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');

                if (value.length > 0) {
                    if (value[0] === '8') {
                        value = '7' + value.slice(1);
                    }
                    if (value[0] !== '7') {
                        value = '7' + value;
                    }
                }

                let formattedValue = '+7';

                if (value.length > 1) {
                    formattedValue += ' (' + value.substring(1, 4);
                }
                if (value.length >= 4) {
                    formattedValue += ') ' + value.substring(4, 7);
                }
                if (value.length >= 7) {
                    formattedValue += '-' + value.substring(7, 9);
                }
                if (value.length >= 9) {
                    formattedValue += '-' + value.substring(9, 11);
                }

                e.target.value = formattedValue;
            });
        }

        // Отправка формы
        orderForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(orderForm);

            fetch(orderForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Показать сообщение об успехе
                    orderForm.style.display = 'none';
                    orderSuccess.style.display = 'block';

                    // Закрыть модальное окно через 3 секунды
                    setTimeout(() => {
                        orderModal.classList.remove('show');
                        orderForm.style.display = 'block';
                        orderSuccess.style.display = 'none';
                        orderForm.reset();

                        // Перезагрузить страницу или перенаправить
                        location.reload();
                    }, 3000);
                } else {
                    showNotification(data.message || 'Ошибка при оформлении заказа', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Ошибка при оформлении заказа', 'error');
            });
        });
    }
});
