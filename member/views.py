from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

# models
from django.contrib.auth.models import User
from .models import Profile, Vcode
from applynsubmit.models import Applymembership

# Google OAuth 2.0
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials

# Gmail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

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
google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID")
google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")
google_sa_secret = getattr(settings, "GOOGLE_SA_SECRET", "GOOGLE_SA_SECRET")
google_sa_creds = "googleSACreds.json"
google_delegated_email = getattr(
    settings, "GOOGLE_DELEGATED_EMAIL", "GOOGLE_DELEGATED_EMAIL"
)
slack_bot_token = getattr(settings, "SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN")
ncp_key_id = getattr(settings, "NCP_KEY_ID", "NCP_KEY_ID")
ncp_secret = getattr(settings, "NCP_SECRET", "NCP_SECRET")
ncp_sens_id = getattr(settings, "NCP_SENS_ID", "NCP_SENS_ID")
ncp_knr_client_id = getattr(settings, "NCP_KNR_CLIENT_ID", "NCP_KNR_CLIENT_ID")
ncp_knr_client_secret = getattr(
    settings, "NCP_KNR_CLIENT_SECRET", "NCP_KNR_CLIENT_SECRET"
)

# Google API (SA)
sa_credentials = service_account.Credentials.from_service_account_file(
    google_sa_creds,
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/gmail.send",
    ],
)
credentials_delegated = sa_credentials.with_subject(google_delegated_email)
mail_service = build("gmail", "v1", credentials=credentials_delegated)

# Bluemove data
management_all_channel_id = "CV3THBHJB"
management_dev_channel_id = "C01L8PETS5S"


