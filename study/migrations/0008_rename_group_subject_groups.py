# Generated by Django 4.2.5 on 2023-12-06 13:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('study', '0007_alter_lesson_options_alter_subject_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subject',
            old_name='group',
            new_name='groups',
        ),
    ]
