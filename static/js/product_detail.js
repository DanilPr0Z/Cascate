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

    // View in salon button
    const viewSalonBtn = document.querySelector('.view-in-salon-btn');
    if (viewSalonBtn) {
        viewSalonBtn.addEventListener('click', function() {
            alert('Функция "Посмотреть в салоне" будет доступна в ближайшее время');
        });
    }

    // Details button
    const detailsBtn = document.querySelector('.details-btn');
    if (detailsBtn) {
        detailsBtn.addEventListener('click', function() {
            alert('Менеджер свяжется с вами в ближайшее время');
        });
    }
});

