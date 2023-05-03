from django.conf import settings
from rest_framework import serializers
from rest_framework_friendly_errors.mixins import FriendlyErrorMessagesMixin

from nf_core.models import *


class UserRegistrationSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, required=True)
    last_name = serializers.CharField(max_length=255, required=True)
    username = serializers.CharField(min_length=6, required=True, allow_null=False, allow_blank=False)
    email = serializers.EmailField(max_length=255, required=True)
    mobile_number = serializers.CharField(max_length=11)
    company_name = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(max_length=None)
    password = serializers.CharField(max_length=255)
    confirm_password = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'mobile_number', 'company_name', 'address', 'password', 'confirm_password']


class LoginSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    email = serializers.CharField(max_length=200)
    password = serializers.CharField(max_length=200)

    class Meta:
        model = User
        fields = ['email', 'password']


class UserInfoSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    user_info_instance = None
    user_group = serializers.SerializerMethodField('get_user_group')
    user_balance = serializers.SerializerMethodField('get_user_balance')
    user_balance_expiry = serializers.SerializerMethodField('get_user_balance_expiry')
    user_image = serializers.SerializerMethodField('get_user_image')
    address = serializers.SerializerMethodField('get_address')
    company_name = serializers.SerializerMethodField('get_company_name')

    def get_user_group(self, instance):
        if self.user_info_instance is None:
            self.user_info_instance = UserInfo.objects.get(user=instance)
        return self.user_info_instance.user_group

    def get_user_image(self, instance):
        request_instance = self.context.get('request')
        return request_instance.build_absolute_uri(self.user_info_instance.user_image.url)

    def get_user_balance(self, instance):
        return self.user_info_instance.credit

    def get_user_balance_expiry(self, instance):
        return self.user_info_instance.expiry_date.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z%z")

    def get_address(self, instance):
        return self.user_info_instance.address

    def get_company_name(self, instance):
        return self.user_info_instance.company_name

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'user_group', 'user_image', 'user_balance', 'user_balance_expiry', 'company_name', 'address', 'is_active']


class UserPricingSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    currency_name = serializers.SerializerMethodField('get_currency_name')
    currency_symbol = serializers.SerializerMethodField('get_currency_symbol')

    @staticmethod
    def get_currency_name(instance):
        return settings.APP_CURRENCY

    @staticmethod
    def get_currency_symbol(instance):
        return settings.APP_CURRENCY_SYMBOL

    class Meta:
        model = UserSMSRate
        fields = ['operator', 'prefix', 'non_masking_rate', 'masking_rate', 'currency_name', 'currency_symbol']


class SMSTemplateSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    user = serializers.IntegerField(required=False, write_only=True)
    created_at = serializers.DateTimeField(required=False, write_only=True)
    updated_at = serializers.DateTimeField(required=False, write_only=True)

    class Meta:
        model = SMSTemplate
        fields = '__all__'


class ContactGroupSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    user = serializers.IntegerField(required=False, write_only=True)
    created_at = serializers.DateTimeField(required=False, write_only=True)
    updated_at = serializers.DateTimeField(required=False, write_only=True)

    class Meta:
        model = ContactGroup
        fields = '__all__'


class ContactSerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.IntegerField(required=False, write_only=True)
    group = serializers.IntegerField(required=False, write_only=True)
    group_name = serializers.SerializerMethodField('get_group_name', read_only=True)

    @staticmethod
    def get_group_name(instance):
        return instance.group.group_name

    class Meta:
        model = Contacts
        fields = ['id', 'user', 'group', 'name', 'mobile', 'group_name']


class RechargeHistorySerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    recharge_date = serializers.SerializerMethodField('get_recharge_date')

    @staticmethod
    def get_recharge_date(instance):
        return instance.created_at.astimezone().strftime("%Y-%m-%d")

    class Meta:
        model = UserRechargeHistory
        fields = ['id', 'payment_method', 'trx_id', 'trx_type', 'recharge_amount', 'previous_balance', 'new_balance', 'balance_expiry_date', 'recharge_date']


class SMSHistorySerializer(FriendlyErrorMessagesMixin, serializers.ModelSerializer):
    scheduled_time = serializers.SerializerMethodField('get_scheduled_time')
    created_at = serializers.SerializerMethodField('get_created_at')

    @staticmethod
    def get_scheduled_time(instance):
        if instance.scheduled_time is not None:
            return instance.scheduled_time.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z%z")
        else:
            return None

    @staticmethod
    def get_created_at(instance):
        return instance.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z%z")

    class Meta:
        model = SMSHistory
        fields = ['uid', 'receiver', 'sender_id', 'operator_name', 'sms_category', 'sms_type', 'sms_length', 'sms_count', 'sms_body', 'sms_rate', 'sms_cost', 'status',
                  'failure_reason', 'scheduled', 'scheduled_time', 'created_at']
