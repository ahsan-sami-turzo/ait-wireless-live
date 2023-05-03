from django import forms
from django.contrib.auth.models import User
from .models import *


class LoginForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'test@example.com'
    }), required=True)

    password = forms.CharField(max_length=200, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': '********',
        'id': 'login[password]'
    }), required=True)

    class Meta:
        model = User
        fields = ['email', 'password']


class SMSRateForm(forms.ModelForm):
    operator_name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'eg. Grameenphone'
    }), label='Operator Name')

    operator_prefix = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'eg. 017'
    }), label='Operator Prefix')

    non_masking_sms_rate = forms.FloatField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'eg. 0.55',
        'steps': 'any'
    }), label='Non-Masking Rate')

    masking_sms_rate = forms.FloatField(widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'eg. 0.35',
        'steps': 'any'
    }), label='Masking Rate')

    class Meta:
        model = DefaultSMSRate
        fields = '__all__'


class SenderIDForm(forms.ModelForm):
    sender_id = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'eg. 096380000001'
    }), label='Sender ID')

    class Meta:
        model = SenderID
        fields = '__all__'


class BlockKeywordForm(forms.ModelForm):
    keywords = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 5
    }), label='Keywords')

    class Meta:
        model = BlockKeyword
        fields = '__all__'


class UserPhotoChangeForm(forms.ModelForm):
    user_image = forms.ImageField(widget=forms.FileInput(attrs={
        'onchange': 'submitPhotoForm()',
        'hidden': True
    }), required=True)

    class Meta:
        model = UserInfo
        fields = ['user_image']


class UserForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))

    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class UserInfoForm(forms.ModelForm):
    company_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }), required=False)

    mobile = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }), required=True)

    address = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }), required=False)

    class Meta:
        model = UserInfo
        fields = ['company_name', 'mobile', 'address']


class UserCreateForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }), required=True)

    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }), required=False)

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }), required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
