# Generated by Django 5.1.3 on 2024-11-29 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_add_pdf_inverted_color_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='show_progress_bars',
            field=models.CharField(
                choices=[('Enabled', 'Enabled'), ('Disabled', 'Disabled')], default='Enabled', max_length=8
            ),
        ),
    ]
