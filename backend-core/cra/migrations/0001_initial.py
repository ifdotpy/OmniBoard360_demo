# Generated by Django 3.0.6 on 2020-05-19 17:14

import cra.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('siebox', '0017_auto_20200428_1443'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('challenge', models.CharField(default=cra.models._gen_challenge, editable=False, max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='HardwareUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_key', models.BinaryField()),
                ('hardware', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='siebox.Hardware')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                              to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
