# Generated by Django 5.0.6 on 2024-09-21 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0023_alter_addconsignment_door_charge_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addconsignment',
            name='total_cost',
            field=models.FloatField(null=True),
        ),
    ]
