# Generated by Django 3.1.9 on 2021-05-05 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_auto_20210505_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=10),
        ),
    ]