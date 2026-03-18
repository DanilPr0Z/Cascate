// Scroll to top button
window.addEventListener('scroll', function() {
    const scrollTop = document.getElementById('scrollTop');
    if (window.pageYOffset > 300) {
        scrollTop.classList.add('visible');
    } else {
        scrollTop.classList.remove('visible');
    }
});

document.getElementById('scrollTop')?.addEventListener('click', function() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href.length > 1) {
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Category Submenus functionality
document.addEventListener('DOMContentLoaded', function() {
    const categoryLinks = document.querySelectorAll('.category-nav-link');
    const categorySubmenus = document.querySelectorAll('.category-submenu');
    let hideSubmenuTimeout;
    let currentActiveSubmenu = null;

    console.log('Category links found:', categoryLinks.length);
    console.log('Category submenus found:', categorySubmenus.length);

    // Function to hide all submenus
    function hideAllSubmenus() {
        categorySubmenus.forEach(submenu => {
            submenu.classList.remove('active');
        });
        currentActiveSubmenu = null;
    }

    // Function to show specific submenu
    function showSubmenu(categorySlug) {
        console.log('Showing submenu for:', categorySlug);
        hideAllSubmenus();
        const submenu = document.getElementById('submenu-' + categorySlug);
        console.log('Submenu element:', submenu);
        if (submenu) {
            clearTimeout(hideSubmenuTimeout);
            submenu.classList.add('active');
            currentActiveSubmenu = submenu;
        }
    }

    // Add hover listeners to category links
    categoryLinks.forEach(link => {
        const categorySlug = link.getAttribute('data-category-slug');
        const submenu = document.getElementById('submenu-' + categorySlug);

        if (submenu) {
            // Show submenu on hover
            link.addEventListener('mouseenter', function() {
                clearTimeout(hideSubmenuTimeout);
                showSubmenu(categorySlug);
            });

            // Hide submenu with delay when leaving link
            link.addEventListener('mouseleave', function() {
                hideSubmenuTimeout = setTimeout(() => {
                    if (currentActiveSubmenu === submenu && !submenu.matches(':hover')) {
                        hideAllSubmenus();
                    }
                }, 150);
            });
        }
    });

    // Keep submenu visible when hovering over it
    categorySubmenus.forEach(submenu => {
        submenu.addEventListener('mouseenter', function() {
            clearTimeout(hideSubmenuTimeout);
        });

        submenu.addEventListener('mouseleave', function() {
            hideSubmenuTimeout = setTimeout(() => {
                hideAllSubmenus();
            }, 150);
        });
    });

    // Hide submenus when clicking outside
    document.addEventListener('click', function(e) {
        const isClickInsideNav = e.target.closest('.secondary-nav');
        const isClickInsideSubmenu = e.target.closest('.category-submenu');

        if (!isClickInsideNav && !isClickInsideSubmenu) {
            hideAllSubmenus();
        }
    });
});

