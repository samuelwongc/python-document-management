# Generated by Django 2.0.1 on 2018-01-08 11:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20180108_1102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='lender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='api.Lender'),
        ),
    ]
