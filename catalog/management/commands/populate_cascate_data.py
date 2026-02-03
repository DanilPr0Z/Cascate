from django.core.management.base import BaseCommand
from catalog.models import Category, SubCategory


class Command(BaseCommand):
    help = 'Заполняет базу данных категориями и подкатегориями из сайта Cascate Porte'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаю заполнение базы данных...'))

        # Очищаем старые данные (опционально)
        # Category.objects.all().delete()
        # SubCategory.objects.all().delete()

        # Структура категорий и подкатегорий
        categories_data = {
            'Двери': {
                'order': 1,
                'description': 'Дизайнерские двери из Италии',
                'subcategories': [
                    'Fly', 'Glamoure', 'Cristal', 'Atlantic', 'Next', 'Livia',
                    'Fly-Light', 'Nuovo', 'Rock', 'Astra', 'Milano', 'Neo Rock',
                    'Neo Nuovo', 'Fly 50', 'Cristal 50', 'Nuovo 60', 'Alta'
                ]
            },
            'Зонирование пространства': {
                'order': 2,
                'description': 'Системы зонирования и раздвижные перегородки',
                'subcategories': []
            },
            'Системы хранения': {
                'order': 3,
                'description': 'Гардеробные системы и шкафы',
                'subcategories': [
                    'Гардеробные', 'AMPIO', 'AMPIO DOORS', 'FIATO', 'FIATO DOORS',
                    'AVOLA', 'AVOLA DOORS', 'AVOLA LIGHT', 'SPIRITO'
                ]
            },
            'Дизайнерские стеновые панели': {
                'order': 4,
                'description': 'Декоративные панели для стен',
                'subcategories': ['Стеновые панели']
            },
            'Мебель': {
                'order': 5,
                'description': 'Дизайнерская мебель из Италии',
                'subcategories': [
                    'Модульные системы / витрины',
                    # Диваны
                    'DREAM', 'ROMEO', 'LEE', 'FLEX', 'ADDA', 'NEO', 'BRIT',
                    'Kubik', 'PEZZO', 'ICON', 'FELIS', 'FELIS UP', 'EDDY',
                    'ANSEL', 'ARNE',
                    # Книжные стеллажи
                    'LEGO / LEGO ASYMMETRIC', 'UN LEGO', 'ROMB', 'STRADA',
                    'LIVELLO', 'FREEDOM', 'AMPIO', 'AVOLA LIGHT',
                    # Столы
                    'ATTRAVERSARE', 'ELYSSE', 'XO', 'TELAIO', 'CASCATA',
                    'RAGNO', 'BRIS', 'ISOLA',
                    # Кровати
                    'LUKAS', 'TINA', 'GINA', 'LOIS', 'PETER', 'ENZO'
                ]
            },
            'Светильники': {
                'order': 6,
                'description': 'Дизайнерские светильники',
                'subcategories': [
                    'Люстры', 'Подвесные светильники', 'Потолочные светильники',
                    'Бра', 'Настольные лампы', 'Торшеры', 'Уличные светильники',
                    'Встраиваемые светильники', 'Трековые светильники'
                ]
            },
            'Декор и аксессуары': {
                'order': 7,
                'description': 'Предметы декора и аксессуары для интерьера',
                'subcategories': []
            },
            'Кухни': {
                'order': 8,
                'description': 'Кухонная мебель',
                'subcategories': []
            },
            'Распродажа': {
                'order': 9,
                'description': 'Товары со скидкой',
                'subcategories': []
            }
        }

        created_categories = 0
        created_subcategories = 0

        for category_name, data in categories_data.items():
            # Создаем или получаем категорию
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': data['description'],
                    'order': data['order']
                }
            )

            if created:
                created_categories += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Создана категория: {category_name}'))
            else:
                self.stdout.write(f'  Категория уже существует: {category_name}')

            # Создаем подкатегории
            for idx, subcategory_name in enumerate(data['subcategories']):
                subcategory, sub_created = SubCategory.objects.get_or_create(
                    category=category,
                    name=subcategory_name,
                    defaults={'order': idx + 1}
                )

                if sub_created:
                    created_subcategories += 1
                    self.stdout.write(f'  ✓ Создана подкатегория: {subcategory_name}')

        self.stdout.write(self.style.SUCCESS(f'\nГотово!'))
        self.stdout.write(self.style.SUCCESS(f'Создано категорий: {created_categories}'))
        self.stdout.write(self.style.SUCCESS(f'Создано подкатегорий: {created_subcategories}'))
