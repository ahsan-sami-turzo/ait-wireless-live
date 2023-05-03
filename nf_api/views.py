import json
import csv
import os.path
import calendar
from datetime import timedelta, datetime
from urllib.parse import unquote_plus

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.db.models import Sum, Q
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken

from Notifier.celery import app
from nf_core.helper import *
from .serializers import *

import requests
# from django.conf import settings

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def clientRegistration(request):
    """
    New user registration
    """
    try:
        payload = request.data

        registration_serializer = UserRegistrationSerializer(data=payload)

        if registration_serializer.is_valid():
            first_name = registration_serializer.validated_data.get('first_name')
            last_name = registration_serializer.validated_data.get('last_name')
            email = registration_serializer.validated_data.get('email')
            mobile_number = registration_serializer.validated_data.get('mobile_number')
            username = registration_serializer.validated_data.get('username')
            password = registration_serializer.validated_data.get('password')
            confirm_password = registration_serializer.validated_data.get('confirm_password')

            if User.objects.filter(username=username).exists():
                writeActivityLog(request, f"Another user with this username ({username}) already exists.")
                return Response({
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': 'Another user with this username already exists.'
                })

            if User.objects.filter(email=email).exists():
                writeActivityLog(request, f"Another user with this email address ({email}) already exists.")
                return Response({
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': 'Another user with this email address already exists.'
                })

            if password != confirm_password:
                writeActivityLog(request, f"Password did not match during registration. Email: {email}")
                return Response({
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': 'Your password did not match.'
                })

            user_instance = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username
            )

            user_instance.set_password(confirm_password)
            user_instance.save()

            company_name = None
            if 'company_name' in request.data:
                company_name = registration_serializer.validated_data.get('company_name')

            user_info_instance = UserInfo.objects.create(
                user=user_instance,
                mobile=mobile_number,
                company_name=company_name,
                address=registration_serializer.validated_data.get('address'),
                user_group="User"
            )

            groups, created = Group.objects.get_or_create(name="User")
            groups.user_set.add(user_instance)

            user_info_instance.user_group = groups.name
            user_info_instance.save()

            # Test Balance Add
            new_balance = round(user_info_instance.credit + 5, 2)
            exp_date = user_info_instance.expiry_date.astimezone() + timedelta(days=30)

            UserRechargeHistory.objects.create(
                user_id=user_info_instance.user.id,
                payment_method="System Credit",
                trx_type="Credit",
                recharge_amount=round(5, 2),
                previous_balance=user_info_instance.credit,
                new_balance=new_balance,
                balance_expiry_date=exp_date,
                remarks="Trial Balance"
            )

            user_info_instance.credit = new_balance
            user_info_instance.expiry_date = exp_date
            user_info_instance.save()

            writeActivityLog(request, f"Fund {settings.APP_CURRENCY} {round(float(5), 2)} has been added to client {user_info_instance.user.email} balance.")
            writeActivityLog(request, f"Client ({user_info_instance.user.email}) => Old Balance: {user_info_instance.credit} & New Balance: {new_balance}")

            UserConfig.objects.create(user=user_instance)

            writeActivityLog(request, f"User registration completed successfully. Email: {email}")
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'User registration completed successfully!'
            })
        else:
            return Response(registration_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def tokenObtainPair(request):
    """
    Generate access token
    """
    try:
        payload = request.data
        login_serializer = LoginSerializer(data=payload)

        if login_serializer.is_valid():
            email = login_serializer.validated_data.get('email')
            password = login_serializer.validated_data.get('password')

            if '@' in email:
                user_instance = User.objects.get(email=email, is_active=True)
            else:
                user_instance = User.objects.get(username=email, is_active=True)

            if check_password(password, user_instance.password):
                try:
                    Group.objects.get(user=user_instance).name
                except Exception as e:
                    writeErrorLog(request, e)
                    writeActivityLog(request, 'No user group has been set. Account is inactive.')
                    return Response({
                        "code": status.HTTP_401_UNAUTHORIZED,
                        "message": "No user group has been set. Account is inactive. Please contact customer support for details.",
                        "status_code": 401,
                        "errors": [
                            {
                                "status_code": 401,
                                "message": "No user group has been set. Account is inactive. Please contact customer support for details."
                            }
                        ]
                    })

                refresh = RefreshToken.for_user(user_instance)

                writeActivityLog(request, f'Access token granted for user {email}.')

                user_instance.last_login = datetime.now().astimezone()
                user_instance.save()

                if not Token.objects.filter(user=user_instance).exists():
                    Token.objects.create(user=user_instance)

                return Response({
                    'code': status.HTTP_200_OK,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'token_type': str(refresh.payload['token_type']),
                    'expiry': refresh.payload['exp'],
                    'user_object': UserInfoSerializer(user_instance, context={'request': request}).data
                })
            else:
                writeActivityLog(request, f"Incorrect email/password combination. Email: {email}")
                return Response({
                    "code": status.HTTP_401_UNAUTHORIZED,
                    "message": "Incorrect email/password combination.",
                    "status_code": 401,
                    "errors": [
                        {
                            "status_code": 401,
                            "message": "Incorrect email/password combination."
                        }
                    ]
                })
        else:
            writeErrorLog(request, login_serializer.errors)
            return Response(login_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def sessionTokenObtainPair(request):
    """
    Generate access token based on session
    """
    try:
        payload = request.data
        session_key = payload['session']

        token_instance = UserLoginSession.objects.get(key__exact=session_key)
        user_instance = token_instance.user

        try:
            Group.objects.get(user=user_instance).name
        except Exception as e:
            writeErrorLog(request, e)
            writeActivityLog(request, 'No user group has been set. Account is inactive.')
            return Response({
                "code": status.HTTP_401_UNAUTHORIZED,
                "message": "No user group has been set. Account is inactive. Please contact customer support for details.",
                "status_code": 401,
                "errors": [
                    {
                        "status_code": 401,
                        "message": "No user group has been set. Account is inactive. Please contact customer support for details."
                    }
                ]
            })

        refresh = RefreshToken.for_user(user_instance)

        writeActivityLog(request, f'Access token granted by session for user {user_instance.email}.')

        user_instance.last_login = datetime.now().astimezone()
        user_instance.save()

        if not Token.objects.filter(user=user_instance).exists():
            Token.objects.create(user=user_instance)

        return Response({
            'code': status.HTTP_200_OK,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': str(refresh.payload['token_type']),
            'expiry': refresh.payload['exp'],
            'user_object': UserInfoSerializer(user_instance, context={'request': request}).data
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def tokenRefresh(request):
    """
    Refresh token and get new access token
    """
    try:
        payload = request.data
        refresh = RefreshToken(token=payload.get('refresh_token'), verify=True)

        user_instance = User.objects.get(id=refresh.payload['user_id'])

        writeActivityLog(request, f'{user_instance.email} requested to refresh token.')

        return Response({
            'code': status.HTTP_200_OK,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': str(refresh.payload['token_type']),
            'expiry': refresh.payload['exp'],
            'user_object': UserInfoSerializer(user_instance, context={'request': request}).data
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def tokenVerify(request):
    """
    Verify Access Token
    """
    try:
        payload = request.data
        verify = UntypedToken(token=payload.get('access_token'))

        user_instance = User.objects.get(id=verify.payload['user_id'])

        writeActivityLog(request, f'{user_instance.email} requested to verify token.')

        return Response({
            'code': status.HTTP_200_OK,
            'access_token': str(verify.token),
            'token_type': str(verify.payload['token_type']),
            'expiry': verify.payload['exp'],
            'user_object': UserInfoSerializer(user_instance, context={'request': request}).data
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def changePassword(request):
    """
    Change user password
    """
    payload = request.data
    current_password = payload['current_password']
    new_password_1 = payload['new_password_1']
    new_password_2 = payload['new_password_2']
    user_instance = User.objects.get(id=request.user.id)
    if new_password_1 == new_password_2:
        if check_password(current_password, user_instance.password):
            user_instance.set_password(new_password_2)
            user_instance.save()
            writeActivityLog(request, 'Password updated successfully!')
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'Your password updated successfully!'
            })
        else:
            writeActivityLog(request, 'Current password did not match!')
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Your current password did not match!'
            })
    else:
        writeActivityLog(request, 'New password did not match')
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': 'Your new password did not match!'
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getClientPricing(request):
    """
    Get the pricing of the SMS for client
    """
    try:
        user_pricing = UserConfig.objects.get(user_id=request.user.id).sms_rate.all()
        user_pricing = UserPricingSerializer(user_pricing, many=True, context={'request': request}).data
        return Response({
            'code': status.HTTP_200_OK,
            'message': "User pricing received successfully!",
            'data': user_pricing
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getClientSenderID(request):
    """
    Get the sender ID of user
    """
    try:
        sender_ids = UserConfig.objects.get(user_id=request.user.id).sender_id.all()
        sender_id_list = []
        for sid in sender_ids:
            sender_id_list.append(sid.sender_id)
        return Response({
            'code': status.HTTP_200_OK,
            'message': "Sender ID received successfully!",
            'data': sender_id_list
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createSMSTemplate(request):
    """
    Create SMS Template
    """
    try:
        payload = request.data
        sms_template_serializer = SMSTemplateSerializer(data=payload)
        if sms_template_serializer.is_valid():
            instance = sms_template_serializer.save(user=request.user)
            writeActivityLog(request, f'SMS template created successfully. Name: {instance.template_name}')
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'SMS template created successfully.'
            })
        else:
            writeErrorLog(request, sms_template_serializer.errors)
            return Response(sms_template_serializer.errors)
    except Exception as e:
        writeErrorLog(request, str(e))
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getSMSTemplate(request, template_id=None):
    """
    Return all the SMS Template for the user
    """
    try:
        if template_id is not None:
            many = False
            sms_templates = SMSTemplate.objects.get(user=request.user, id=template_id)
        else:
            many = True
            sms_templates = SMSTemplate.objects.filter(user=request.user)
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'SMS template received successfully.',
            'data': SMSTemplateSerializer(sms_templates, many=many).data
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updateSMSTemplate(request, template_id):
    """
    Update the SMS Template for the user
    """
    try:
        payload = request.data
        sms_templates = SMSTemplate.objects.get(user=request.user, id=template_id)
        sms_template_serializer = SMSTemplateSerializer(data=payload)
        if sms_template_serializer.is_valid():
            instance = sms_template_serializer.update(sms_templates, sms_template_serializer.validated_data)
            writeActivityLog(request, f'SMS template updated successfully. Name: {instance.template_name}')
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'SMS template updated successfully.',
                'data': SMSTemplateSerializer(sms_templates).data
            })
        else:
            writeErrorLog(request, sms_template_serializer.errors)
            return Response(sms_template_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteSMSTemplate(request, template_id):
    """
    Delete SMS Template Object
    """
    try:
        template_instance = SMSTemplate.objects.get(id=template_id)
        writeActivityLog(request, f"SMS template deleted successfully. {template_instance.template_name}")
        template_instance.delete()
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'SMS template deleted successfully.'
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createContactGroup(request):
    """
    Create contact group
    """
    try:
        payload = request.data
        contact_group_serializer = ContactGroupSerializer(data=payload)
        if contact_group_serializer.is_valid():
            instance = contact_group_serializer.save(user=request.user)
            writeActivityLog(request, f"Contact groups created successfully. Name: {instance.group_name}")
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'Contact group created successfully!'
            })
        else:
            writeErrorLog(request, contact_group_serializer.errors)
            return Response(contact_group_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getContactGroup(request, group_id=None):
    """
    Get the contact groups list
    """
    try:
        if group_id is not None:
            many = False
            contact_groups = ContactGroup.objects.get(user=request.user, id=group_id)
        else:
            many = True
            contact_groups = ContactGroup.objects.filter(user=request.user)
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'Contact groups received successfully.',
            'data': ContactGroupSerializer(contact_groups, many=many).data
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updateContactGroup(request, group_id):
    """
    Update the contact group name
    """
    try:
        payload = request.data
        group_instance = ContactGroup.objects.get(user=request.user, id=group_id)
        contact_group_serializer = ContactGroupSerializer(data=payload)
        if contact_group_serializer.is_valid():
            contact_group_serializer.update(group_instance, contact_group_serializer.validated_data)
            writeActivityLog(request, f"Contact gorup updated successfully. Name: {group_instance.group_name}")
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'Contact group updated successfully!'
            })
        else:
            writeErrorLog(request, contact_group_serializer.errors)
            return Response(contact_group_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteContactGroup(request, group_id):
    """
    Delete the contact group
    """
    try:
        group_instance = ContactGroup.objects.get(user=request.user, id=group_id)
        writeActivityLog(request, f"Contact group deleted successfully. Name: {group_instance.group_name}")
        group_instance.delete()
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'Contact group deleted successfully!'
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createSingleContact(request):
    """
    Create a single contact
    """
    try:
        payload = request.data
        contact_serializer = ContactSerializer(data=payload)
        if contact_serializer.is_valid():
            group = contact_serializer.validated_data.get('group')
            group = ContactGroup.objects.get(id=group)
            instance = contact_serializer.save(user=request.user, group=group)
            writeActivityLog(request, f"Contact created successfully. Name: {instance.name}")
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'Contact created successfully!'
            })
        else:
            writeErrorLog(request, contact_serializer.errors)
            return Response(contact_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createMultipleContact(request):
    """
    Create multiple contacts
    """
    try:
        payload = request.data
        for contact in payload['contacts']:
            contact_serializer = ContactSerializer(data=contact)
            if contact_serializer.is_valid():
                group = contact_serializer.validated_data.get('group')
                group = ContactGroup.objects.get(id=group)
                instance = contact_serializer.save(user=request.user, group=group)
                writeActivityLog(request, f"Contact created successfully. Name: {instance.name}")
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'Contact created successfully!'
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getContacts(request):
    """
    Return all the contacts of a user
    """
    try:
        many = True
        if 'group_id' in request.GET and request.GET['group_id'] != "":
            contacts = Contacts.objects.filter(user=request.user, group_id=request.GET['group_id']).order_by('id')
        else:
            contacts = Contacts.objects.filter(user=request.user).order_by('id')
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'Contact received successfully.',
            'data': ContactSerializer(contacts, many=many).data
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updateContact(request, contact_id):
    """
    Update the contact
    """
    try:
        payload = request.data
        contact_serializer = ContactSerializer(data=payload)
        if contact_serializer.is_valid():
            contact_instance = Contacts.objects.get(id=contact_id)
            instance = contact_serializer.update(contact_instance, contact_serializer.validated_data)
            writeActivityLog(request, f"Contact updated successfully. Name: {instance.name}")
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'Contact updated successfully!'
            })
        else:
            writeErrorLog(request, contact_serializer.errors)
            return Response(contact_serializer.errors)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteContact(request, contact_id):
    """
    Delete the contact
    """
    try:
        contact_instance = Contacts.objects.get(id=contact_id)
        writeActivityLog(request, f"Contact deleted successfully. Name: {contact_instance.name}")
        contact_instance.delete()
        return Response({
            'code': status.HTTP_200_OK,
            'message': 'Contact deleted successfully!'
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def uploadContacts(request):
    try:
        user_info = UserInfo.objects.get(user=request.user)
        if not user_info.config_status:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'User account must be configured before uploading files.'
            })
        user_config = UserConfig.objects.get(user=request.user)

        group_id = request.data['group']
        file = request.data['file']
        timestamp = str(datetime.now().timestamp()).split('.')[0]
        file_path = os.path.join(settings.BASE_DIR, f'media/{timestamp}.csv')

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        param = {
            "file_path": file_path,
            "user_id": request.user.id,
            "group_id": group_id
        }
        app.send_task("nf_core.tasks.uploadContact", queue=user_config.queue.queue, kwargs=param)

        writeActivityLog(request, f"Contact file has been scheduled for upload. {json.dumps(param)}")

        return Response({
            'code': status.HTTP_200_OK,
            'message': 'Your contact file has been scheduled for upload. It will be ready within 1 minute.'
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def userRechargeHistory(request):
    """
    Recharge history of the user
    """
    try:
        recharge_history = UserRechargeHistory.objects.filter(user_id=request.user.id).order_by('-created_at')

        if 'from_date' in request.GET and request.GET['from_date'] != "":
            from_date = datetime.strptime(request.GET['from_date'], "%Y-%m-%d").astimezone()
            recharge_history = recharge_history.filter(created_at__gte=from_date)

        if 'to_date' in request.GET and request.GET['to_date'] != "":
            to_date = datetime.strptime(request.GET['to_date'], "%Y-%m-%d").astimezone() + timedelta(days=1)
            recharge_history = recharge_history.filter(created_at__lte=to_date)

        paginator = PageNumberPagination()
        paginator.page_size = request.GET['count']
        result_page = paginator.paginate_queryset(recharge_history, request)
        serializer = RechargeHistorySerializer(result_page, many=True, context={'request': request})
        response = paginator.get_paginated_response(serializer.data)
        return Response({
            'code': status.HTTP_200_OK,
            'message': "User recharge history received successfully!",
            'count': response.data['count'],
            'next': response.data['next'],
            'previous': response.data['previous'],
            'results': response.data['results']
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def myAccountInfo(request):
    """
    Return the logged in used information
    """
    return Response({
        'code': status.HTTP_200_OK,
        'message': 'My account information received successfully.',
        'data': UserInfoSerializer(request.user, context={'request': request}).data
    })


def sendSMSCore(request, req_message_body, req_receiver, req_remove_duplicate, req_sender_id, schedule_time=None):
    original_sms_body = unquote_plus(req_message_body)
    mobile_numbers, total, valid, invalid = validateMobileNumber(request, req_receiver, req_remove_duplicate)
    sms_length, sms_type, sms_count, sms_body = validateSMSBody(request, original_sms_body)
    sms_body = unquote_plus(sms_body)
    sender_id = req_sender_id

    if sms_length > 0 and sms_count > 0 and valid > 0:
        """
        Checking is the sms content has blocked keyword
        """
        if containsBlockedKeyword(request, sms_body):
            return {
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'The sms content has been blocked as it contains blocked keywords.'
            }

        user_info_instance = UserInfo.objects.get(user=request.user)
        user_instance = user_info_instance.user
        user_config = UserConfig.objects.get(user=request.user)

        queue_name = user_config.queue.queue

        """
        Checking if the Sender ID belongs to this user
        """
        if not user_config.sender_id.filter(sender_id=sender_id).exists():
            return {
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Invalid Sender ID provided. Please enter a valid one.'
            }

        """
        Check the SMS type. This will return masking/non-masking
        """
        sms_category = checkSMSType(request, sender_id)

        sms_report = []

        sms_rates = user_config.sms_rate.all()

        old_balance = user_info_instance.credit

        for num in mobile_numbers:
            error, error_msg, operator_name, sms_rate = getMobileOperatorNameAndRate(request, sms_rates, num, sms_category)
            if error:
                return {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': error_msg
                }

            sms_cost = round(sms_rate * sms_count, 4)

            if user_info_instance.credit >= sms_cost:
                if user_info_instance.expiry_date >= datetime.now().astimezone():
                    sms_instance = SMSHistory.objects.create(
                        uid=str(uuid.uuid4()),
                        user=user_instance,
                        receiver=num,
                        sms_category=sms_category,
                        sms_type=sms_type,
                        sms_length=sms_length,
                        sms_count=sms_count,
                        sms_body=original_sms_body,
                        sms_body_encoded=sms_body,
                        sms_cost=sms_cost,
                        sender_id=sender_id,
                        operator_name=operator_name,
                        sms_rate=round(sms_rate, 4),
                        sms_queue=queue_name
                    )

                    new_balance = round(user_info_instance.credit - sms_cost, 4)

                    user_info_instance.credit = new_balance
                    user_info_instance.save()

                    param = {
                        "sms_id": sms_instance.id,
                        "user_id": sms_instance.user.id,
                        "queue_name": queue_name,
                        "username": user_instance.username,
                        "sms_count": sms_instance.sms_count,
                        "sender_id": sms_instance.sender_id,
                        "sms_type": sms_instance.sms_type,
                        "sms_body": sms_instance.sms_body,
                        "receiver": sms_instance.receiver,
                        "operator_name": sms_instance.operator_name
                    }
                    
                    # return {"param": param}
                    
                    ########### Start call the operator API here ###########
                    # sms_body = param.get('sms_body')
                    # sms_type = param.get('sms_type')
                    # sender_id = param.get('sender_id')
                    # receiver = param.get('receiver')
                    # url = settings.INFOZILLION_URL + "/api/v1/send-sms"
                    # payload = {
                    #     "username": settings.INFOZILLION_USERNAME,
                    #     "password": settings.INFOZILLION_PASSWORD,
                    #     "apiKey": settings.INFOZILLION_APIKEY,
                    #     "billMsisdn": sender_id,
                    #     "cli": "AMBALA",
                    #     "msisdnList": [receiver],
                    #     "transactionType": "T",
                    #     "messageType": 3,
                    #     "message": sms_body
                    # }
                    # header = {"Content-Type": "application/json"}
                    # response = requests.post(url, data=json.dumps(payload), headers=header)
                    # response = response.json()
                    # return {"response": response}
                    ########### End call the operator API here ###########

                    if schedule_time is None:
                        if not settings.DEBUG:
                            # return {"param": param}
                            app.send_task("nf_core.tasks.sendSMSQueue", queue=queue_name, kwargs=param)
                    else:
                        sms_instance.scheduled = True
                        sms_instance.scheduled_time = schedule_time
                        sms_instance.scheduled_params = json.dumps(param)
                        sms_instance.save()

                        SMSSchedule.objects.create(
                            sms_id=sms_instance.id,
                            sms_queue=queue_name,
                            params=json.dumps(param),
                            scheduled_time=schedule_time
                        )

                    writeActivityLog(request, f"SMS queue successfully. Queue: {queue_name} | ID: {sms_instance.id} | Cost: {sms_cost} | New Balance: {new_balance}")

                    sms_report.append({
                        'uid': sms_instance.uid,
                        'receiver': num,
                        'cost': sms_cost,
                        'status': 'Pending'
                    })
                else:
                    writeErrorLog(request, 'SMS sending failed! You account balance has been expired.')
                    return {
                        'code': status.HTTP_400_BAD_REQUEST,
                        'message': 'SMS sending failed! You account balance has been expired.'
                    }
            else:
                writeErrorLog(request, f'SMS sending failed! Insufficient balance. | {settings.APP_CURRENCY} {user_info_instance.credit}')
                return {
                    'code': status.HTTP_400_BAD_REQUEST,
                    'message': 'SMS sending failed! Insufficient balance.'
                }
        return {
            'code': status.HTTP_200_OK,
            'message': 'SMS has been queued successfully!',
            'old_balance': "{:.2f}".format(old_balance),
            'new_balance': "{:.2f}".format(user_info_instance.credit),
            'total_sms_cost': "{:.2f}".format(old_balance - user_info_instance.credit),
            'data': sms_report
        }
    else:
        writeErrorLog(request, f"User: {request.user.email} | SMS Length: {sms_length} | SMS Count: {sms_count} | Valid: {valid}")
        return {
            'code': status.HTTP_400_BAD_REQUEST,
            'message': 'Something went wrong. Please try again!'
        }


@api_view(['POST', 'GET'])
@authentication_classes([JWTAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def sendSMS(request):
    """
    Send SMS API for Portal
    """
    try:
        """
        Formatting and validating mobile numbers and SMS body for both GET and POST request
        """
        if request.method == 'POST':
            req_message_body = request.data['message']
            req_receiver = request.data['receiver']
            req_remove_duplicate = request.data['remove_duplicate']
            req_sender_id = str(request.data['sender_id']).strip()
        else:
            req_message_body = request.GET['message']
            req_receiver = request.GET['receiver']
            req_remove_duplicate = request.GET['remove_duplicate']
            req_sender_id = str(request.GET['sender_id']).strip()

        response = sendSMSCore(request, req_message_body, req_receiver, req_remove_duplicate, req_sender_id)
        return Response(response)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST', 'GET'])
@authentication_classes([JWTAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def scheduleSMS(request):
    """
    Send Scheduled SMS
    """
    try:
        print(request.META.get('HTTP_AUTHORIZATION'))
        print(request.user)
        """
        Formatting and validating mobile numbers and SMS body for both GET and POST request
        """
        if request.method == 'POST':
            req_message_body = request.data['message']
            req_receiver = request.data['receiver']
            req_remove_duplicate = request.data['remove_duplicate']
            req_sender_id = str(request.data['sender_id']).strip()
            schedule_time = str(request.data['schedule_time']).strip()
            schedule_time = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M").astimezone()
        else:
            req_message_body = request.GET['message']
            req_receiver = request.GET['receiver']
            req_remove_duplicate = request.GET['remove_duplicate']
            req_sender_id = str(request.GET['sender_id']).strip()
            schedule_time = str(request.GET['schedule_time']).strip()
            schedule_time = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M").astimezone()

        response = sendSMSCore(request, req_message_body, req_receiver, req_remove_duplicate, req_sender_id, schedule_time)
        return Response(response)
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def sendGroupSMS(request):
    try:
        payload = request.data
        sms_body = payload['message']
        remove_duplicates = payload['remove_duplicate']
        group_id = payload['group_id']
        sender_id = payload['sender_id']
        if ContactGroup.objects.filter(id=group_id).exists():
            receiver_list = []
            contact_list = Contacts.objects.filter(group_id=group_id, user=request.user)
            for contact in contact_list:
                receiver_list.append(contact.mobile)

            response_list = []
            if len(receiver_list) != 0:
                receiver_list = ",".join(receiver_list)
                response_list.append(sendSMSCore(request, sms_body, receiver_list, remove_duplicates, sender_id))
            return Response({
                'code': status.HTTP_200_OK,
                'message': 'Group SMS queued successfully.',
                'data': response_list
            })
        else:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Invalid group id.'
            })
    except Exception as e:
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def sendFileSMS(request):
    try:
        payload = request.data
        sms_body = payload['message']
        remove_duplicates = payload['remove_duplicate']
        sender_id = payload['sender_id']
        file = request.data['file']
        timestamp = str(datetime.now().timestamp()).split('.')[0]
        file_path = os.path.join(settings.BASE_DIR, f'media/SMS{timestamp}.csv')

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        sms_to_send = []
        with open(file_path, encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            success_count = 0
            failed_count = 0
            for row in csv_reader:
                if row[0] != "" and row[0] is not None:
                    success, mobile = formatMobileNumber(row[0])
                    if success:
                        try:
                            sms_to_send.append(mobile)
                        except Exception:
                            failed_count += 1
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1

        if len(sms_to_send) != 0:
            sms_to_send = ",".join(sms_to_send)
            response = sendSMSCore(request, sms_body, sms_to_send, remove_duplicates, sender_id)

            if os.path.exists(file_path):
                os.remove(file_path)

            return Response(response)
        else:
            return Response({
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "No receiver in file."
            })
    except Exception as e:
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getClientAPIKey(request):
    """
    Return the api key of the user
    """
    if 'regenerate' in request.GET and int(request.GET['regenerate']) == 1:
        Token.objects.filter(user=request.user).delete()
    if not Token.objects.filter(user=request.user).exists():
        Token.objects.create(user=request.user)
    key = Token.objects.get(user=request.user).key
    return Response({
        'code': status.HTTP_200_OK,
        'message': 'API Key received successfully.',
        'data': f"AM {key}"
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def smsDeliveryReport(request, sms_uid=None):
    """
    SMS Delivery report for user
    """
    try:
        if sms_uid is None:
            delivery_report = SMSHistory.objects.filter(user_id=request.user.id).order_by('-created_at')
        else:
            delivery_report = SMSHistory.objects.filter(user_id=request.user.id, uid=sms_uid).order_by('-created_at')

        if 'from_date' in request.GET and request.GET['from_date'] != "":
            from_date = datetime.strptime(request.GET['from_date'], "%Y-%m-%d").astimezone()
            delivery_report = delivery_report.filter(created_at__gte=from_date)

        if 'to_date' in request.GET and request.GET['to_date'] != "":
            to_date = datetime.strptime(request.GET['to_date'], "%Y-%m-%d").astimezone() + timedelta(days=1)
            delivery_report = delivery_report.filter(created_at__lte=to_date)

        if 'status' in request.GET and request.GET['status'] != "":
            delivery_report = delivery_report.filter(status__icontains=request.GET['status'])

        paginator = PageNumberPagination()
        paginator.page_size = request.GET['count']
        result_page = paginator.paginate_queryset(delivery_report, request)
        serializer = SMSHistorySerializer(result_page, many=True, context={'request': request})
        response = paginator.get_paginated_response(serializer.data)
        return Response({
            'code': status.HTTP_200_OK,
            'message': "SMS delivery report received successfully!",
            'count': response.data['count'],
            'next': response.data['next'],
            'previous': response.data['previous'],
            'results': response.data['results']
        })
    except Exception as e:
        writeErrorLog(request, e)
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def getAccountBalance(request):
    """
    Return the account balance of the user
    """
    user_info_instance = UserInfo.objects.get(user=request.user)
    return Response({
        'code': status.HTTP_200_OK,
        'message': 'User balance received successfully.',
        'data': {
            'currency': settings.APP_CURRENCY,
            'balance': user_info_instance.credit,
            'expiry_date': user_info_instance.expiry_date.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z%z")
        }
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getDashboardSummary(request):
    """
    Return the summary for the dashboard
    """
    try:
        total_sms_cost = round(SMSHistory.objects.filter(user=request.user, status="Delivered").aggregate(total=Sum('sms_cost'))['total'], 2)
    except Exception as e:
        total_sms_cost = 0
        writeErrorLog(request, e)

    return Response({
        'code': status.HTTP_200_OK,
        'message': 'Dashboard summary received successfully.',
        'data': {
            'successful_sms': SMSHistory.objects.filter(user=request.user, status="Delivered").count(),
            'failed_sms': SMSHistory.objects.filter(user=request.user, status="Failed").count(),
            'total_sms_cost': total_sms_cost,
            'account_balance': round(UserInfo.objects.get(user=request.user).credit, 2)
        }
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getDashboardGraph(request):
    """
    Return the graph data for the dashboard
    """
    sms_history = SMSHistory.objects.filter(user=request.user)
    total_data = []
    pending_data = []
    delivered_data = []
    failed_data = []
    for month in range(1, (datetime.now().astimezone().month + 1)):
        current_year = datetime.now().astimezone().year
        month = "{:02d}".format(month)
        start_date = datetime.strptime(f"{current_year}-{month}-01 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone()
        end_date = datetime.strptime(f"{current_year}-{month}-{calendar.monthrange(current_year, int(month))[1]} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone()
        sms_graph = sms_history.filter(created_at__range=[start_date, end_date])
        total_data.append(sms_graph.count())
        pending_data.append(sms_graph.filter(status="Pending").count())
        delivered_data.append(sms_graph.filter(status="Delivered").count())
        failed_data.append(sms_graph.filter(Q(status="Failed") | Q(status="Blocked")).count())

    return Response({
        'code': status.HTTP_200_OK,
        'message': 'User dashboard data received successfully!',
        'data': {
            'graph': [{
                'name': 'Total SMS',
                'data': total_data
            }, {
                'name': 'Pending SMS',
                'data': pending_data
            }, {
                'name': 'Delivered SMS',
                'data': delivered_data
            }, {
                'name': 'Failed SMS',
                'data': failed_data
            }]
        }
    })


@api_view(['GET'])
def testAPI(request):
    return Response(dict(code=status.HTTP_200_OK, message="API call received successfully!"))
    

@api_view(['GET'])
def testInfozAPI(request):
    try:
        url = "https://api.mnpspbd.com/a2p-sms/api/v1/send-sms"
        header = {"Content-Type": "application/json"}
        payload = {
            "username": "ambala",
            "password": "gEjfmD3@cduAY7F",
            "apiKey": "ioP7tN47IWx7XjWwL7tJxmoPYyXqHGi9",
            "billMsisdn": "01894784406",
            "cli": "AMBALA",
            "msisdnList": ["8801511311266"],
            "transactionType": "T",
            "messageType": 3,
            "message": "প্রিয় HONOFA AKTER OTS, কোড-003.0116.00016, অদ্য 02 Apr, 2023 তারিখে আপনি 18,900 টাকা ঋণের কিস্তি পরিশোধ করেছেন। ধন্যবাদ, আম্বালা ফাউন্ডেশন।"
        }
        # return Response(dict(url=url, payload=payload))
        response = requests.post(url, data=json.dumps(payload), headers=header)
        response = response.json()
        return Response({"response": response})
    except Exception as e:
        return (e)
        
        
@api_view(['GET'])
def getDeliveryStatusAPI(request):
    url = settings.INFOZILLION_DELIVERYSTATUS_URL
    payload = {
        "username": settings.INFOZILLION_USERNAME,
        "password": settings.INFOZILLION_PASSWORD,
        "apiKey": settings.INFOZILLION_APIKEY,
        "billMsisdn": "01894784406",
        "msisdnList": ["8801512548626"],
        "serverReference": "88d41292-88a8-4cd6-a37b-7d6d0c6fe47f"
    }
    header = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=header).json()
    if response["deliveryStatus"]:
        d_status = response["deliveryStatus"][0].split('-')[1]
        if d_status == 'Delivery Pending':
            d_status = "Processing"
        elif d_status == 'UnDelivered':
            d_status = "Failed"
    else:
        d_status = 'Failed'
    return Response(dict(response=response,d_status=d_status))
    
    
@api_view(['GET'])
def updateDeliveryStatusAPI(request):
    
    url = settings.INFOZILLION_DELIVERYSTATUS_URL
    payload = {
        "username": settings.INFOZILLION_USERNAME,
        "password": settings.INFOZILLION_PASSWORD,
        "apiKey": settings.INFOZILLION_APIKEY,
        "billMsisdn": "01894784406",
        "msisdnList": ["8801862663653"],
        "serverReference": "bc9ce199-bcc8-49d3-a4f9-ada0587375db"
    }
    header = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=header).json()
    if response["deliveryStatus"]:
        d_status = response["deliveryStatus"][0].split('-')[1]
        if d_status == 'Delivery Pending':
            d_status = "Processing"
        elif d_status == 'UnDelivered':
            d_status = "Failed"
    else:
        d_status = 'Failed'
    return Response(dict(response=response,d_status=d_status))