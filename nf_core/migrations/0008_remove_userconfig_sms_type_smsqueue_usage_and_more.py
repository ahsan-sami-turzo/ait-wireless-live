# Generated by Django 4.0.7 on 2022-09-18 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nf_core', '0007_smsqueue_smstype_usersmsrate_userconfig'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userconfig',
            name='sms_type',
        ),
        migrations.AddField(
            model_name='smsqueue',
            name='usage',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='SMSType',
        ),
    ]
