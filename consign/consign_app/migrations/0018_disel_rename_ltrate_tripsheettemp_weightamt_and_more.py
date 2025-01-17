# Generated by Django 5.0.6 on 2024-09-17 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consign_app', '0017_alter_account_track_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Disel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Date', models.CharField(max_length=50, null=True)),
                ('vehicalno', models.CharField(max_length=50, null=True)),
                ('drivername', models.CharField(max_length=50, null=True)),
                ('ltrate', models.FloatField(max_length=50, null=True)),
                ('liter', models.FloatField(max_length=50, null=True)),
                ('total', models.FloatField(max_length=50, null=True)),
                ('trip_id', models.FloatField(max_length=50, null=True)),
            ],
        ),
        migrations.RenameField(
            model_name='tripsheettemp',
            old_name='LTRate',
            new_name='weightAmt',
        ),
        migrations.RemoveField(
            model_name='tripsheetprem',
            name='prod_price',
        ),
        migrations.RemoveField(
            model_name='tripsheetprem',
            name='weight',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='AdvGiven',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='DriverName',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='Ltr',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='Time',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='VehicalNo',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='prod_price',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='trip_id',
        ),
        migrations.RemoveField(
            model_name='tripsheettemp',
            name='weight',
        ),
        migrations.AddField(
            model_name='tripsheetprem',
            name='weightAmt',
            field=models.IntegerField(null=True),
        ),
    ]
