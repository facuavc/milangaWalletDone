# Generated by Django 4.2.7 on 2023-12-20 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0021_remove_gasto_numberpayment_gasto_paymentid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingreso',
            name='numberPayment',
        ),
        migrations.AddField(
            model_name='ingreso',
            name='paymentId',
            field=models.CharField(default=11, max_length=45),
            preserve_default=False,
        ),
    ]