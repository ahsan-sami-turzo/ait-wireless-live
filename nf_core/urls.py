from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('', homeRedirect),

    path('home', dashboard, name='nf.index'),

    path('auth/login', nfLogin, name='auth.login'),
    path('auth/logout', nfLogout, name='auth.logout'),

    path('user/management', userManagement, name='nf.user.management'),
    path('user/management/add-user', addNewUser, name='nf.user.management.add.user'),
    path('user/management/fund-debit-credit', userFundDebitCredit, name='nf.user.fund.debit.credit'),
    path('user/management/update-profile/<int:instance_id>', userProfileUpdate, name='nf.user.profile.update'),
    path('user/management/configure/<int:instance_id>', userConfiguration, name='nf.user.configuration'),
    path('user/management/config/update/<int:instance_id>', userConfigurationUpdate, name='nf.user.configuration.update'),
    path('user/management/config/pending', userPendingConfig, name='nf.user.pending.config'),
    path('user/management/status-toggle/<int:instance_id>', userStatusToggle, name='nf.user.status.toggle'),
    path('user/management/delete/<int:instance_id>', userDelete, name='nf.user.delete'),
    path('user/management/remove-from-admin/<int:instance_id>', userRemoveFromAdmin, name='nf.user.remove.admin'),
    path('user/management/add-to-admin/<int:instance_id>', userAddToAdmin, name='nf.user.add.admin'),
    path('user/management/login/<int:instance_id>', userAccountLogin, name='nf.user.account.login'),

    path('sms-report', smsReport, name='nf.sms.report'),

    path('recharge-report', rechargeReport, name='nf.recharge.report'),

    path('sms-rate', smsRate, name='nf.sms.rate'),
    path('sms-rate/delete/<int:rate_key>', smsRateDelete, name='nf.sms.rate.delete'),

    path('sender-id', senderID, name='nf.sender.id'),
    path('sender-id/default/<int:instance_id>', senderIDDefault, name='nf.sender.id.default'),
    path('sender-id/delete/<int:instance_id>', senderIDDelete, name='nf.sender.id.delete'),

    path('report/telco-report', telcoReport, name='nf.report.telco'),
    path('report/new-telco-report', telcoReportTabular, name='nf.report.telco.tabular'),
    path('report/balance-report', balanceReport, name='nf.report.balance'),
    path('report/deliver-failed-report', deliveryFailedReport, name='nf.report.delivery.failed'),

    path('block-keyword', blockKeyword, name='nf.block.keyword'),

    path('log/<str:log_type>/<str:log_date>', logManager, name='nf.log'),

    path('my-account', myAccount, name='nf.my.account'),

    path('local-api/sms-rate/ssr', smsRateSSR, name='nf.sms.rate.ssr'),
    path('local-api/sender-id/ssr', senderIDSSR, name='nf.sender.id.ssr'),
    path('local-api/sender-id/duplicate-check', senderIDDuplicateCheck, name='nf.sender.id.duplicate.check'),
    path('local-api/user-management/ssr', userManagementSSR, name='nf.user.management.ssr'),
    path('local-api/recharge-report/ssr', userRechargeReportSSR, name='nf.recharge.report.ssr'),
    path('local-api/sms-report/ssr', userSMSReportSSR, name='nf.sms.report.ssr'),
    path('local-api/client-pending-confi/ssr', clientPendingConfigSSR, name='nf.client.pending.config.ssr'),
    path('local-api/decide-sms-queue', decideSMSQueue, name='nf.decide.sms.queue'),
    path('local-api/dashboard-stats', dashboardStats, name='nf.dashboard.stats'),
    path('local-api/weekly-sms-graph', weeklySMSGraph, name='nf.weekly.sms.graph'),
    path('local-api/realtime-stat', realTimeStat, name='nf.realtime.stat'),
    
    
    # BTRC GATEWAY TRAFFIC REPORT
    # Date: 09-04-2023
    path('report/gateway-traffic-report', gatewayTrafficReport, name='nf.gateway.traffic.report'),
    path('local-api/gateway-traffic-report/ssr', gatewayTrafficReportSSR, name='nf.gateway.traffic.report.ssr'),
]
