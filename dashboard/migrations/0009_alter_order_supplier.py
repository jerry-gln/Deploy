# Generated by Django 5.0.3 on 2024-03-31 22:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_rename_supplier_supplier_suppliers_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='supplier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboard.supplier'),
        ),
    ]