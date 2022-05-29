# Generated by Django 3.2.13 on 2022-05-29 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='allow_google_hd_bypass',
            field=models.BooleanField(default=False, help_text='Allow non-workspace Google logins'),
        ),
    ]