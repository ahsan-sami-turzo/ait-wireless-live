from django.urls import path

from .views import *

urlpatterns = [
    path('v1/client/registration', clientRegistration),

    path('v1/client/login', tokenObtainPair),
    path('v1/client/session-login', sessionTokenObtainPair),

    path('v1/client/token/refresh', tokenRefresh),
    path('v1/client/token/verify', tokenVerify),

    path('v1/client/my-account', myAccountInfo),

    path('v1/client/change-password', changePassword),

    path('v1/client/pricing', getClientPricing),
    path('v1/client/sender-id', getClientSenderID),

    path('v1/client/sms-template/create', createSMSTemplate),
    path('v1/client/sms-template/get', getSMSTemplate),
    path('v1/client/sms-template/get/<int:template_id>', getSMSTemplate),
    path('v1/client/sms-template/update/<int:template_id>', updateSMSTemplate),
    path('v1/client/sms-template/delete/<int:template_id>', deleteSMSTemplate),

    path('v1/client/address-book/contact-group/create', createContactGroup),
    path('v1/client/address-book/contact-group/get', getContactGroup),
    path('v1/client/address-book/contact-group/get/<int:group_id>', getContactGroup),
    path('v1/client/address-book/contact-group/update/<int:group_id>', updateContactGroup),
    path('v1/client/address-book/contact-group/delete/<int:group_id>', deleteContactGroup),

    path('v1/client/address-book/manage-contact/create-single-contact', createSingleContact),
    path('v1/client/address-book/manage-contact/create-multiple-contact', createMultipleContact),
    path('v1/client/address-book/manage-contact/upload-contact', uploadContacts),
    path('v1/client/address-book/manage-contact/get', getContacts),
    path('v1/client/address-book/manage-contact/update/<int:contact_id>', updateContact),
    path('v1/client/address-book/manage-contact/delete/<int:contact_id>', deleteContact),

    path('v1/client/recharge-history', userRechargeHistory),

    path('v1/client/get-api-key', getClientAPIKey),
    path('v1/client/get-account-balance', getAccountBalance),

    path('v1/client/sms/send-sms', sendSMS),
    path('v1/client/sms/schedule-sms', scheduleSMS),
    path('v1/client/sms/send-group-sms', sendGroupSMS),
    path('v1/client/sms/send-sms-by-file', sendFileSMS),

    path('v1/client/report/sms-delivery-report', smsDeliveryReport),
    path('v1/client/report/sms-delivery-report/<str:sms_uid>', smsDeliveryReport),

    path('v1/client/get-dashboard-summary', getDashboardSummary),
    path('v1/client/get-dashboard-graph', getDashboardGraph),
    
    path('v1/client/test', testAPI),
    path('v1/client/test/send-sms', testInfozAPI),
    path('v1/client/test/get-delivery-status', getDeliveryStatusAPI),
    path('v1/client/test/update-delivery-status', updateDeliveryStatusAPI),
]