####
#### utils
####
def gmail_message(
    str_v_code=None,
    str_name=None,
    str_email=None,
):
    # a mail for verification code
    if str_v_code:
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + str_name
            + """님의 이메일 주소 인증 코드입니다.</title>
            </head>

            <body>
                <center style="font-family: AppleSDGothic, apple sd gothic neo, noto sans korean, noto sans korean regular, noto sans cjk kr, noto sans cjk, nanum gothic, malgun gothic, dotum, arial, helvetica, MS Gothic, sans-serif;">
                    <table align="center" border="0" cellpadding="0" cellspacing="0" height="100%" width="100%" id="bodyTable">
                        <tr>
                            <td align="center" valign="top" id="bodyCell">
                                <!-- BEGIN TEMPLATE // -->
                                <table align="center" border="0" cellspacing="0" cellpadding="0" width="600" style="width:600px;">
                                    <tr>
                                        <td align="center" valign="top" width="600" style="width:600px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                class="templateContainer">
                                                <tr>
                                                    <td valign="top" id="templatePreheader"></td>
                                                </tr>
                                                <tr>
                                                    <td valign="top" id="templateHeader">
                                                        <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                            class="mcnImageBlock" style="min-width:100%;">
                                                            <tbody class="mcnImageBlockOuter">
                                                                <tr>
                                                                    <td valign="top" style="padding:9px" class="mcnImageBlockInner">
                                                                        <table align="left" width="100%" border="0" cellpadding="0"
                                                                            cellspacing="0" class="mcnImageContentContainer"
                                                                            style="min-width:100%;">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td class="mcnImageContent" valign="top"
                                                                                        style="padding-right: 9px; padding-left: 9px; padding-top: 0; padding-bottom: 0;">
                                                                                        <a href="https://portal.bluemove.or.kr" target="_blank">
                                                                                            <img align="left"
                                                                                                src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/681b79e3-e459-6f97-567b-928c8229a6c9.png"
                                                                                                alt="블루무브 포털"
                                                                                                width="110"
                                                                                                style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                                class="mcnRetinaImage">
                                                                                        </a>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td valign="top" id="templateBody">
                                                        <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                            class="mcnTextBlock" style="min-width:100%;">
                                                            <tbody class="mcnTextBlockOuter">
                                                                <tr>
                                                                    <td valign="top" class="mcnTextBlockInner"
                                                                        style="padding-top:9px;">
                                                                        <table align="left" border="0" cellpadding="0"
                                                                            cellspacing="0" style="max-width:100%; min-width:100%;"
                                                                            width="100%" class="mcnTextContentContainer">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td valign="top" class="mcnTextContent"
                                                                                        style="padding-top:0; padding-right:18px; padding-bottom:0px; padding-left:18px;">
                                                                                        <h1>
                                                                                            """
            + str_name
            + """님의 이메일 주소 인증 코드입니다.
                                                                                        </h1>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                        <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                            class="mcnTextBlock" style="min-width:100%;">
                                                            <tbody class="mcnTextBlockOuter">
                                                                <tr>
                                                                    <td valign="top" class="mcnTextBlockInner"
                                                                        style="padding-top:9px;">
                                                                        <table align="left" border="0" cellpadding="0"
                                                                            cellspacing="0" style="max-width:100%; min-width:100%;"
                                                                            width="100%" class="mcnTextContentContainer">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td valign="top" class="mcnTextContent"
                                                                                        style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px; font-size:14px;">
                                                                                        <p>
                                                                                            안녕하세요, """
            + str_name
            + """님!<br>
                                                                                            가입 확정을 위한 이메일 주소 인증 코드를 보내드립니다.
                                                                                        </p>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                        <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                            class="mcnBoxedTextBlock" style="min-width:100%;">
                                                            <tbody class="mcnBoxedTextBlockOuter">
                                                                <tr>
                                                                    <td valign="top" class="mcnBoxedTextBlockInner">
                                                                        <table align="left" border="0" cellpadding="0"
                                                                            cellspacing="0" width="100%" style="min-width:100%;"
                                                                            class="mcnBoxedTextContentContainer">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td
                                                                                        style="padding-top:9px; padding-left:18px; padding-bottom:9px; padding-right:18px;">
                                                                                        <table border="0" cellspacing="0"
                                                                                            class="mcnTextContentContainer"
                                                                                            width="100%"
                                                                                            style="min-width: 100% !important;background-color: #F7F7F7;">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td valign="top"
                                                                                                        class="mcnTextContent"
                                                                                                        style="padding: 18px;color: #545859;font-size: 14px;font-weight: normal; text-align: center;">
                                                                                                        """
            + str_v_code
            + """
                                                                                                    </td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                        <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                            class="mcnTextBlock" style="min-width:100%;">
                                                            <tbody class="mcnTextBlockOuter">
                                                                <tr>
                                                                    <td valign="top" class="mcnTextBlockInner"
                                                                        style="padding-top:9px;">
                                                                        <table align="left" border="0" cellpadding="0"
                                                                            cellspacing="0" style="max-width:100%; min-width:100%;"
                                                                            width="100%" class="mcnTextContentContainer">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td valign="top" class="mcnTextContent"
                                                                                        style="padding-top:0; padding-right:18px; padding-bottom:9px; padding-left:18px; font-size:14px;">
                                                                                        <p>
                                                                                            가입 확정 단계에서 위 10자리 코드를 입력해주시기 바랍니다.<br>
                                                                                            만약 이메일 주소 인증 코드를 요청한 적이 없으실 경우 이 메일을 무시해주시기 바랍니다.
                                                                                        </p>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td valign="top" id="templateFooter">
                                                        <table border="0" cellpadding="0" cellspacing="0" width="100%"
                                                            class="mcnTextBlock" style="min-width:100%;">
                                                            <tbody class="mcnTextBlockOuter">
                                                                <tr>
                                                                    <td valign="top" class="mcnTextBlockInner"
                                                                        style="padding-top:9px;">
                                                                        <table align="left" border="0" cellpadding="0"
                                                                            cellspacing="0" style="max-width:100%; min-width:100%;"
                                                                            width="100%" class="mcnTextContentContainer">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td valign="top" class="mcnTextContent"
                                                                                        style="padding: 0px 18px 9px; text-align: left;">
                                                                                        <hr
                                                                                            style="border:0;height:.5px;background-color:#EEEEEE;">
                                                                                        <small style="color: #545859;">
                                                                                            이 메일은 블루무브 포털에서 자동 발송되었습니다. 궁금한 점이 있으실
                                                                                            경우 <a
                                                                                                href="mailto:management@bluemove.or.kr">management@bluemove.or.kr</a>로
                                                                                            문의해주시기 바랍니다.<br>
                                                                                            ⓒ 파란물결 블루무브
                                                                                        </small>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                <!-- // END TEMPLATE -->
                            </td>
                        </tr>
                    </table>
                </center>
            </body>

            </html>
            """
        )
        message = MIMEText(message_text, "html")
        message["from"] = "Bluemove Portal <" + google_delegated_email + ">"
        message["to"] = str_email
        message["subject"] = str_name + "님의 이메일 주소 인증 코드입니다."
    message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf8")}
    return message


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
                v_code_obj = Vcode.objects.get(
                    last_name=last_name,
                    phone_last_five_digits=phone_num[6:],
                    code=v_code_input_value,
                )
                if v_code_obj.will_expire_on > datetime.datetime.now():
                    context = {"status": "passed"}
                    v_code_obj.will_expire_on = (
                        datetime.datetime.now() + datetime.timedelta(minutes=1)
                    )
                    v_code_obj.save()
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
                Vcode.objects.create(
                    last_name=last_name,
                    phone_last_five_digits=phone_num[6:],
                    code=v_code,
                    will_expire_on=will_expire_on,
                )
                context = {"status": "generated"}
            else:
                context = {"status": status_code}
    return JsonResponse(context)


