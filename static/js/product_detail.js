// Product detail page functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Product detail JS loaded');

    // Image gallery - thumbnail switching
    const thumbnails = document.querySelectorAll('.thumbnail-image');
    const mainImage = document.getElementById('mainProductImage');

    console.log('Thumbnails found:', thumbnails.length);
    console.log('Main image:', mainImage);

    if (thumbnails.length > 0 && mainImage) {
        console.log('Setting up thumbnail click handlers');
        thumbnails.forEach((thumbnail, index) => {
            console.log('Thumbnail', index, 'data-image:', thumbnail.getAttribute('data-image'));

            thumbnail.addEventListener('click', function() {
                console.log('Thumbnail clicked!');
                const imageUrl = this.getAttribute('data-image');
                console.log('Image URL:', imageUrl);

                // Remove active class from all thumbnails
                thumbnails.forEach(t => t.classList.remove('active'));

                // Add active class to clicked thumbnail
                this.classList.add('active');

                // Change main image with fade effect
                mainImage.style.opacity = '0.5';
                setTimeout(() => {
                    mainImage.src = imageUrl;
                    mainImage.style.opacity = '1';
                }, 200);
            });
        });
    } else {
        console.log('No thumbnails or main image found!');
    }

    // Collapsible sections
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');

    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const parent = this.parentElement;
            const isActive = parent.classList.contains('active');

            // Close all other collapsible items
            document.querySelectorAll('.collapsible-item').forEach(item => {
                item.classList.remove('active');
            });

            // Toggle current item
            if (!isActive) {
                parent.classList.add('active');
            }
        });
    });

    // Add to cart button
    const addToCartBtn = document.querySelector('.add-to-cart-btn');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function() {
            // Show notification
            const originalText = this.textContent;
            this.textContent = 'ДОБАВЛЕНО В КОРЗИНУ!';
            const originalBg = this.style.backgroundColor;

            setTimeout(() => {
                this.textContent = originalText;
                this.style.backgroundColor = originalBg;
            }, 2000);
        });
    }

    // Rating functionality
    const ratingStars = document.getElementById('rating-stars');
    console.log('Rating stars element:', ratingStars);

    if (ratingStars) {
        const stars = ratingStars.querySelectorAll('.star');
        const productId = ratingStars.dataset.productId;
        let currentRating = parseInt(ratingStars.dataset.userRating) || 0;

        console.log('Found stars:', stars.length);
        console.log('Product ID:', productId);
        console.log('Current rating:', currentRating);

        // Обновление визуального состояния звезд
        function updateStars(rating) {
            console.log('Updating stars to rating:', rating);
            stars.forEach((star, index) => {
                if (index < rating) {
                    star.classList.add('filled');
                } else {
                    star.classList.remove('filled');
                }
            });
        }

        // Hover эффект
        stars.forEach((star, index) => {
            star.addEventListener('mouseenter', function() {
                const rating = index + 1;
                stars.forEach((s, i) => {
                    if (i < rating) {
                        s.classList.add('hover');
                    } else {
                        s.classList.remove('hover');
                    }
                });
            });

            star.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const rating = parseInt(this.dataset.rating);
                console.log('Star clicked! Rating:', rating);
                submitRating(rating);
            });
        });

        ratingStars.addEventListener('mouseleave', function() {
            stars.forEach(s => s.classList.remove('hover'));
        });

        // Отправка рейтинга на сервер
        function submitRating(rating) {
            console.log('Submitting rating:', rating);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            console.log('CSRF Token:', csrfToken);

            const url = `/rate-product/${productId}/`;
            console.log('URL:', url);

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken || getCookie('csrftoken'),
                },
                body: `rating=${rating}`
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    currentRating = data.user_rating;
                    updateStars(currentRating);

                    // Обновляем текст рейтинга
                    const ratingText = document.getElementById('rating-text');
                    if (ratingText) {
                        const count = data.ratings_count;
                        const plural = count === 1 ? 'оценка' : (count < 5 ? 'оценки' : 'оценок');
                        ratingText.innerHTML = `Средний рейтинг: <strong>${data.average_rating}</strong> (${count} ${plural})`;
                    }

                    // Показываем уведомление
                    showNotification(data.message);
                } else if (data.error) {
                    console.error('Server error:', data.error);
                    showNotification(data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Произошла ошибка при сохранении оценки');
            });
        }

        // Функция для получения CSRF токена из cookie
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

        // Функция для показа уведомлений
        function showNotification(message) {
            // Создаем элемент уведомления
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #4CAF50;
                color: white;
                padding: 15px 20px;
                border-radius: 4px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);

            // Удаляем через 3 секунды
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Инициализируем текущий рейтинг
        updateStars(currentRating);
    }
});

