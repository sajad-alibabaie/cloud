# Generated by Django 3.2.10 on 2021-12-19 21:11

import cloud.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0002_alter_document_last_download'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='uniq_Id',
            field=models.UUIDField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(upload_to=cloud.models.get_file_path),
        ),
    ]
