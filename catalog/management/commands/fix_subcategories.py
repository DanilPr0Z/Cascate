from django.core.management.base import BaseCommand
from catalog.models import Product, SubCategory


class Command(BaseCommand):
    help = 'Исправляет подкатегории товаров на основе их названий'

    # Маппинг ключевых слов в названии товара к slug подкатегории
    # Порядок важен - более специфичные ключевые слова должны идти первыми
    KEYWORD_TO_SUBCATEGORY = [
        # Светильники (более специфичные первыми)
        ('настольная лампа', 'nastolnye-lampy'),
        ('люстра', 'liustry'),
        ('бра', 'bra'),
        ('лампа', 'nastolnye-lampy'),
        ('торшер', 'torshery'),
        ('подвесн', 'podvesnye'),
        # Кухни (более специфичные первыми)
        ('кухонный гарнитур', 'kukhonnye-garnitury'),
        ('кухонный остров', 'kukhonnye-ostrova'),
        ('кухонн', 'kukhonnye-stoly'),
        ('гарнитур', 'kukhonnye-garnitury'),
        ('остров', 'kukhonnye-ostrova'),
        # Бытовая техника
        ('холодильник', 'kholodilniki'),
        ('плита', 'plity'),
        ('посудомойка', 'posudomoiki'),
        ('вытяжка', 'vytiazhki'),
        # Мягкая мебель
        ('диван', 'divany'),
        ('кресло', 'kresla'),
        ('пуф', 'pufy-i-banketki'),
        ('банкетка', 'pufy-i-banketki'),
        ('шезлонг', 'shezlongi'),
        ('кушетка', 'kushetki'),
        # Столовые (последние, т.к. "стол" может быть частью других слов)
        ('стул', 'stulia'),
        ('табурет', 'taburety'),
        ('сервант', 'servanty'),
        ('буфет', 'bufety'),
        ('стол', 'stoly'),
    ]

    def handle(self, *args, **options):
        fixed_count = 0
        errors = []

        for product in Product.objects.select_related('category', 'subcategory').all():
            product_name_lower = product.name.lower()

            # Ищем ключевое слово в названии (порядок важен!)
            new_subcategory_slug = None
            for keyword, slug in self.KEYWORD_TO_SUBCATEGORY:
                if keyword in product_name_lower:
                    new_subcategory_slug = slug
                    break

            if new_subcategory_slug:
                # Ищем подкатегорию с таким slug в категории товара
                try:
                    new_subcategory = SubCategory.objects.get(
                        category=product.category,
                        slug=new_subcategory_slug
                    )

                    if product.subcategory != new_subcategory:
                        old_name = product.subcategory.name if product.subcategory else 'None'
                        product.subcategory = new_subcategory
                        product.save(update_fields=['subcategory'])
                        fixed_count += 1
                        self.stdout.write(
                            f'  {product.name}: {old_name} -> {new_subcategory.name}'
                        )
                except SubCategory.DoesNotExist:
                    errors.append(f'{product.name}: подкатегория {new_subcategory_slug} не найдена в {product.category.name}')

        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\nИсправлено {fixed_count} товаров.'))
        else:
            self.stdout.write(self.style.SUCCESS('Все товары уже имеют корректные подкатегории.'))

        if errors:
            self.stdout.write(self.style.WARNING('\nПредупреждения:'))
            for err in errors:
                self.stdout.write(f'  {err}')
