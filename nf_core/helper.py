import os
import uuid
import math
from django.conf import settings
from datetime import datetime
from nf_core.models import BlockKeyword


def get_client_ip(request):
    """
    Get the ip from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def writeErrorLog(request, error_msg):
    """
    Log all the error from the system
    """
    try:
        date_str = datetime.now().astimezone().strftime("%Y_%m_%d")
        log_file = os.path.join(settings.BASE_DIR, f'logs/error/error_log_{date_str}.log')
        f = open(log_file, "a")
        f.write("[%s][GMT%s] | %s | %s\r\n" % (
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().astimezone().strftime("%z"),
            str(get_client_ip(request)), str(error_msg)))
        f.close()
    except Exception as e:
        print(e)
        pass


def writeActivityLog(request, activity_msg):
    """
    Log all the activity from the system
    """
    try:
        date_str = datetime.now().astimezone().strftime("%Y_%m_%d")
        log_file = os.path.join(settings.BASE_DIR, f'logs/activity/activity_log_{date_str}.log')
        f = open(log_file, "a")
        f.write("[%s][GMT%s] | %s | %s | %s\r\n" % (
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().astimezone().strftime("%z"),
            str(get_client_ip(request)), request.user, str(activity_msg)))
        f.close()
    except Exception as e:
        print(e)
        pass


def getFormErrors(form_object):
    """
    Serialize the form errors
    """
    error_list = []
    error_data = form_object.errors.as_data()
    for key in error_data:
        for e in form_object.errors[key].as_data():
            for err in e:
                error_list.append(f"{str(key).replace('_', ' ').title()}: {err}")
    return error_list


def deleteMedia(media_path):
    """
    Delete media except default
    """
    if 'default' not in media_path:
        if os.path.exists(media_path):
            os.remove(media_path)


def formatMobileNumber(mobile_numbers):
    """
    Format the mobile number
    """
    operators = ["013", "014", "015", "016", "017", "018", "019"]
    mob = f"0{str(mobile_numbers).strip()[-10:]}"
    if len(mob) == 13:
        if mob[:3] == "880":
            mob = mob[2:]

    if len(mob) == 14:
        if mob[:3] == "+88":
            mob = mob[3:]

    if len(mob) == 10:
        mob = "0%s" % mob

    if len(mob) == 11 and mob[:3] in operators:
        return True, "88%s" % mob
    else:
        return False, ""


def validateMobileNumber(request, mobile_numbers, remove_duplicate):
    """
    Validate the mobile numbers and remove duplicates if asked
    """
    my_mobile = []
    operators = ["013", "014", "015", "016", "017", "018", "019"]
    total = len(mobile_numbers)
    invalid = 0
    valid = 0
    mobile_numbers = str(mobile_numbers).split(',')
    for mob in mobile_numbers:
        mob = str(mob).strip()
        if len(mob) == 13:
            if mob[:3] == "880":
                mob = mob[2:]

        if len(mob) == 14:
            if mob[:3] == "+88":
                mob = mob[3:]

        if len(mob) == 10:
            mob = "0%s" % mob

        if len(mob) == 11 and mob[:3] in operators:
            if remove_duplicate:
                if mob not in my_mobile:
                    my_mobile.append(mob)
                    valid += 1
            else:
                my_mobile.append(mob)
                valid += 1
        else:
            invalid += 1

    final_mobiles = []
    for mob in my_mobile:
        final_mobiles.append("88%s" % mob)

    return final_mobiles, total, valid, invalid


def isUnicode(request, s):
    """
    Check the content type
    """
    try:
        s.encode('ascii')
        return "text"
    except Exception as e:
        writeErrorLog(request, e)
        return "unicode"


def checkSMSType(request, sender_id):
    """
    Check the sms type based on sender id
    """
    try:
        if str(sender_id).isnumeric():
            return "Non-masking"
        else:
            return "Masking"
    except Exception as e:
        writeErrorLog(request, e)
        return "Masking"


def validateSMSBody(request, sms_body):
    """
    Validate and count sms length

    For English:
    160 Character = 1 SMS
    For more than 160 Character (1 SMS Body), rest sms will be 153 Character = 1 SMS

    For Unicode:
    70 Character = 1 SMS
    For more than 70 Character (1 SMS Body), rest sms will be 67 Character = 1 SMS
    """
    sms_body = str(sms_body).replace('\r\n', '\n')
    sms_body = sms_body.strip()
    sms_length = len(sms_body)
    sms_type = isUnicode(request, sms_body)
    sms_count = 0
    if sms_type == "text":
        if sms_length > 160:
            temp_length = sms_length - 160
            sms_count = 1 + math.ceil(temp_length / 153)
        else:
            sms_count = 1
    else:
        if sms_length > 70:
            temp_length = sms_length - 70
            sms_count = 1 + math.ceil(temp_length / 67)
        else:
            sms_count = 1

    if sms_count <= 10:
        return sms_length, sms_type, sms_count, sms_body
    else:
        return 0, 0, 0, ""


def containsBlockedKeyword(request, sms_body):
    """
    Check for blocked keyword in sms content
    """
    block_keyword = BlockKeyword.objects.all().last()
    block_keyword = str(block_keyword.keywords).split(',')
    for key, kw in enumerate(block_keyword):
        try:
            block_keyword[key] = kw.lower().strip()
        except Exception as e:
            writeErrorLog(request, e)
    try:
        sms_body_copy = str(sms_body).lower()
    except Exception as e:
        writeErrorLog(request, e)
        sms_body_copy = sms_body

    for kw in block_keyword:
        if kw in sms_body_copy:
            return True

    return False


def getMobileOperatorNameAndRate(request, sms_rates, mobile_number, sms_category):
    """
    Return the mobile operator name and rate based on prefix

    sms_category = masking/non-masking
    """
    operator_name = ""
    operator_prefix = ""
    sms_rate = 0
    if mobile_number[:5] == "88013":
        operator_name = "Grameenphone"
        operator_prefix = "013"
    elif mobile_number[:5] == "88014":
        operator_name = "Banglalink"
        operator_prefix = "014"
    elif mobile_number[:5] == "88015":
        operator_name = "Teletalk"
        operator_prefix = "015"
    elif mobile_number[:5] == "88016":
        operator_name = "Airtel"
        operator_prefix = "016"
    elif mobile_number[:5] == "88017":
        operator_name = "Grameenphone"
        operator_prefix = "017"
    elif mobile_number[:5] == "88018":
        operator_name = "Robi"
        operator_prefix = "018"
    elif mobile_number[:5] == "88019":
        operator_name = "Banglalink"
        operator_prefix = "019"
    try:
        error = False
        error_msg = ""
        sms_rates = sms_rates.get(operator=operator_name, prefix=operator_prefix)
        if str(sms_category).lower() == "masking":
            sms_rate = sms_rates.masking_rate
        else:
            sms_rate = sms_rates.non_masking_rate
    except Exception as e:
        error_msg = str(e)
        error = True
        writeErrorLog(request, e)
    return error, error_msg, operator_name, sms_rate
