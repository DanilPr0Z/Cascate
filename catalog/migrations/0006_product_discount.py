from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_product_price_from_alter_product_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount',
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name='Скидка (%)',
                help_text='От 0 до 99. При ненулевом значении цена отображается красным.',
            ),
        ),
    ]
