# Generated by Django 4.2.5 on 2023-10-17 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('study', '0005_group_students_alter_lesson_photos'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
