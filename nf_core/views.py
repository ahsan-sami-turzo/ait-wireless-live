import json
import os.path

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, AdminPasswordChangeForm
from rest_framework.authtoken.models import Token
from django.db.models import Sum, Count

from .decorator import *
from .forms import *
from .helper import *

from datetime import datetime, timedelta
from operator import itemgetter

def seedData(request):
    """
    Default data seed
    """
    if not User.objects.filter(username='ambalawireless').exists():
        user_instance = User.objects.create(
            first_name='Ambala',
            last_name='Wireless',
            username='ambalawireless',
            email='ambalawireless@gmail.com',
            is_staff=True,
            is_superuser=True
        )
        user_instance.set_password('ambalA9090')
        user_instance.save()

        groups, created = Group.objects.get_or_create(name='Admin')
        groups.user_set.add(user_instance)

        UserInfo.objects.create(
            user=user_instance,
            mobile='01700000000',
            company_name='Ambala Wireless',
            address='House No-62, Block-Ka Pisciculture Housing Society, Dhaka 1207',
            user_group="Admin"
        )

        UserConfig.objects.create(user=user_instance)

    if BlockKeyword.objects.all().count() == 0:
        BlockKeyword.objects.create()

    if SMSQueue.objects.all().count() == 0:
        SMSQueue.objects.create(name="General 1", queue="general1")
        SMSQueue.objects.create(name="General 2", queue="general2")
        SMSQueue.objects.create(name="General 3", queue="general3")
        SMSQueue.objects.create(name="General 4", queue="general4")
        SMSQueue.objects.create(name="General 5", queue="general5")

        SMSQueue.objects.create(name="Priority 1", queue="priority1")
        SMSQueue.objects.create(name="Priority 2", queue="priority2")
        SMSQueue.objects.create(name="Priority 3", queue="priority3")
        SMSQueue.objects.create(name="Priority 4", queue="priority4")
        SMSQueue.objects.create(name="Priority 5", queue="priority5")

    if DefaultSMSRate.objects.all().count() == 0:
        DefaultSMSRate.objects.create(
            operator_name="Grameenphone",
            operator_prefix="017",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
        DefaultSMSRate.objects.create(
            operator_name="Grameenphone",
            operator_prefix="013",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
        DefaultSMSRate.objects.create(
            operator_name="Banglalink",
            operator_prefix="014",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
        DefaultSMSRate.objects.create(
            operator_name="Banglalink",
            operator_prefix="019",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
        DefaultSMSRate.objects.create(
            operator_name="Robi",
            operator_prefix="018",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
        DefaultSMSRate.objects.create(
            operator_name="Airtel",
            operator_prefix="016",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
        DefaultSMSRate.objects.create(
            operator_name="Teletalk",
            operator_prefix="015",
            masking_sms_rate=0.6,
            non_masking_sms_rate=0.3
        )
    return HttpResponse("Seeding completed successfully.")


def homeRedirect(request):
    return HttpResponseRedirect(reverse('nf.index'))


@unauthenticated_user
def nfLogin(request):
    """
    User login handler
    """
    login_form = LoginForm()
    if request.method == 'POST':
        try:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                user_email = login_form.data.get('email')
                user_password = login_form.data.get('password')

                # Get the user instance
                user_instance = User.objects.filter(email=user_email, is_superuser=True, is_active=True)

                # Checking if the user exists
                if user_instance.exists():
                    # Get the username
                    username = user_instance[0].username

                    # Check if the user is valid
                    valid_user = authenticate(request, username=username, password=user_password)

                    if valid_user is not None:
                        writeActivityLog(request, "Login successful from email address (%s)." % user_email)
                        auth_login(request, valid_user)

                        request.session['user_avatar'] = user_instance[0].user_info.user_image.url

                        if 'next' in request.GET:
                            nextPage = request.GET['next']
                            return HttpResponseRedirect(nextPage)

                        return HttpResponseRedirect(reverse('nf.index'))
                    else:
                        writeActivityLog(request, "Invalid email address (%s) or password." % user_email)
                        messages.error(request, 'Invalid email address or password.')
                else:
                    writeActivityLog(request, "No user found with the provided email address %s." % user_email)
                    messages.error(request, 'No user found with the provided email address.')
        except Exception as e:
            writeErrorLog(request, str(e))
            messages.error(request, e)
    context = {
        'app_name': settings.APP_NAME,
        'login_form': login_form
    }
    return render(request, 'auth/login.html', context)


@login_required
def nfLogout(request):
    """
    Session logout
    """
    writeActivityLog(request, "Successful logout from email address (%s)." % request.user.email)
    auth_logout(request)
    return HttpResponseRedirect(reverse('auth.login'))


@login_required
def dashboard(request):
    """
    Home page
    """
    if 'qc' in request.GET:
        SMSQueueHandler.objects.all().delete()
        return HttpResponseRedirect(reverse('nf.index'))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Dashboard"
    }
    return render(request, 'home/index.html', context)


@login_required
def smsRate(request):
    """
    Render SMS Rate page, add/edit the data
    """
    sms_rate_form = SMSRateForm()
    if request.method == 'POST':
        if request.POST['action'] == 'add':
            sms_rate_form = SMSRateForm(data=request.POST)
            if sms_rate_form.is_valid():
                form_instance = sms_rate_form.save()
                writeActivityLog(request, f"Added a new sms rate. ID: {form_instance.id}")
                messages.success(request, 'Default SMS rate added successfully!')
                return HttpResponseRedirect(reverse('nf.sms.rate'))
            else:
                error_list = getFormErrors(sms_rate_form)
                messages.error(request, "<br>".join(error_list))

        if request.POST['action'] == 'edit':
            instance = DefaultSMSRate.objects.get(id=request.POST['rate_id'])
            sms_rate_form = SMSRateForm(instance=instance, data=request.POST)
            if sms_rate_form.is_valid():
                form_instance = sms_rate_form.save()
                writeActivityLog(request, f"Updated sms rate. ID: {form_instance.id}")
                messages.success(request, 'Default SMS rate updated successfully!')
                return HttpResponseRedirect(reverse('nf.sms.rate'))
            else:
                error_list = getFormErrors(sms_rate_form)
                messages.error(request, "<br>".join(error_list))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Default SMS Rate",
        'add_sms_rate': True,
        'sms_rate_form': sms_rate_form
    }
    return render(request, 'configuration/sms_rate.html', context)


@login_required
def smsRateDelete(request, rate_key):
    """
    Delete SMS Rate object
    """
    DefaultSMSRate.objects.get(pk=rate_key).delete()
    writeActivityLog(request, f"Deleted sms rate. ID: {rate_key}")
    messages.success(request, 'SMS rate deleted successfully!')
    return HttpResponseRedirect(reverse('nf.sms.rate'))


@login_required
@csrf_exempt
def smsRateSSR(request):
    """
    SSR Rendering for Datatable
    """
    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    data_array = []

    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    sms_rate = DefaultSMSRate.objects.all()

    # Count the total length
    totalLength = sms_rate.count()
    filteredLength = totalLength

    if search_value != "" or search_value is not None:
        sms_rate = sms_rate.filter(
            Q(operator_name__icontains=search_value) |
            Q(operator_prefix__icontains=search_value) |
            Q(non_masking_sms_rate__in=search_value) |
            Q(masking_sms_rate__in=search_value))

        filteredLength = sms_rate.count()

    sorting_keys = ['id', 'operator_name', 'operator_prefix', 'non_masking_sms_rate', 'masking_sms_rate']
    if sorting_dir == 'asc':
        sms_rate = sms_rate.order_by(f'{sorting_keys[sorting_column]}')
    else:
        sms_rate = sms_rate.order_by(f'-{sorting_keys[sorting_column]}')

    sms_rate = sms_rate[startLimit:endLimit]
    for key, row_data in enumerate(sms_rate):
        edit_action = f"""<a href="javascript:void(0);" class="badge badge-info" onclick="editSMSRate('{row_data.id}','{row_data.operator_name}','{row_data.operator_prefix}','{row_data.non_masking_sms_rate}','{row_data.masking_sms_rate}')">Edit</a>"""
        delete_action = f"""<a href="{reverse('nf.sms.rate.delete', kwargs={'rate_key': row_data.id})}" 
            class="badge badge-secondary" onclick="return confirm('Are you sure to delete this data?')">Delete</a>"""
        data_array.append([
            row_data.id,
            row_data.operator_name,
            row_data.operator_prefix,
            f"{settings.APP_CURRENCY} {row_data.non_masking_sms_rate}",
            f"{settings.APP_CURRENCY} {row_data.masking_sms_rate}",
            f"{edit_action} {delete_action}"
        ])
    response = {
        "draw": request.POST['draw'],
        "recordsTotal": totalLength,
        "recordsFiltered": filteredLength,
        "data": data_array
    }
    return JsonResponse(response, safe=False)


@login_required
def senderID(request):
    """
    Sender ID management
    """
    sender_id_form = SenderIDForm()
    if request.method == 'POST':
        if request.POST['action'] == 'add':
            sender_id_form = SenderIDForm(data=request.POST)
            if sender_id_form.is_valid():
                form_instance = sender_id_form.save()
                writeActivityLog(request, f"Added a new sender id. ID: {form_instance.id}")
                messages.success(request, 'Sender ID added successfully!')
                return HttpResponseRedirect(reverse('nf.sender.id'))
            else:
                error_list = getFormErrors(sender_id_form)
                messages.error(request, "<br>".join(error_list))

        if request.POST['action'] == 'edit':
            instance = SenderID.objects.get(id=request.POST['instance_id'])
            sender_id_form = SenderIDForm(instance=instance, data=request.POST)
            if sender_id_form.is_valid():
                form_instance = sender_id_form.save()
                writeActivityLog(request, f"Updated sender id. ID: {form_instance.id}")
                messages.success(request, 'Sender ID updated successfully!')
                return HttpResponseRedirect(reverse('nf.sender.id'))
            else:
                error_list = getFormErrors(sender_id_form)
                messages.error(request, "<br>".join(error_list))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Sender ID",
        'add_sender_id': True,
        'sender_id_form': sender_id_form
    }
    return render(request, 'configuration/sender_id.html', context)


@login_required
@csrf_exempt
def senderIDSSR(request):
    """
    SSR Rendering for Datatable
    """
    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    data_array = []

    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    sender_id = SenderID.objects.all()

    # Count the total length
    totalLength = sender_id.count()
    filteredLength = totalLength

    if search_value != "" or search_value is not None:
        sender_id = sender_id.filter(Q(sender_id__icontains=search_value))

        filteredLength = sender_id.count()

    sorting_keys = ['id', 'sender_id', 'default']
    if sorting_dir == 'asc':
        sender_id = sender_id.order_by(f'{sorting_keys[sorting_column]}')
    else:
        sender_id = sender_id.order_by(f'-{sorting_keys[sorting_column]}')

    sender_id = sender_id[startLimit:endLimit]
    for key, row_data in enumerate(sender_id):
        edit_action = f"""<a href="javascript:void(0);" class="badge badge-info" onclick="editSenderID('{row_data.id}','{row_data.sender_id}')">Edit</a>"""
        delete_action = f"""<a href="{reverse('nf.sender.id.delete', kwargs={'instance_id': row_data.id})}" 
            class="badge badge-secondary" onclick="return confirm('Are you sure to delete this data?')">Delete</a>"""
        default_badge = f"""<a href="{reverse('nf.sender.id.default', kwargs={'instance_id': row_data.id})}" class="badge badge-danger">False</a>"""
        if row_data.default:
            default_badge = f"""<a href="{reverse('nf.sender.id.default', kwargs={'instance_id': row_data.id})}" class="badge badge-success">True</a>"""
        data_array.append([
            row_data.id,
            row_data.sender_id,
            default_badge,
            f"{edit_action} {delete_action}"
        ])
    response = {
        "draw": request.POST['draw'],
        "recordsTotal": totalLength,
        "recordsFiltered": filteredLength,
        "data": data_array
    }
    return JsonResponse(response, safe=False)


@login_required
@csrf_exempt
def senderIDDuplicateCheck(request):
    """
    Checking for duplicate sender id
    """
    payload = json.loads(request.body)
    return JsonResponse({
        "code": 200,
        "data": SenderID.objects.filter(sender_id__icontains=payload['sender_id']).exists()
    }, safe=False)


@login_required
def senderIDDefault(request, instance_id):
    """
    Set default sender id
    """
    SenderID.objects.all().update(default=False)
    SenderID.objects.filter(pk=instance_id).update(default=True)
    writeActivityLog(request, f"Set default sender id. ID: {instance_id}")
    messages.success(request, 'Sender ID default has been set successfully!')
    return HttpResponseRedirect(reverse('nf.sender.id'))


@login_required
def senderIDDelete(request, instance_id):
    """
    Delete sender id instance
    """
    SenderID.objects.get(pk=instance_id).delete()
    writeActivityLog(request, f"Deleted sender id. ID: {instance_id}")
    messages.success(request, 'Sender ID deleted successfully!')
    return HttpResponseRedirect(reverse('nf.sender.id'))


@login_required
def blockKeyword(request):
    """
    Block specific keyword from SMS content
    """
    instance = BlockKeyword.objects.all().last()
    block_keyword_form = BlockKeywordForm(instance=instance)
    if request.method == 'POST':
        block_keyword_form = BlockKeywordForm(instance=instance, data=request.POST)
        block_keyword_form.save()
        writeActivityLog(request, f"Updated block keyword.")
        messages.success(request, 'Keywords updated successfully.')
        return HttpResponseRedirect(reverse('nf.block.keyword'))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Block Keyword",
        'block_keyword_form': block_keyword_form
    }
    return render(request, 'configuration/block_keyword.html', context)


@login_required
def logManager(request, log_type, log_date):
    """
    Show the activity log based on date
    """
    original_log_date = log_date
    log_date = datetime.strptime(str(log_date), "%Y-%m-%d").strftime("%Y_%m_%d")
    if log_type == 'activity-log':
        log_title = "Activity Log"
        folder_prefix = "activity"
        file_name = "activity_log"
    else:
        log_title = "Error Log"
        folder_prefix = "error"
        file_name = "error_log"
    log_file = os.path.join(settings.BASE_DIR, f'logs/{folder_prefix}/{file_name}_{log_date}.log')
    log_data = ""
    log_array = []
    if os.path.exists(log_file):
        for line in reversed(list(open(log_file))):
            log_array.append(line.rstrip())
        log_data = "\n".join(log_array)
    else:
        messages.error(request, 'No log file found for the selected date.')
    context = {
        'app_name': settings.APP_NAME,
        'page_title': log_title,
        'log_data': log_data,
        'log_date': original_log_date,
        'log_type': log_type
    }
    return render(request, 'log/log.html', context)


@login_required
def userManagement(request):
    """
    Manage clients
    """
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "User Management",
        'add_user': True
    }
    return render(request, 'user/user_management.html', context)


@login_required
def addNewUser(request):
    """
    Create new user account
    """
    user_form = UserCreateForm()
    user_info_form = UserInfoForm()
    if request.method == 'POST':
        user_form = UserCreateForm(data=request.POST)
        user_info_form = UserInfoForm(data=request.POST)
        if user_form.is_valid() and user_info_form.is_valid():
            first_name = user_form.cleaned_data.get('first_name')
            last_name = user_form.cleaned_data.get('last_name')
            email = user_form.cleaned_data.get('email')
            username = email
            mobile_number = user_info_form.cleaned_data.get('mobile')

            password = request.POST['password1']
            confirm_password = request.POST['password2']

            if User.objects.filter(username=username).exists():
                writeActivityLog(request, f"Another user with this username ({username}) already exists.")
                messages.error(request, 'Another user with this username already exists.')
            else:
                if User.objects.filter(email=email).exists():
                    writeActivityLog(request, f"Another user with this email address ({email}) already exists.")
                    messages.error(request, 'Another user with this email address already exists.')
                else:
                    if password != confirm_password:
                        writeActivityLog(request, f"Password did not match during registration. Email: {email}")
                        messages.error(request, 'Your password did not match.')
                    else:
                        user_instance = User.objects.create(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            username=username
                        )

                        user_instance.set_password(confirm_password)
                        user_instance.save()

                        company_name = None
                        if 'company_name' in request.POST and request.POST['company_name'] != "":
                            company_name = user_info_form.cleaned_data.get('company_name')

                        user_info_instance = UserInfo.objects.create(
                            user=user_instance,
                            mobile=mobile_number,
                            company_name=company_name,
                            address=user_info_form.cleaned_data.get('address'),
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
                        messages.success(request, 'User account has been created successfully.')
                        return HttpResponseRedirect(reverse('nf.user.profile.update', kwargs={'instance_id': user_instance.id}))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Add User",
        'user_form': user_form,
        'user_info_form': user_info_form
    }
    return render(request, 'user/add_user.html', context)


@login_required
def userFundDebitCredit(request):
    """
    Credit/Debit find to user account
    """
    if request.method == 'POST':
        user_id = request.POST['user_id']
        deposit_type = request.POST['deposit_type']
        trx_amount = request.POST['trx_amount']
        validity_month = request.POST['validity']
        remarks = request.POST['remarks']
        user_info_instance = UserInfo.objects.get(user_id=user_id)

        if deposit_type == "credit":
            new_balance = round(user_info_instance.credit + float(trx_amount), 2)
            exp_date = datetime.now().astimezone() + timedelta(days=int(validity_month) * 30)
        else:
            new_balance = round(user_info_instance.credit - float(trx_amount), 2)
            exp_date = user_info_instance.expiry_date.astimezone()

        UserRechargeHistory.objects.create(
            user_id=user_id,
            payment_method="Manual Payment",
            trx_type=str(deposit_type).title(),
            recharge_amount=round(float(trx_amount), 2),
            previous_balance=user_info_instance.credit,
            new_balance=new_balance,
            balance_expiry_date=exp_date,
            remarks=remarks
        )

        user_info_instance.credit = new_balance
        user_info_instance.expiry_date = exp_date
        user_info_instance.save()

        writeActivityLog(request, f"Fund {settings.APP_CURRENCY} {round(float(trx_amount), 2)} has been added to client {user_info_instance.user.email} balance.")
        writeActivityLog(request, f"Client ({user_info_instance.user.email}) => Old Balance: {user_info_instance.credit} & New Balance: {new_balance}")

        messages.success(request, "User fund has been updated successfully.")
    return HttpResponseRedirect(reverse('nf.user.management'))


@login_required
def userProfileUpdate(request, instance_id):
    """
    Update the user profile
    """
    user_info_instance = UserInfo.objects.get(user_id=instance_id)
    image_path = user_info_instance.user_image.path
    user_instance = user_info_instance.user
    photo_change_form = UserPhotoChangeForm()
    change_password_form = AdminPasswordChangeForm(request.user)
    user_form = UserForm(instance=user_instance)
    user_info_form = UserInfoForm(instance=user_info_instance)
    if request.method == 'POST':
        if 'action' in request.POST and request.POST['action'] == 'change_photo':
            photo_change_form = UserPhotoChangeForm(instance=user_info_instance, files=request.FILES)
            if photo_change_form.is_valid():
                deleteMedia(image_path)
                photo_change_form.save()
                messages.success(request, 'User photo has been updated successfully.')
                writeActivityLog(request, f'User {user_info_instance.user.email} photo updated successfully.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        elif 'action' in request.POST and request.POST['action'] == 'change_password':
            change_password_form = AdminPasswordChangeForm(user_instance, request.POST)
            if change_password_form.is_valid():
                change_password_form.save()
                messages.success(request, 'User password has been updated successfully.')
                writeActivityLog(request, f'User ({user_instance.email}) password has been updated successfully.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            else:
                error_list = getFormErrors(change_password_form)
                messages.error(request, "<br>".join(error_list))
        elif 'action' in request.POST and request.POST['action'] == 'change_info':
            user_form = UserForm(instance=user_instance, data=request.POST)
            user_info_form = UserInfoForm(instance=user_info_instance, data=request.POST)
            if user_form.is_valid() and user_info_form.is_valid():
                user_form.save()
                user_info_form.save()
                messages.success(request, 'Profile information updated successfully.')
                writeActivityLog(request, f'Profile ({user_instance.email}) information updated successfully.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Update Profile",
        'user_info_instance': user_info_instance,
        'photo_change_form': photo_change_form,
        'change_password_form': change_password_form,
        'user_form': user_form,
        'user_info_form': user_info_form
    }
    return render(request, 'user/user_profile.html', context)


@login_required
def userPendingConfig(request):
    """
    User pending configuration
    """
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "User Pending Configuration"
    }
    return render(request, 'user/user_pending_config.html', context)


@login_required
@csrf_exempt
def userManagementSSR(request):
    """
    SSR Rendering for Datatable
    """
    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    data_array = []

    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    client_list = UserInfo.objects.all()

    # Count the total length
    totalLength = client_list.count()
    filteredLength = totalLength

    if search_value != "" or search_value is not None:
        client_list = client_list.filter(
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(user__email__icontains=search_value) |
            Q(user__groups__name__icontains=search_value) |
            Q(mobile__icontains=search_value) |
            Q(user__username__icontains=search_value) |
            Q(company_name__icontains=search_value))

        filteredLength = client_list.count()

    sorting_keys = ['id', '', 'user__first_name', 'user__groups__name', 'credit', '', 'user__is_active']
    if sorting_dir == 'asc':
        client_list = client_list.order_by(f'{sorting_keys[sorting_column]}')
    else:
        client_list = client_list.order_by(f'-{sorting_keys[sorting_column]}')

    client_list = client_list[startLimit:endLimit]
    for key, row_data in enumerate(client_list):
        user_instance = row_data.user
        company_name = ""
        if row_data.company_name is not None and row_data.company_name != "":
            company_name = row_data.company_name
        user_info = f"""<small>{user_instance.first_name} {user_instance.last_name}<br><b>{company_name}</b><br>{user_instance.email}<br>{row_data.mobile}</small>"""

        today_date = datetime.now().astimezone()
        expiry_date = row_data.expiry_date.astimezone()
        days_remaining = (expiry_date - today_date).days

        user_credit = f"""<small>{'{0:.2f}'.format(row_data.credit)} {settings.APP_CURRENCY_SYMBOL}<br>{days_remaining} days</small>"""

        if row_data.config_status:
            config_instance = UserConfig.objects.get(user=user_instance)
            sender_ids = config_instance.sender_id.all()
            sender_id = []
            for sid in sender_ids:
                sender_id.append(sid.sender_id)
            sender_id = f"""<a href="javascript:void(0);" onclick="viewSenderID('{"**".join(sender_id)}')">View Sender IDs</a>"""
            route_info = f"""<small>{config_instance.queue.name}<br>{sender_id}</small>"""
        else:
            route_info = "-"

        status_toggle_url = reverse('nf.user.status.toggle', kwargs={'instance_id': user_instance.id})
        if row_data.config_status:
            if user_instance.is_active:
                user_status = f"""<a class="text-success" href="{status_toggle_url}" style="font-size: 22px;" title="User is Active"><i class="fa fa-check-circle"></i></a>"""
            else:
                user_status = f"""<a class="text-danger" href="{status_toggle_url}" style="font-size: 22px;" title="User is Inactive"><i class="fa fa-times-circle"></i></a>"""
        else:
            user_status = f"""<a class="text-warning" href="javascript:void(0);" style="font-size: 22px;" title="Configuration Pending"><i class="fa fa-warning"></i></a>"""
        configure_action = f"""<a href="{reverse('nf.user.configuration', kwargs={'instance_id': user_instance.id})}" class="badge badge-info">Configure</a>"""
        delete_action = f"""<a href="{reverse('nf.user.delete', kwargs={'instance_id': user_instance.id})}" class="badge badge-secondary" onclick="return confirm('Are you sure to delete this data?')">Delete</a>"""
        user_image = f"""<img class="round" id="user_avatar" src="{row_data.user_image.url}" alt="avatar" height="40" width="40">"""

        if row_data.user_group == 'Admin':
            user_group = f"""<label class="badge badge-success">Admin</label>"""
        else:
            user_group = f"""<label class="badge badge-info">User</label>"""

        update_profile = f"""<a href="{reverse('nf.user.profile.update', kwargs={'instance_id': user_instance.id})}" class="badge badge-dark">Edit Profile</a>"""

        if user_instance.is_superuser:
            remove_admin_action = f"""<a href="{reverse('nf.user.remove.admin', kwargs={'instance_id': user_instance.id})}" class="badge badge-danger" onclick="return confirm('Are you sure to remove from admin?')">Remove from Admin</a>"""
            add_admin_action = ""
        else:
            remove_admin_action = ""
            add_admin_action = f"""<a href="{reverse('nf.user.add.admin', kwargs={'instance_id': user_instance.id})}" class="badge badge-success" onclick="return confirm('Are you sure to add to admin?')">Add to Admin</a>"""

        debit_credit = f"""<a class="badge badge-success" href="javascript:void(0);" onclick="debitCreditModal('{user_instance.id}','{user_instance.first_name} {user_instance.last_name}')">Fund Debit/Credit</a>"""

        login_user = f"""<a href="{reverse('nf.user.account.login', kwargs={'instance_id': user_instance.id})}" class="badge badge-warning text-dark">Login</a>"""

        data_array.append([
            row_data.id,
            user_image,
            user_info,
            user_group,
            user_credit,
            route_info,
            user_status,
            f"{login_user}<br>{debit_credit}<br>{update_profile}<br>{remove_admin_action}{add_admin_action}<br>{configure_action}{delete_action}"
        ])
    response = {
        "draw": request.POST['draw'],
        "recordsTotal": totalLength,
        "recordsFiltered": filteredLength,
        "data": data_array
    }
    return JsonResponse(response, safe=False)


@login_required
@csrf_exempt
def userRechargeReportSSR(request):
    """
    SSR Rendering for Datatable
    """
    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    data_array = []

    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    filter_user = request.GET['user']
    filter_from = request.GET['from']
    filter_to = request.GET['to']

    recharge_report = UserRechargeHistory.objects.all().order_by('-created_at')

    if filter_user != "":
        recharge_report = recharge_report.filter(user_id=filter_user)

    if filter_from != "":
        filter_from = datetime.strptime(filter_from, "%Y-%m-%d").astimezone()
        recharge_report = recharge_report.filter(created_at__gte=filter_from)

    if filter_to != "":
        filter_to = datetime.strptime(filter_to, "%Y-%m-%d").astimezone() + timedelta(days=1)
        recharge_report = recharge_report.filter(created_at__lte=filter_to)

    # Count the total length
    totalLength = recharge_report.count()
    filteredLength = totalLength

    if search_value != "" or search_value is not None:
        recharge_report = recharge_report.filter(
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(user__email__icontains=search_value) |
            Q(trx_type__icontains=search_value) |
            Q(user__username__icontains=search_value))

        filteredLength = recharge_report.count()

    sorting_keys = ['id', '', 'created_at', 'trx_type', 'previous_balance', 'recharge_amount', 'new_balance', 'balance_expiry_date']
    if sorting_dir == 'asc':
        recharge_report = recharge_report.order_by(f'{sorting_keys[sorting_column]}')
    else:
        recharge_report = recharge_report.order_by(f'-{sorting_keys[sorting_column]}')

    recharge_report = recharge_report[startLimit:endLimit]
    for key, row_data in enumerate(recharge_report):
        user_instance = row_data.user
        user_info = f"""<small>{user_instance.first_name} {user_instance.last_name}<br>{user_instance.email}</small>"""

        previous_balance = "{:.2f}".format(row_data.previous_balance)
        previous_balance = f"{settings.APP_CURRENCY_SYMBOL} {previous_balance}"

        recharge_amount = "{:.2f}".format(row_data.recharge_amount)
        recharge_amount = f"{settings.APP_CURRENCY_SYMBOL} {recharge_amount}"

        new_balance = "{:.2f}".format(row_data.new_balance)
        new_balance = f"{settings.APP_CURRENCY_SYMBOL} {new_balance}"

        remarks = "-"
        if row_data.remarks is not None and row_data.remarks != "":
            remarks = row_data.remarks

        data_array.append([
            row_data.id,
            user_info,
            row_data.created_at.strftime("%d %b %Y"),
            row_data.trx_type,
            previous_balance,
            recharge_amount,
            new_balance,
            row_data.balance_expiry_date.strftime("%d %b %Y"),
            remarks
        ])
    response = {
        "draw": request.POST['draw'],
        "recordsTotal": totalLength,
        "recordsFiltered": filteredLength,
        "data": data_array
    }
    return JsonResponse(response, safe=False)


@login_required
@csrf_exempt
def userSMSReportSSR(request):
    """
    SSR Rendering for Datatable
    """
    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    data_array = []

    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    filter_user = request.GET['user']
    filter_from = request.GET['from']
    filter_to = request.GET['to']
    filter_status = ""
    filter_operator = ""
    filter_sms_type = ""
    if 'status' in request.GET:
        filter_status = request.GET['status']

    if 'operator' in request.GET:
        filter_operator = request.GET['operator']

    if 'sms_type' in request.GET:
        filter_sms_type = request.GET['sms_type']

    sms_report = SMSHistory.objects.all().order_by('-created_at')

    if filter_user != "":
        sms_report = sms_report.filter(user_id=filter_user)

    if filter_from != "":
        filter_from = datetime.strptime(filter_from, "%Y-%m-%d").astimezone()
        sms_report = sms_report.filter(created_at__gte=filter_from)

    if filter_to != "":
        filter_to = datetime.strptime(filter_to, "%Y-%m-%d").astimezone() + timedelta(days=1)
        sms_report = sms_report.filter(created_at__lte=filter_to)

    if filter_status != "":
        if filter_status == "Scheduled":
            sms_report = sms_report.filter(scheduled=True)
        else:
            sms_report = sms_report.filter(status=filter_status)

    if filter_operator != "":
        sms_report = sms_report.filter(operator_name=filter_operator)

    if filter_sms_type != "":
        sms_report = sms_report.filter(sms_category=filter_sms_type)

    # Count the total length
    totalLength = sms_report.count()
    filteredLength = totalLength

    if search_value != "" or search_value is not None:
        sms_report = sms_report.filter(
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(user__email__icontains=search_value) |
            Q(user__username__icontains=search_value) |
            Q(uid__icontains=search_value) |
            Q(receiver__icontains=search_value) |
            Q(sender_id__icontains=search_value) |
            Q(sms_body__icontains=search_value) |
            Q(status__icontains=search_value))

        filteredLength = sms_report.count()

    sorting_keys = ['id', '', 'receiver', 'created_at', 'sender_id', 'sms_cost', 'sms_body', 'status']
    if sorting_dir == 'asc':
        sms_report = sms_report.order_by(f'{sorting_keys[sorting_column]}')
    else:
        sms_report = sms_report.order_by(f'-{sorting_keys[sorting_column]}')

    sms_report = sms_report[startLimit:endLimit]
    for key, row_data in enumerate(sms_report):
        user_instance = row_data.user
        user_info = f"""<small>{user_instance.first_name} {user_instance.last_name}<br>{user_instance.email}</small>"""
        receiver = f"""<small>{row_data.receiver}<br>{row_data.operator_name}</small>"""
        timestamp = f"""<small>{row_data.created_at.astimezone().strftime("%d %b %Y<br>%I:%M:%S %p")}</small>"""
        sender_id = f"""<small>{row_data.sender_id}<br>{row_data.sms_category}</small>"""
        sms_cost = f"""<small>{row_data.sms_count} @ {row_data.sms_rate}<br>{settings.APP_CURRENCY} {row_data.sms_cost}</small>"""
        sms_content = str(row_data.sms_body).replace("\r", "").replace("\n", "<br>")
        sms_content = f"""<small>{sms_content}</small>"""

        sms_badge = "badge-dark"
        if row_data.status == "Delivered":
            sms_badge = "badge-success"
        elif row_data.status == "Failed":
            sms_badge = "badge-danger"
        elif row_data.status == "Pending":
            sms_badge = "badge-warning"

        sch_badge = ""
        if row_data.scheduled:
            sch_badge = f"""<span class="badge badge-dark">Scheduled at {row_data.scheduled_time.astimezone().strftime("%Y-%m-%d %H:%M")}</span><br>"""

        sms_status = f"""{sch_badge}<label class="badge {sms_badge}">{row_data.status}</label>"""

        data_array.append([
            row_data.id,
            user_info,
            receiver,
            timestamp,
            sender_id,
            sms_cost,
            sms_content,
            sms_status
        ])
    response = {
        "draw": request.POST['draw'],
        "recordsTotal": totalLength,
        "recordsFiltered": filteredLength,
        "data": data_array
    }
    return JsonResponse(response, safe=False)


@login_required
@csrf_exempt
def clientPendingConfigSSR(request):
    """
    SSR Rendering for Datatable
    """
    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    data_array = []

    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    client_list = UserInfo.objects.filter(user_group="User", config_status=False)

    # Count the total length
    totalLength = client_list.count()
    filteredLength = totalLength

    if search_value != "" or search_value is not None:
        client_list = client_list.filter(
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(user__email__icontains=search_value) |
            Q(mobile__icontains=search_value) |
            Q(user__username__icontains=search_value) |
            Q(company_name__icontains=search_value))

        filteredLength = client_list.count()

    sorting_keys = ['id', '', 'user__first_name', 'credit', 'user__date_joined']
    if sorting_dir == 'asc':
        client_list = client_list.order_by(f'{sorting_keys[sorting_column]}')
    else:
        client_list = client_list.order_by(f'-{sorting_keys[sorting_column]}')

    client_list = client_list[startLimit:endLimit]
    for key, row_data in enumerate(client_list):
        user_instance = row_data.user
        company_name = ""
        if row_data.company_name is not None and row_data.company_name != "":
            company_name = row_data.company_name
        user_info = f"""<small>{user_instance.first_name} {user_instance.last_name}<br><b>{company_name}</b><br>{user_instance.email}<br>{row_data.mobile}</small>"""

        today_date = datetime.now().astimezone()
        expiry_date = row_data.expiry_date.astimezone()
        days_remaining = (expiry_date - today_date).days

        user_credit = f"""<small>{'{0:.2f}'.format(row_data.credit)} {settings.APP_CURRENCY_SYMBOL}<br>{days_remaining} days</small>"""

        configure_action = f"""<a href="{reverse('nf.user.configuration', kwargs={'instance_id': user_instance.id})}" class="badge badge-info">Configure</a>"""
        delete_action = f"""<a href="{reverse('nf.user.delete', kwargs={'instance_id': user_instance.id})}" class="badge badge-secondary" onclick="return confirm('Are you sure to delete this data?')">Delete</a>"""
        user_image = f"""<img class="round" id="user_avatar" src="{row_data.user_image.url}" alt="avatar" height="40" width="40">"""
        data_array.append([
            row_data.id,
            user_image,
            user_info,
            user_credit,
            user_instance.date_joined.astimezone().strftime("%d %b %Y<br>%I:%M:%S %p"),
            f"{configure_action}{delete_action}"
        ])
    response = {
        "draw": request.POST['draw'],
        "recordsTotal": totalLength,
        "recordsFiltered": filteredLength,
        "data": data_array
    }
    return JsonResponse(response, safe=False)


@login_required
def userStatusToggle(request, instance_id):
    """
    Toggle the status of the client
    """
    user_instance = User.objects.get(id=instance_id)
    user_instance.is_active = not user_instance.is_active
    user_instance.save()

    writeActivityLog(request, f'User ({user_instance.email}) status ({not user_instance.is_active} -> {user_instance.is_active}) updated successfully.')
    messages.success(request, 'User status updated successfully.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def userDelete(request, instance_id):
    """
    Delete client object
    """
    user_info_instance = UserInfo.objects.get(user_id=instance_id)
    deleteMedia(user_info_instance.user_image.path)

    user_instance = User.objects.get(id=instance_id)
    writeActivityLog(request, f'User ({user_instance.email}) deleted successfully.')
    user_instance.delete()
    messages.success(request, 'User deleted successfully.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def decideSMSQueue(request):
    """
    Decide SMS Queue based on usage
    """
    if 'priority' in request.GET and request.GET['priority'] != "" and int(request.GET['priority']) == 1:
        priority = True
    else:
        priority = False
    if priority:
        queue_instance = SMSQueue.objects.filter(name__icontains="Priority").order_by('usage').first()
    else:
        queue_instance = SMSQueue.objects.filter(name__icontains="General").order_by('usage').first()
    return JsonResponse({
        'code': 200,
        'data': {
            'id': queue_instance.id,
            'name': queue_instance.name
        }
    }, safe=False)


@login_required
def userConfiguration(request, instance_id):
    """
    Client configuration handler
    """
    user_info_instance = UserInfo.objects.get(user_id=instance_id)
    user_instance = user_info_instance.user

    if user_info_instance.config_status:
        return HttpResponseRedirect(reverse('nf.user.configuration.update', kwargs={'instance_id': user_instance.id}))

    sms_rates = DefaultSMSRate.objects.all()

    if request.method == 'POST':
        if UserConfig.objects.filter(user=user_instance).exists():
            config_instance = UserConfig.objects.get(user=user_instance)
        else:
            config_instance = UserConfig.objects.create(user=user_instance)

        sender_ids = request.POST.getlist('sender_id')
        sms_queue_id = request.POST['sms_queue_id']

        for sid in sender_ids:
            sid_object = SenderID.objects.get(id=sid)
            config_instance.sender_id.add(sid_object)

        priority = False
        if 'priority_checkbox' in request.POST and int(request.POST['priority_checkbox']) == 1:
            priority = True

        queue_instance = SMSQueue.objects.get(id=sms_queue_id)

        config_instance.queue = queue_instance
        config_instance.priority = priority
        config_instance.save()

        queue_instance.usage = queue_instance.usage + 1
        queue_instance.save()

        for rate in sms_rates:
            nm_key = f'rate_-_{rate.operator_name}_-_{rate.operator_prefix}_-_nm_-_{rate.id}'
            m_key = f'rate_-_{rate.operator_name}_-_{rate.operator_prefix}_-_m_-_{rate.id}'
            if nm_key in request.POST and m_key in request.POST:
                # print(f"ID: {rate.id}, NM: {request.POST[nm_key]}, M: {request.POST[m_key]}")
                rate_object = UserSMSRate.objects.create(
                    operator=rate.operator_name,
                    prefix=rate.operator_prefix,
                    masking_rate=rate.masking_sms_rate,
                    non_masking_rate=rate.non_masking_sms_rate
                )
                config_instance.sms_rate.add(rate_object)

        user_info_instance.config_status = True
        user_info_instance.save()

        writeActivityLog(request, f"User ({user_instance.email}) configuration has been saved successfully.")
        messages.success(request, "User configuration has been saved successfully.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    sender_ids = SenderID.objects.all().order_by('default')

    context = {
        'app_name': settings.APP_NAME,
        'page_title': "User Configuration",
        'sender_ids': sender_ids,
        'sms_rates': sms_rates,
        'currency_name': settings.APP_CURRENCY,
        'user_info_instance': user_info_instance
    }
    return render(request, 'user/user_configuration.html', context)


@login_required
def userConfigurationUpdate(request, instance_id):
    """
    Update user configuration
    """
    user_info_instance = UserInfo.objects.get(user_id=instance_id)
    user_instance = user_info_instance.user

    sms_rates = DefaultSMSRate.objects.all()

    if request.method == 'POST':
        if UserConfig.objects.filter(user=user_instance).exists():
            config_instance = UserConfig.objects.get(user=user_instance)
        else:
            config_instance = UserConfig.objects.create(user=user_instance)

        sender_ids = request.POST.getlist('sender_id')
        sms_queue_id = request.POST['sms_queue_id']

        for sid in config_instance.sender_id.all():
            sid_object = SenderID.objects.get(id=sid.id)
            config_instance.sender_id.remove(sid_object)

        for sid in sender_ids:
            sid_object = SenderID.objects.get(id=sid)
            config_instance.sender_id.add(sid_object)

        priority = False
        if 'priority_checkbox' in request.POST and int(request.POST['priority_checkbox']) == 1:
            priority = True

        queue_instance = SMSQueue.objects.get(id=sms_queue_id)

        config_instance.queue = queue_instance
        config_instance.priority = priority
        config_instance.save()

        if sms_queue_id != config_instance.queue_id:
            queue_instance.usage = queue_instance.usage + 1
            queue_instance.save()

        for rate in config_instance.sms_rate.all():
            nm_key = f'rate_-_{rate.operator}_-_{rate.prefix}_-_nm_-_{rate.id}'
            m_key = f'rate_-_{rate.operator}_-_{rate.prefix}_-_m_-_{rate.id}'
            if nm_key in request.POST and m_key in request.POST:
                rate_object = UserSMSRate.objects.get(id=rate.id)
                rate_object.operator = rate.operator
                rate_object.prefix = rate.prefix
                rate_object.masking_rate = float(request.POST[m_key])
                rate_object.non_masking_rate = float(request.POST[nm_key])
                rate_object.save()

        user_info_instance.config_status = True
        user_info_instance.save()

        writeActivityLog(request, f"User ({user_instance.email}) configuration has been updated successfully.")
        messages.success(request, "User configuration has been updated successfully.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    sender_ids = SenderID.objects.all().order_by('default')

    user_configuration = UserConfig.objects.get(user=user_instance)

    sender_id = user_configuration.sender_id.all()
    sender_id_array = []
    for sid in sender_id:
        sender_id_array.append(sid.id)

    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Update User Configuration",
        'sender_ids': sender_ids,
        'sms_rates': sms_rates,
        'currency_name': settings.APP_CURRENCY,
        'user_info_instance': user_info_instance,
        'user_configuration': user_configuration,
        'sender_id_array': sender_id_array
    }
    return render(request, 'user/user_configuration_update.html', context)


@login_required
def userRemoveFromAdmin(request, instance_id):
    """
    Remove user from superuser
    """
    user_info_instance = UserInfo.objects.get(user_id=instance_id)
    user_instance = user_info_instance.user

    try:
        groups, created = Group.objects.get_or_create(name="Admin")
        groups.user_set.remove(user_instance)
        writeActivityLog(request, f"Removed user ({user_instance.email}) from admin role.")
    except Exception as e:
        writeErrorLog(request, e)

    try:
        groups, created = Group.objects.get_or_create(name="User")
        groups.user_set.add(user_instance)
        writeActivityLog(request, f"Added user ({user_instance.email}) to user role.")
    except Exception as e:
        writeErrorLog(request, e)

    user_instance.is_superuser = False
    user_instance.save()

    user_info_instance.user_group = "User"
    user_info_instance.save()

    messages.success(request, 'User has been removed from admin role.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def userAddToAdmin(request, instance_id):
    """
    Add user to superuser
    """
    user_info_instance = UserInfo.objects.get(user_id=instance_id)
    user_instance = user_info_instance.user

    try:
        groups, created = Group.objects.get_or_create(name="User")
        groups.user_set.remove(user_instance)
        writeActivityLog(request, f"Removed user ({user_instance.email}) from user role.")
    except Exception as e:
        writeErrorLog(request, e)

    try:
        groups, created = Group.objects.get_or_create(name="Admin")
        groups.user_set.add(user_instance)
        writeActivityLog(request, f"Added user ({user_instance.email}) to admin role.")
    except Exception as e:
        writeErrorLog(request, e)

    user_instance.is_superuser = True
    user_instance.save()

    user_info_instance.user_group = "Admin"
    user_info_instance.save()

    messages.success(request, 'User has been added to admin role.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def userAccountLogin(request, instance_id):
    """
    Login to user account anonymously
    """
    UserLoginSession.objects.filter(user_id=instance_id).delete()
    if not UserLoginSession.objects.filter(user_id=instance_id).exists():
        UserLoginSession.objects.create(user_id=instance_id, key=str(uuid.uuid4()))
    user_token = UserLoginSession.objects.get(user_id=instance_id).key
    return HttpResponseRedirect(f'{settings.PORTAL_URL}?session={user_token}')


@login_required
def myAccount(request):
    """
    My user account management
    """
    user_info_instance = UserInfo.objects.get(user=request.user)
    image_path = user_info_instance.user_image.path
    photo_change_form = UserPhotoChangeForm()
    change_password_form = PasswordChangeForm(request.user)
    user_form = UserForm(instance=request.user)
    user_info_form = UserInfoForm(instance=user_info_instance)
    if request.method == 'POST':
        if 'action' in request.POST and request.POST['action'] == 'change_photo':
            photo_change_form = UserPhotoChangeForm(instance=user_info_instance, files=request.FILES)
            if photo_change_form.is_valid():
                deleteMedia(image_path)
                photo_change_form.save()
                request.session['user_avatar'] = user_info_instance.user_image.url
                messages.success(request, 'Your photo has been updated successfully.')
                writeActivityLog(request, f'User {user_info_instance.user.email} photo updated successfully.')
                return HttpResponseRedirect(reverse('nf.my.account'))
        elif 'action' in request.POST and request.POST['action'] == 'change_password':
            change_password_form = PasswordChangeForm(request.user, request.POST)
            if change_password_form.is_valid():
                user = change_password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been updated successfully.')
                writeActivityLog(request, f'User ({request.user.email}) password has been updated successfully.')
                return HttpResponseRedirect(reverse('nf.my.account'))
            else:
                error_list = getFormErrors(change_password_form)
                messages.error(request, "<br>".join(error_list))
        elif 'action' in request.POST and request.POST['action'] == 'change_info':
            user_form = UserForm(instance=request.user, data=request.POST)
            user_info_form = UserInfoForm(instance=user_info_instance, data=request.POST)
            if user_form.is_valid() and user_info_form.is_valid():
                user_form.save()
                user_info_form.save()
                messages.success(request, 'Profile information updated successfully.')
                writeActivityLog(request, f'Profile ({request.user.email}) information updated successfully.')
                return HttpResponseRedirect(reverse('nf.my.account'))
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "My Account",
        'user_info_instance': user_info_instance,
        'photo_change_form': photo_change_form,
        'change_password_form': change_password_form,
        'user_form': user_form,
        'user_info_form': user_info_form
    }
    return render(request, 'account/my_account.html', context)


@login_required
def rechargeReport(request):
    """
    User recharge report
    """
    user_list = User.objects.all().order_by('first_name')
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Recharge Report",
        'user_list': user_list
    }
    return render(request, 'user/user_recharge_report.html', context)


@login_required
def smsReport(request):
    """
    User SMS report
    """
    user_list = User.objects.all().order_by('first_name')
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "SMS Report",
        'user_list': user_list
    }
    return render(request, 'user/user_sms_report.html', context)


@login_required
def dashboardStats(request):
    """
    Return the stats to display in dashboard
    """
    total_users = User.objects.all().count()
    sms_instance = SMSHistory.objects.all()
    total_sms_delivered = sms_instance.filter(status="Delivered").count()
    today_date = datetime.today().astimezone().strftime("%Y-%m-%d")
    today_date = datetime.strptime(today_date, "%Y-%m-%d").astimezone()
    tomorrow_date = today_date + timedelta(days=1)
    total_sms_delivered_today = sms_instance.filter(status="Delivered", created_at__gte=today_date, created_at__lte=tomorrow_date).count()
    total_sms_cost = sms_instance.aggregate(Sum('sms_cost'))['sms_cost__sum']
    if total_sms_cost is None:
        total_sms_cost = 0
    return JsonResponse({
        'code': 200,
        'message': 'Dashboard stats received successfully.',
        'data': {
            'total_users': total_users,
            'total_sms_delivered': total_sms_delivered,
            'total_sms_delivered_today': total_sms_delivered_today,
            'total_sms_cost': f"{settings.APP_CURRENCY} " + "{:.2f}".format(round(total_sms_cost, 2))
        }
    }, safe=False)


@login_required
def weeklySMSGraph(request):
    """
    Return the data for SMS graph
    """
    end_date = datetime.now().astimezone().strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d").astimezone() + timedelta(days=1)

    start_date = end_date - timedelta(days=7)

    filter_start_date = start_date
    filter_end_date = start_date

    date_array = []
    sms_count = []

    for i in range(0, 7):
        query_from = start_date
        query_to = query_from + timedelta(days=1)

        date_array.append(query_from.strftime("%d %b %Y"))
        sms_count.append(SMSHistory.objects.filter(created_at__gte=query_from, created_at__lte=query_to, status="Delivered").count())

        start_date = query_to

        filter_end_date = query_from

    return JsonResponse({
        'code': 200,
        'message': 'Graph data received successfully.',
        'data': {
            'date': date_array,
            'count': sms_count,
            'filter_start_date': filter_start_date.strftime("%d %b %Y"),
            'filter_end_date': filter_end_date.strftime("%d %b %Y")
        }
    }, safe=False)


@login_required
def realTimeStat(request):
    """
    Return the realtime stat for Dashboard
    """
    sms_list = []
    sms_queue = SMSQueueHandler.objects.all().order_by('-created_at')
    for sms in sms_queue[:20]:
        sms_list.append({
            'username': sms.username,
            'sms_count': sms.sms_count,
            'timestamp': sms.created_at.astimezone().strftime("%d %b %Y %H:%M"),
            'queue': sms.queue,
            'operator': sms.operator_logo
        })
    return JsonResponse({
        'code': 200,
        'message': 'Stats data received successfully.',
        'data': sms_list
    }, safe=False)


@login_required
def telcoReport(request):
    """
    Generate a report for telco
    """
    if 'from_date' in request.GET and 'to_date' in request.GET:
        to_date = datetime.strptime(request.GET['to_date'], "%Y-%m-%d").astimezone() + timedelta(days=1)
        from_date = datetime.strptime(request.GET['from_date'], "%Y-%m-%d").astimezone()
    else:
        to_date = datetime.now().astimezone()
        from_date = to_date - timedelta(days=7)
        return HttpResponseRedirect(f"{reverse('nf.report.telco')}?from_date={from_date.date()}&to_date={to_date.date()}")

    operator_names = ["Grameenphone", "Banglalink", "Teletalk", "Robi", "Airtel"]
    telco_report = SMSHistory.objects.filter(created_at__range=[from_date, to_date], operator_name__in=operator_names, status="Delivered").values('operator_name').annotate(
        sms_count=Count('operator_name')).order_by('-sms_count')

    in_report = []
    report_data = []
    total_sms = 0
    for report in telco_report:
        report_data.append(report)
        total_sms += float(report['sms_count'])
        in_report.append(report['operator_name'])

    for op in operator_names:
        if op not in in_report:
            report_data.append({
                'operator_name': op,
                'sms_count': 0
            })

    graph_series_label = []
    graph_series_value = []
    for dt in report_data:
        if total_sms != 0:
            percent = round((float(dt['sms_count']) / total_sms) * 100, 2)
        else:
            percent = 0
        graph_series_label.append(dt['operator_name'])
        graph_series_value.append(percent)
        dt['percentage'] = str(percent)

    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Telco Report",
        'from_date': from_date,
        'to_date': to_date,
        'report_data': report_data,
        'graph_series_label': json.dumps(graph_series_label),
        'graph_series_value': json.dumps(graph_series_value)
    }
    return render(request, 'report/telco-report.html', context)


@login_required
def telcoReportTabular(request):
    """
    Telco Report in Tabular Format
    """
    user_list = User.objects.all().order_by('first_name')
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Telco Report",
        'user_list': user_list
    }
    return render(request, 'report/telco-report-tabular.html', context)


@login_required
def balanceReport(request):
    """
    Generate a report for user balance
    """
    user_list = User.objects.all().order_by('first_name')
    user_info = None
    if 'user' in request.GET and request.GET['user'] != "":
        user_info = UserInfo.objects.get(user_id=request.GET['user'])
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "Balance Report",
        'user_list': user_list,
        'user_info': user_info
    }
    return render(request, 'report/balance_report.html', context)


@login_required
def deliveryFailedReport(request):
    """
    Generate a report for user sms
    """
    user_list = User.objects.all().order_by('first_name')
    user_info = None
    if 'user' in request.GET and request.GET['user'] != "":
        user_info = UserInfo.objects.get(user_id=request.GET['user'])
    context = {
        'app_name': settings.APP_NAME,
        'page_title': "SMS Report",
        'user_list': user_list,
        'user_info': user_info
    }
    return render(request, 'report/delivery_failed_report.html', context)
    
    
# BTRC GATEWAY TRAFFIC REPORT
# Date: 09-04-2023
@login_required
def gatewayTrafficReport(request):
    """
    Generate a report for gateway traffic (BTRC)
    """

    context = {
        'app_name': settings.APP_NAME,
        'page_title': "BTRC Gateway Traffic Report",
        'user_info': UserInfo.objects.all().order_by('id')
    }
    return render(request, 'report/gateway_traffic_report.html', context)


@login_required
@csrf_exempt
def gatewayTrafficReportSSR(request):
    """
    SSR Rendering for Datatable
    """

    filter_from = request.GET['from']
    filter_to = request.GET['to']
    filter_status = request.GET['status']
    filter_user = request.GET['user']

    if filter_from == "" and filter_to == "" and filter_status == "" and filter_user == "":
        return JsonResponse({
            "draw": request.POST['draw'],
            "data": [],
            "recordsTotal": 0,
            "recordsFiltered": 0,
        })

    search_value = request.POST['search[value]'].strip()
    startLimit = int(request.POST['start'])
    endLimit = startLimit + int(request.POST['length'])
    sorting_column = int(request.POST['order[0][column]'].strip())
    sorting_dir = request.POST['order[0][dir]'].strip()

    sms_report = SMSHistory.objects.all()

    if filter_from != "":
        filter_from = datetime.strptime(filter_from, "%Y-%m-%d").astimezone()
        sms_report = sms_report.filter(created_at__gte=filter_from)

    if filter_to != "":
        filter_to = datetime.strptime(filter_to, "%Y-%m-%d").astimezone() + timedelta(days=1)
        sms_report = sms_report.filter(created_at__lte=filter_to)

    if filter_status != "":
        if filter_status == "Scheduled":
            sms_report = sms_report.filter(scheduled=True)
        else:
            sms_report = sms_report.filter(status=filter_status)

    if filter_user != "":
        sms_report = sms_report.filter(user_id=filter_user)

    sms_report = (sms_report
                  .values('user_id', 'sender_id', 'operator_name', 'sms_category')
                  .annotate(count=Count('id'))
                  .order_by('user_id')
                  )

    data_array = []
    sms_report = sms_report[startLimit:endLimit]
    for key, value in enumerate(sms_report):
        user_info = list(UserInfo.objects.filter(user_id=value.get("user_id")).values())
        for k, info in enumerate(user_info):
            company_name = info.get("company_name")

        # sender_id_prefix = value.get("sender_id")[0:3]
        # gateway_provider = "" if sender_id_prefix == "880" else settings.GW_PROVIDERS[sender_id_prefix]
        
        sender_id_prefix = value.get("sender_id")[2:5] if value.get("sender_id")[0:1] != '0' else value.get("sender_id")[0:3]
        gateway_provider = settings.GW_PROVIDERS[sender_id_prefix]
        
        data_array.append([
            key + 1,
            company_name,
            "SMS",
            value.get("sender_id"),
            value.get("sms_category"),
            gateway_provider,
            value.get("operator_name"),
            value.get("count")
        ])

    if sorting_dir == 'desc':
        data_array = sorted(data_array, key=itemgetter(sorting_column), reverse=True)
    else:
        data_array = sorted(data_array, key=itemgetter(sorting_column), reverse=False)

    totalLength = len(data_array)

    response = {
        "draw": request.POST['draw'],
        "data": data_array,
        "recordsTotal": totalLength,
        "recordsFiltered": len(data_array),
    }

    return JsonResponse(response, safe=False)

