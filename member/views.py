from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

# models
from django.contrib.auth.models import User
from .models import Profile, Signupvcode
from applynsubmit.models import Applymembership

# Slack
from slack_sdk import WebClient

# NCP SENS
import hmac, hashlib
import time, requests, json

# varification
import random, string

# multiple functions
import re
import datetime
import base64
from django.http import HttpResponse
from django.http import JsonResponse

# secrets
slack_bot_token = getattr(settings, "SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN")
ncp_sens_id = "ncp:sms:kr:270162116975:bluemove-portal"
ncp_key_id = "6mYnNwIE99gB11D9k2Xa"
ncp_secret = "ZqkivXWO0N5G7EgowbOsnWBnkBz1vwM1IYJc3nF8"

# Bluemove data
management_all_channel_id = "CV3THBHJB"
management_dev_channel_id = "C01L8PETS5S"


####
#### utils
####
def ncp_sens_message(str_to=None, str_v_code=None):
    sid = ncp_sens_id
    sms_uri = f"/sms/v2/services/{sid}/messages"
    sms_url = f"https://sens.apigw.ntruss.com{sms_uri}"
    acc_key_id = ncp_key_id
    acc_sec_key = bytes(ncp_secret, "utf-8")
    stime = int(float(time.time()) * 1000)
    hash_str = f"POST {sms_uri}\n{stime}\n{acc_key_id}"
    digest = hmac.new(
        acc_sec_key, msg=hash_str.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    d_hash = base64.b64encode(digest).decode()
    from_no = "0232960613"
    to_no = str_to
    message = f"[블루무브] 인증 번호는 {str_v_code} 입니다."
    msg_data = {
        "type": "SMS",
        "countryCode": "82",
        "from": f"{from_no}",
        "contentType": "COMM",
        "content": f"{message}",
        "messages": [{"to": f"{to_no}"}],
    }
    response = requests.post(
        sms_url,
        data=json.dumps(msg_data),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": str(stime),
            "x-ncp-iam-access-key": acc_key_id,
            "x-ncp-apigw-signature-v2": d_hash,
        },
    )
    return response.text


def phone_num_validation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if "#" in data:
            last_name = data.split("#")[0]
            phone_num = data.split("#")[1].replace("-", "")
            v_code_input_value = data.split("#")[2]
            try:
                v_code_obj = Signupvcode.objects.get(
                    last_name=last_name,
                    phone_last_five_digits=phone_num[6:],
                    code=v_code_input_value,
                )
                if v_code_obj.will_expire_on > datetime.datetime.now():
                    context = {"status": "passed"}
                    v_code_obj.will_expire_on = (
                        datetime.datetime.now() + datetime.timedelta(minutes=1)
                    )
                else:
                    context = {"status": "expired"}
            except:
                context = {"status": "failed"}
        elif "$" in data:
            last_name = data.split("$")[0]
            phone_num = data.split("$")[1].replace("-", "")
            v_code = ""
            for i in range(6):
                v_code += random.choice(string.digits)
            response = ncp_sens_message(str_to=phone_num, str_v_code=v_code)
            status_code = json.loads(response).get("statusCode")
            will_expire_on = datetime.datetime.now() + datetime.timedelta(minutes=1)
            if status_code[0] == "2":
                Signupvcode.objects.create(
                    last_name=last_name,
                    phone_last_five_digits=phone_num[6:],
                    code=v_code,
                    will_expire_on=will_expire_on,
                )
                context = {"status": "generated"}
            else:
                context = {"status": status_code}
    return JsonResponse(context)


def privacy_masking(obj_user):
    masked_name = (
        obj_user.last_name
        + re.sub("[\S]", "*", obj_user.first_name[:-1])
        + obj_user.first_name[-1:]
    )
    masked_phone = (
        obj_user.profile.phone.split("-")[0]
        + "-"
        + obj_user.profile.phone.split("-")[1]
        + "-****"
    )
    masked_email = (
        obj_user.email.split("@")[0][0]
        + re.sub("[\S]", "*", obj_user.email.split("@")[0][1:])
        + "@"
        + obj_user.email.split("@")[1][0]
        + re.sub("[^.]", "*", obj_user.email.split("@")[1][1:])
    )
    return masked_name, masked_phone, masked_email


