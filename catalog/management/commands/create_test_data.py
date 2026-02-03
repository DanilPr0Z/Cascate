
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from unidecode import unidecode
from PIL import Image
import io
from catalog.models import (
    Category, SubCategory, Product, ProductImage,
    FilterCategory, FilterValue
)
import random


def transliterate_slugify(text):
    """Транслитерирует русский текст и создает slug"""
    # Сначала транслитерируем, потом создаем slug
    transliterated = unidecode(text)
    return slugify(transliterated)


class Command(BaseCommand):
    help = 'Создает тестовые данные для каталога (категории, товары, фильтры)'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем создание тестовых данных...')
        
        # Очищаем существующие данные (опционально)
        self.stdout.write('Очистка существующих данных...')
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        FilterValue.objects.all().delete()
        FilterCategory.objects.all().delete()
        
        # Создаем категории фильтров
        self.stdout.write('Создание категорий фильтров...')
        filter_categories = self.create_filter_categories()
        
        # Создаем категории
        self.stdout.write('Создание категорий...')
        categories = self.create_categories()
        
        # Создаем подкатегории
        self.stdout.write('Создание подкатегорий...')
        subcategories_map = self.create_subcategories(categories)
        
        # Создаем товары
        self.stdout.write('Создание товаров...')
        self.create_products(categories, subcategories_map, filter_categories)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Успешно создано:\n'
                f'  - {Category.objects.count()} категорий\n'
                f'  - {SubCategory.objects.count()} подкатегорий\n'
                f'  - {Product.objects.count()} товаров\n'
                f'  - {ProductImage.objects.count()} изображений\n'
                f'  - {FilterCategory.objects.count()} категорий фильтров\n'
                f'  - {FilterValue.objects.count()} значений фильтров\n'
            )
        )

    def create_image_file(self, width=800, height=600, color=None):
        """Создает тестовое изображение"""
        if color is None:
            colors = [
                (200, 150, 120),  # бежевый
                (150, 180, 200),  # голубой
                (180, 150, 180),  # розовый
                (160, 200, 160),  # зеленый
                (200, 180, 150),  # оранжевый
                (180, 160, 140),  # коричневый
            ]
            color = random.choice(colors)
        
        img = Image.new('RGB', (width, height), color=color)
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return ContentFile(img_io.read(), name='test_image.jpg')

    def create_filter_categories(self):
        """Создает категории фильтров"""
        filter_categories_data = [
            {'name': 'Популярные', 'slug': 'popular', 'order': 1},
            {'name': 'По стилю', 'slug': 'style', 'order': 2},
            {'name': 'По дизайну', 'slug': 'design', 'order': 3},
            {'name': 'По материалу', 'slug': 'material', 'order': 4},
            {'name': 'По форме', 'slug': 'shape', 'order': 5},
            {'name': 'По цвету', 'slug': 'color', 'order': 6},
            {'name': 'По помещению', 'slug': 'room', 'order': 7},
        ]
        
        filter_categories = {}
        filter_values_map = {
            'style': ['Современный', 'Классический', 'Модерн', 'Минимализм', 'Скандинавский'],
            'design': ['Угловой', 'Прямой', 'Модульный', 'Трансформер', 'С подлокотниками'],
            'material': ['Дерево', 'Ткань', 'Кожа', 'Металл', 'Пластик', 'МДФ'],
            'shape': ['Квадратный', 'Круглый', 'Овальный', 'Прямоугольный', 'Угловой'],
            'color': ['Белый', 'Черный', 'Бежевый', 'Серый', 'Коричневый', 'Синий', 'Зеленый'],
            'room': ['Гостиная', 'Спальня', 'Кухня', 'Детская', 'Кабинет', 'Прихожая'],
        }
        
        for data in filter_categories_data:
            fc, created = FilterCategory.objects.get_or_create(
                slug=data['slug'],
                defaults={'name': data['name'], 'order': data['order']}
            )
            filter_categories[data['slug']] = fc
            
            # Создаем значения для категории фильтра
            if data['slug'] in filter_values_map:
                for value_name in filter_values_map[data['slug']]:
                    FilterValue.objects.get_or_create(
                        filter_category=fc,
                        slug=transliterate_slugify(value_name),
                        defaults={'name': value_name}
                    )
        
        return filter_categories

    def create_categories(self):
        """Создает категории товаров"""
        categories_data = [
            {
                'name': 'Мягкая мебель',
                'slug': 'myagkaya_mebel',
                'order': 1,
                'color': (200, 150, 120),  # бежевый
            },
            {
                'name': 'Столовые',
                'slug': 'stolovye',
                'order': 2,
                'color': (150, 130, 100),  # коричневый
            },
            {
                'name': 'Светильники',
                'slug': 'svetilniki',
                'order': 3,
                'color': (255, 220, 150),  # желтый
            },
            {
                'name': 'Бытовая техника',
                'slug': 'bytovaya_tehnika',
                'order': 4,
                'color': (180, 180, 180),  # серый
            },
            {
                'name': 'Кухни',
                'slug': 'kuhni',
                'order': 5,
                'color': (100, 100, 120),  # темно-серый
            },
        ]
        
        categories = {}
        for data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'order': data['order'],
                    'description': f'Описание категории {data["name"]}'
                }
            )
            
            # Добавляем изображение, если его нет
            if not category.image or created:
                category.image.save(
                    f'{data["slug"]}.jpg',
                    self.create_image_file(color=data['color']),
                    save=True
                )
            
            categories[data['slug']] = category
            self.stdout.write(f'  ✓ Создана категория: {category.name}')
        
        return categories

    def create_subcategories(self, categories):
        """Создает подкатегории"""
        subcategories_data = {
            'myagkaya_mebel': ['Диваны', 'Кресла', 'Пуфы и банкетки', 'Шезлонги', 'Кушетки'],
            'stolovye': ['Столы', 'Стулья', 'Табуреты', 'Серванты', 'Буфеты'],
            'svetilniki': ['Люстры', 'Бра', 'Настольные лампы', 'Торшеры', 'Подвесные'],
            'bytovaya_tehnika': ['Холодильники', 'Плиты', 'Посудомойки', 'Вытяжки'],
            'kuhni': ['Кухонные гарнитуры', 'Кухонные острова', 'Кухонные столы'],
        }
        
        subcategories_map = {}
        for category_slug, subcat_names in subcategories_data.items():
            if category_slug not in categories:
                continue
            
            category = categories[category_slug]
            subcategories_map[category_slug] = []
            
            for order, subcat_name in enumerate(subcat_names, 1):
                subcat_slug = transliterate_slugify(subcat_name)
                subcat, created = SubCategory.objects.get_or_create(
                    category=category,
                    slug=subcat_slug,
                    defaults={
                        'name': subcat_name,
                        'order': order
                    }
                )
                subcategories_map[category_slug].append(subcat)
                self.stdout.write(f'  ✓ Создана подкатегория: {category.name} > {subcat_name}')
        
        return subcategories_map

    def create_products(self, categories, subcategories_map, filter_categories):
        """Создает товары"""
        product_names_templates = {
            'myagkaya_mebel': [
                '{style} диван {name} от {brand}',
                '{design} диван {name}',
                'Диван {design} {name} от {brand}',
                'Угловой диван {name} от {brand}',
                'Прямой диван {name} от {brand}',
            ],
            'stolovye': [
                'Стол обеденный {name} от {brand}',
                'Стул {name} от {brand}',
                '{style} стол {name}',
                'Набор столовый {name}',
            ],
            'svetilniki': [
                'Люстра {name} от {brand}',
                'Бра {name}',
                'Настольная лампа {name}',
                '{style} светильник {name}',
            ],
            'bytovaya_tehnika': [
                'Холодильник {name} от {brand}',
                'Плита {name}',
                'Посудомойка {name} от {brand}',
            ],
            'kuhni': [
                'Кухонный гарнитур {name}',
                'Кухонный остров {name}',
                '{style} кухня {name}',
            ],
        }
        
        brands = ['Flexform', 'Minotti', 'Poliform', 'B&B Italia', 'Cassina', 'Roche Bobois']
        product_names = ['Groundpiece', 'Living', 'Comfort', 'Elegance', 'Modern', 'Classic', 'Premium', 'Luxury']
        styles = ['Современный', 'Классический', 'Модерн', 'Минимализм']
        
        availability_options = ['in_stock', 'in_stock', 'in_stock', 'on_the_way', 'new_2025', 'new_arrival']
        
        # Получаем значения фильтров
        style_values = list(FilterValue.objects.filter(filter_category__slug='style'))
        design_values = list(FilterValue.objects.filter(filter_category__slug='design'))
        material_values = list(FilterValue.objects.filter(filter_category__slug='material'))
        color_values = list(FilterValue.objects.filter(filter_category__slug='color'))
        room_values = list(FilterValue.objects.filter(filter_category__slug='room'))
        
        for category_slug, category in categories.items():
            subcategories = subcategories_map.get(category_slug, [])
            templates = product_names_templates.get(category_slug, ['{name}'])
            
            # Создаем от 20 до 50 товаров для каждой категории
            products_count = random.randint(20, 50)
            
            for i in range(products_count):
                # Генерируем название
                template = random.choice(templates)
                name = template.format(
                    name=random.choice(product_names),
                    brand=random.choice(brands),
                    style=random.choice(styles),
                    design=random.choice(['Угловой', 'Прямой', 'Модульный', 'Трансформер'])
                )
                
                # Выбираем подкатегорию
                subcategory = random.choice(subcategories) if subcategories else None
                
                # Генерируем цену
                price = random.randint(100000, 5000000)
                
                # Генерируем характеристики
                country = random.choice(['Италия', 'Германия', 'Франция', 'Испания', 'Россия'])
                materials = ', '.join(random.sample([m.name for m in material_values], k=random.randint(2, 4)))
                dimensions = f"{random.randint(200, 400)}*{random.randint(150, 300)}*h{random.randint(50, 90)} см"
                product_number = f"T{random.randint(100000, 999999)} / {random.randint(100000, 999999)}"
                
                # Создаем товар
                product = Product.objects.create(
                    category=category,
                    subcategory=subcategory,
                    name=name,
                    slug=f"{category_slug}-{random.randint(1000, 9999)}-{i}",
                    price=price,
                    country=country,
                    materials=materials,
                    dimensions=dimensions,
                    product_number=product_number,
                    availability=random.choice(availability_options),
                    is_new=random.choice([True, False, False, False]),
                    is_popular=random.choice([True, False, False]),
                    short_description=f"Красивый {name.lower()} для вашего дома.",
                    description=f"Подробное описание товара {name}. Высокое качество, стильный дизайн, комфорт и надежность."
                )
                
                # Добавляем фильтры
                filter_values_to_add = []
                if style_values:
                    filter_values_to_add.append(random.choice(style_values))
                if design_values and random.choice([True, False]):
                    filter_values_to_add.append(random.choice(design_values))
                if material_values:
                    filter_values_to_add.extend(random.sample(material_values, k=random.randint(1, 3)))
                if color_values:
                    filter_values_to_add.append(random.choice(color_values))
                if room_values:
                    filter_values_to_add.append(random.choice(room_values))
                
                product.filter_values.set(filter_values_to_add)
                
                # Создаем изображения (от 1 до 4 изображений)
                images_count = random.randint(1, 4)
                for img_idx in range(images_count):
                    # Разные цвета для разных изображений
                    color_variations = [
                        (200, 150, 120),
                        (180, 160, 140),
                        (160, 140, 120),
                        (220, 180, 150),
                    ]
                    color = color_variations[img_idx % len(color_variations)]
                    
                    product_image = ProductImage.objects.create(
                        product=product,
                        image=self.create_image_file(
                            width=random.randint(600, 1200),
                            height=random.randint(600, 1200),
                            color=color
                        ),
                        is_main=(img_idx == 0),
                        order=img_idx,
                        alt_text=f"{product.name} - изображение {img_idx + 1}"
                    )
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'  Создано товаров для {category.name}: {i + 1}/{products_count}')
        
        self.stdout.write('  ✓ Все товары созданы!')

