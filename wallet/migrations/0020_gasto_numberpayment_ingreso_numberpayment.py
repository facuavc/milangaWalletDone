# Generated by Django 4.2.7 on 2023-12-20 02:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0019_alter_gasto_date_alter_ingreso_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='gasto',
            name='numberPayment',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='ingreso',
            name='numberPayment',
            field=models.IntegerField(default=1),
        ),
    ]