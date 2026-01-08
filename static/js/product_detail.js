// Product image switching
document.addEventListener('DOMContentLoaded', function() {
    const mainImage = document.getElementById('mainProductImage');
    const thumbnails = document.querySelectorAll('.thumbnail-image');
    
    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Update main image
                const newSrc = this.dataset.image;
                if (newSrc) {
                    mainImage.style.opacity = '0';
                    setTimeout(() => {
                        mainImage.src = newSrc;
                        mainImage.style.opacity = '1';
                    }, 150);
                }
                
                // Update active thumbnail
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
            
            // Hover preview
            thumbnail.addEventListener('mouseenter', function() {
                const newSrc = this.dataset.image;
                if (newSrc && !this.classList.contains('active')) {
                    mainImage.style.opacity = '0.7';
                }
            });
            
            thumbnail.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    mainImage.style.opacity = '1';
                }
            });
        });
    }
});

