# Generated by Django 5.0.6 on 2024-09-05 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0007_addconsignment_category_addconsignmenttemp_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='cahregweight',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='frieght',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='prefix',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
