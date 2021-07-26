# Generated by Django 3.2.5 on 2021-07-26 16:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calendar_generator', '0007_auto_20210719_2117'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArbitraryLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('label', models.CharField(max_length=64)),
                ('calendar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='calendar_generator.calendar')),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('calendar', 'date')},
            },
        ),
    ]
