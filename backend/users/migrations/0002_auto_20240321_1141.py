# Generated by Django 3.2.16 on 2024-03-21 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['username'], 'verbose_name': 'Пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=254, unique=True, verbose_name='Имя пользователя'),
        ),
    ]
