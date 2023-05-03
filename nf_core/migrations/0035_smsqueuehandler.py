# Generated by Django 4.0.7 on 2022-09-24 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nf_core', '0034_userloginsession_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSQueueHandler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sms_id', models.IntegerField()),
                ('username', models.CharField(max_length=200)),
                ('sms_count', models.IntegerField(default=1)),
                ('queue', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]