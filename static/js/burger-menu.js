// Бургер меню функционал
function delayMenu() {
    let menuPause = document.getElementsByClassName("menu__item");
    setTimeout(function () {
        // Здесь можно добавить логику задержки
    }, 5000, menuPause);
}

delayMenu();

// Закрытие меню при клике на ссылку
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu__toggle');
    const menuItems = document.querySelectorAll('.menu__item');

    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Если это не родительский элемент подменю, закрываем меню
            if (!this.parentElement.id.includes('product')) {
                menuToggle.checked = false;
            }
        });
    });
});
