# Generated by Django 4.0.7 on 2022-09-24 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nf_core', '0028_smshistory_uid_alter_userloginsession_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smshistory',
            name='uid',
            field=models.CharField(default='d59fab64-1748-4ab4-91c7-52eeb03fa7e5', max_length=200),
        ),
        migrations.AlterField(
            model_name='userloginsession',
            name='key',
            field=models.TextField(default='a92287df-9f6b-457f-8b30-94dd0676618c'),
        ),
    ]
