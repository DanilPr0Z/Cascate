// Category card click handler
document.addEventListener('DOMContentLoaded', function() {
    const categoryCards = document.querySelectorAll('.category-card');
    
    categoryCards.forEach(card => {
        const url = card.dataset.categoryUrl;
        
        if (url) {
            card.addEventListener('click', function(e) {
                // Don't navigate if clicking on subcategory link
                if (e.target.closest('.subcategory-link')) {
                    // Let the link work naturally
                    return;
                }
                // Navigate to category page
                window.location.href = url;
            });
        }
    });
    
    // Prevent category card click when clicking on subcategory links
    const subcategoryLinks = document.querySelectorAll('.subcategory-link');
    subcategoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.stopPropagation(); // Stop event from bubbling to category card
        });
    });
});

