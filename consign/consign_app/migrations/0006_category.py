# Generated by Django 5.0.6 on 2024-09-05 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0005_addconsignment_payment_mode_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cat_name', models.CharField(max_length=150, null=True)),
            ],
        ),
    ]