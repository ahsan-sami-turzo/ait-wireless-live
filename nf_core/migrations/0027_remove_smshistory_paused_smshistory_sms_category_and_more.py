# Generated by Django 4.0.7 on 2022-09-24 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nf_core', '0026_userloginsession'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='smshistory',
            name='paused',
        ),
        migrations.AddField(
            model_name='smshistory',
            name='sms_category',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='smshistory',
            name='sms_queue',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='userloginsession',
            name='key',
            field=models.TextField(default='4e88816b-b74c-4294-95c7-bf80c5123883'),
        ),
    ]
