# Generated by Django 5.2 on 2025-05-25 15:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_page_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={'verbose_name': 'Сторінка', 'verbose_name_plural': 'Сторінки'},
        ),
        migrations.RemoveField(
            model_name='page',
            name='menu_order',
        ),
    ]
