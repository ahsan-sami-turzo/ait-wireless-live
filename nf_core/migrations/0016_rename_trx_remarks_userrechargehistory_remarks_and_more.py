# Generated by Django 4.0.7 on 2022-09-23 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nf_core', '0015_remove_userrechargehistory_gw_response'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userrechargehistory',
            old_name='trx_remarks',
            new_name='remarks',
        ),
        migrations.AddField(
            model_name='userrechargehistory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
