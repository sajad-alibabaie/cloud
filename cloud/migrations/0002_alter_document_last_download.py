# Generated by Django 3.2.10 on 2021-12-19 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='last_download',
            field=models.DateTimeField(null=True, verbose_name='Last Download'),
        ),
    ]