def email_addr_validation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if "#" in data:
            email_addr = data.split("#")[0]
            v_code_input_value = data.split("#")[1]
            try:
                v_code_obj = Vcode.objects.get(
                    last_name=request.user.last_name,
                    email_last_letter_with_host=email_addr.split("@")[0][-1] + email_addr.split("@")[1],
                    code=v_code_input_value,
                )
                if v_code_obj.will_expire_on > datetime.datetime.now():
                    context = {"status": "passed"}
                    v_code_obj.will_expire_on = (
                        datetime.datetime.now() + datetime.timedelta(minutes=1)
                    )
                    v_code_obj.save()
                else:
                    context = {"status": "expired"}
            except:
                context = {"status": "failed"}
        elif "@" in data and not "#" in data:
            email_addr = data
            v_code = ""
            for i in range(10):
                v_code += random.choice(string.ascii_uppercase + string.digits)
            mail_service.users().messages().send(
                userId=google_delegated_email,
                body=gmail_message(
                    str_v_code=v_code,
                    str_name=request.user.last_name + request.user.first_name,
                    str_email=email_addr,
                ),
            ).execute()
            will_expire_on = datetime.datetime.now() + datetime.timedelta(minutes=3)
            Vcode.objects.create(
                last_name=request.user.last_name,
                email_last_letter_with_host=email_addr.split("@")[0][-1] + email_addr.split("@")[1],
                code=v_code,
                will_expire_on=will_expire_on,
            )
            context = {"status": "generated"}
    return JsonResponse(context)


def kor_name_romanizer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        response = (
            json.loads(
                requests.get(
                    "https://naveropenapi.apigw.ntruss.com/krdict/v1/romanization",
                    params={
                        "query": data,
                    },
                    headers={
                        "X-NCP-APIGW-API-KEY-ID": ncp_knr_client_id,
                        "X-NCP-APIGW-API-KEY": ncp_knr_client_secret,
                    },
                ).text
            )
            .get("aResult")[0]
            .get("aItems")[0]
        )
    return JsonResponse(response)


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
    expired_v_codes = Vcode.objects.filter(
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
                v_code_obj = Vcode.objects.get(
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
