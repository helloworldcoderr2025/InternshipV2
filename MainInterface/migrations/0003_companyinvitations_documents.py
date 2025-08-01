# Generated by Django 5.1.5 on 2025-06-09 19:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainInterface', '0002_mails'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyInvitations',
            fields=[
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='MainInterface.company')),
                ('invited_date', models.TextField()),
            ],
            options={
                'db_table': 'company_invitations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('rollno', models.BigAutoField(primary_key=True, serialize=False)),
                ('results', models.TextField()),
                ('scorecard', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'documents',
                'managed': False,
            },
        ),
    ]
