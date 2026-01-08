// Filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const sortSelect = document.getElementById('sortSelect');
    
    // Sort functionality
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const form = document.getElementById('filter-form');
            if (form) {
                // Update sort hidden field
                let sortInput = form.querySelector('input[name="sort"]');
                if (!sortInput) {
                    sortInput = document.createElement('input');
                    sortInput.type = 'hidden';
                    sortInput.name = 'sort';
                    form.appendChild(sortInput);
                }
                sortInput.value = this.value;
                form.submit();
            }
        });
    }
    
    // Product card image switching on hover
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const mainImage = card.querySelector('.product-image');
        const thumbnails = card.querySelectorAll('.product-thumbnail');
        
        if (mainImage && thumbnails.length > 0) {
            const originalSrc = mainImage.src;
            
            thumbnails.forEach(thumbnail => {
                thumbnail.addEventListener('mouseenter', function() {
                    const newSrc = this.dataset.image;
                    if (newSrc) {
                        mainImage.style.opacity = '0';
                        setTimeout(() => {
                            mainImage.src = newSrc;
                            mainImage.style.opacity = '1';
                        }, 150);
                    }
                });
            });
            
            // Reset to original on mouse leave
            card.addEventListener('mouseleave', function() {
                if (originalSrc) {
                    mainImage.style.opacity = '0';
                    setTimeout(() => {
                        mainImage.src = originalSrc;
                        mainImage.style.opacity = '1';
                    }, 150);
                }
            });
        }
    });
    
    // Product card click handler
    productCards.forEach(card => {
        const url = card.dataset.productUrl;
        const link = card.querySelector('.product-link');
        const addToCartBtn = card.querySelector('.btn-add-to-cart');
        const detailsHover = card.querySelector('.product-details-hover');
        
        if (url && link) {
            link.href = url;
        }
        
        // Prevent card click when clicking on buttons or details
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                // TODO: Add to cart functionality
                alert('Товар добавлен в корзину!');
            });
        }
        
        // Prevent card navigation when clicking on details area
        if (detailsHover) {
            detailsHover.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    });
});

