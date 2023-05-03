# Generated by Django 4.0.7 on 2022-09-23 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nf_core', '0024_alter_userrechargehistory_options_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='smshistory',
            name='nf_core_sms_user_id_5de1cc_idx',
        ),
        migrations.AddIndex(
            model_name='smshistory',
            index=models.Index(fields=['user', 'receiver', 'sender_id', 'status', 'scheduled'], name='nf_core_sms_user_id_2be863_idx'),
        ),
    ]
