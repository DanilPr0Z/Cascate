(function () {
    'use strict';

    function filterSubcategories(categorySelect, subcategorySelect) {
        var categoryId = categorySelect.value;
        var currentSubcatId = subcategorySelect.value;

        if (!categoryId) {
            // Очищаем подкатегории если категория не выбрана
            subcategorySelect.innerHTML = '<option value="">---------</option>';
            return;
        }

        fetch('/admin/catalog/product/subcategories-by-category/?category_id=' + categoryId)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                subcategorySelect.innerHTML = '<option value="">---------</option>';
                data.subcategories.forEach(function (s) {
                    var opt = document.createElement('option');
                    opt.value = s.id;
                    opt.textContent = s.name;
                    if (String(s.id) === String(currentSubcatId)) {
                        opt.selected = true;
                    }
                    subcategorySelect.appendChild(opt);
                });
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var categorySelect = document.getElementById('id_category');
        var subcategorySelect = document.getElementById('id_subcategory');

        if (!categorySelect || !subcategorySelect) return;

        // При смене категории — фильтруем подкатегории
        categorySelect.addEventListener('change', function () {
            subcategorySelect.value = '';
            filterSubcategories(categorySelect, subcategorySelect);
        });

        // При загрузке страницы — фильтруем если категория уже выбрана
        if (categorySelect.value) {
            filterSubcategories(categorySelect, subcategorySelect);
        }
    });
})();
