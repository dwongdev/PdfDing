# Generated by Django 5.0.6 on 2024-07-15 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_unnecessary_profile_information'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='dark_mode',
            field=models.CharField(choices=[('Light', 'Light'), ('Dark', 'Dark')], default='Light', max_length=5),
        ),
    ]