def slack_blocks_and_text(qrs_users_inactivated=None):
    if qrs_users_inactivated:
        users_list = []
        for obj_user in qrs_users_inactivated:
            masked_name, masked_phone, masked_email = privacy_masking(obj_user)
            users_list.append(
                "✅ " + masked_name + "님 (" + masked_phone + " / " + masked_email + ")"
            )
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"✂️ 비활성 계정 자동 삭제됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"30일 동안 미사용된 모든 비활성 계정이 자동 삭제되었습니다.",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*삭제된 계정 정보:*\n" + "\n".join(users_list),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*삭제일시:*\n"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        ]
        text = f"✂️ 비활성 계정 자동 삭제됨"
    return blocks, text


####
#### functions for incoming requests from outside
####
def cron_delete_all_expired_v_codes(request):
    expired_v_codes = Signupvcode.objects.filter(
        will_expire_on__lt=datetime.datetime.now()
    )
    if expired_v_codes:
        for v_code in expired_v_codes:
            v_code.delete()
    return HttpResponse(status=200)


def cron_delete_all_inactive_users(request):
    users_inactivated = User.objects.filter(
        last_login__lte=datetime.datetime.now() - datetime.timedelta(days=30)
    )
    if users_inactivated:
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(channel=management_all_channel_id)
        except:
            pass
        blocks, text = slack_blocks_and_text(qrs_users_inactivated=users_inactivated)
        client.chat_postMessage(
            channel=management_all_channel_id,
            link_names=True,
            as_user=True,
            blocks=blocks,
            text=text,
        )
        for user in users_inactivated:
            user.delete()
    return HttpResponse(status=200)


####
#### views
####
@login_required
def myaccount(request):
    # obj
    app = None
    # str, lst
    last_name = request.POST.get("last_name")
    first_name = request.POST.get("first_name")
    phone = request.POST.get("phone")
    delete_msg = request.POST.get("deleteMsg")
    v_code_input_value = request.POST.get("v_code")
    # boolean
    not_modified = None
    modified = None
    unable_to_delete = None
    wrong_delete_msg = None
    unable_to_modify = None
    scroll_to_modify = None
    scroll_to_delete = None
    if request.method == "POST" and not delete_msg:
        user = User.objects.get(id=request.user.id)
        profile = Profile.objects.get(user=request.user)
        if (
            user.last_name == last_name
            and user.first_name == first_name
            and profile.phone == phone
        ):
            not_modified = True
        elif not profile.phone == phone:
            try:
                v_code_obj = Signupvcode.objects.get(
                    last_name=last_name,
                    phone_last_five_digits=phone.replace("-", "")[6:],
                    code=v_code_input_value,
                )
                if v_code_obj:
                    user.last_name = last_name
                    user.first_name = first_name
                    user.save()
                    profile.phone = phone
                    profile.save()
                    modified = True
            except:
                unable_to_modify = True
        scroll_to_modify = True
    elif request.method == "POST" and delete_msg:
        try:
            app = Applymembership.objects.get(applicant=request.user, received=True)
        except:
            pass
        if delete_msg == request.user.email and not app:
            request.user.delete()
            return redirect("home:main")
        elif delete_msg == request.user.email and app:
            unable_to_delete = True
            scroll_to_delete = True
        elif not delete_msg == request.user.email:
            wrong_delete_msg = True
            scroll_to_delete = True
    return render(
        request,
        "member/myaccount.html",
        {
            # str, lst
            "delete_msg": delete_msg,
            "last_name": last_name,
            "first_name": first_name,
            # boolean
            "not_modified": not_modified,
            "modified": modified,
            "unable_to_delete": unable_to_delete,
            "wrong_delete_msg": wrong_delete_msg,
            "unable_to_modify": unable_to_modify,
            "scroll_to_modify": scroll_to_modify,
            "scroll_to_delete": scroll_to_delete,
        },
    )
