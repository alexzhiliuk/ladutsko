# Generated by Django 4.2.5 on 2023-12-14 19:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_application_options_application_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='application',
            old_name='group_id',
            new_name='group_number',
        ),
    ]
