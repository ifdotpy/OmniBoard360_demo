# Generated by Django 2.1.10 on 2019-10-17 17:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('phone', models.CharField(blank=True, max_length=17, null=True)),
                ('email', models.EmailField(max_length=254)),
                ('cv_link', models.URLField(blank=True, max_length=128, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('position_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Position')),
            ],
        ),
    ]
