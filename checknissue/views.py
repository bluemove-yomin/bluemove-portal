from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# models
from django.contrib.auth.models import User
from .models import *

# Django auth
from django.contrib.auth import logout

# Google OAuth 2.0
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials

# django-allauth (https://django-allauth.readthedocs.io/en/latest/index.html)
from allauth.socialaccount.models import SocialToken

# Gmail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# NCP SENS
import hmac, hashlib
import time, requests, json

# verification
import random, string, datetime

# cert
import io, os
from googleapiclient.http import MediaIoBaseDownload

# multiple functions
import base64

# secrets
google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID")
google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")
google_sa_secret = getattr(settings, "GOOGLE_SA_SECRET", "GOOGLE_SA_SECRET")
google_sa_creds = "googleSACreds.json"
google_delegated_email = getattr(
    settings, "GOOGLE_DELEGATED_EMAIL", "GOOGLE_DELEGATED_EMAIL"
)
ncp_sens_id = getattr(settings, "NCP_SENS_ID", "NCP_SENS_ID")
ncp_key_id = getattr(settings, "NCP_KEY_ID", "NCP_KEY_ID")
ncp_secret = getattr(settings, "NCP_SECRET", "NCP_SECRET")

# Google API (User)
## Google Sheets
# portal_user_id = User.objects.filter(email="portal@bluemove.or.kr")[0]
# token = SocialToken.objects.get(
#     account__user=portal_user_id, account__provider="google"
# )
# credentials = Credentials(
#     client_id=google_client_id,
#     client_secret=google_client_secret,
#     token_uri="https://oauth2.googleapis.com/token",
#     refresh_token=token.token_secret,
#     token=token.token,
# )
# sheets_service = build("sheets", "v4", credentials=credentials)

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
drive_service = build("drive", "v3", credentials=credentials_delegated)
sheets_service = build("sheets", "v4", credentials=credentials_delegated)
slides_service = build("slides", "v1", credentials=credentials_delegated)
mail_service = build("gmail", "v1", credentials=credentials_delegated)

# Bluemove data
register_id = "1HkfnZ-2udmQAgE3u8o54rj6ek6IpcDFPjsgX4ycFATs"
cert_temp_id = "1t6dIVahi512hK-KHqIWXGT4Gy3RPJ8BkpJN5vu3UERY"
cert_folder_id = "1OmoM9u3RbaZe6N6KuQI2aBYW6ncCaGqa"
cert_log_id = "1RsjxAgPdd87m3ztfc6AHFZvRntNuUc5uu_4lalrY17I"


####
#### utils
####
def end_date(end_date):
    if end_date == "현재":
        return "현재"
    else:
        year = end_date.split("-")[0]
        month = end_date.split("-")[1]
        day = end_date.split("-")[2]
        return year + "년 " + month + "월 " + day + "일"


def gmail_message(
    str_cert_name=None,
    obj_alumni_row=None,
    str_v_code=None,
    str_alumni_name=None,
    str_alumni_email=None,
):
    # a mail for a certificate
    if str_cert_name:
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + obj_alumni_row[2]
            + """ 블루무버님의 활동증명서입니다.</title>
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
                                                                                        <img align="left"
                                                                                            src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/681b79e3-e459-6f97-567b-928c8229a6c9.png"
                                                                                            alt="블루무브 포털"
                                                                                            width="110"
                                                                                            style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                            class="mcnRetinaImage">
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
            + obj_alumni_row[2]
            + """ 블루무버님의 활동증명서입니다.
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
            + obj_alumni_row[2]
            + """ 블루무버님!<br>
                                                                                            발급된 활동증명서를 첨부 파일로 보내드립니다.
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
                                                                                                        style="padding: 18px;color: #545859;font-size: 14px;font-weight: normal;">
                                                                                                        <b>성명</b>: """
            + obj_alumni_row[2]
            + """<br>
                                                                                                        <b>기간</b>: """
            + obj_alumni_row[1]
            + """<br>
                                                                                                        <b>소속 및 역할</b>: """
            + obj_alumni_row[3]
            + """<br>
                                                                                                        <b>활동 내용</b>: """
            + obj_alumni_row[8]
            + """<br>
                                                                                                        <b>활동 기간</b>: """
            + obj_alumni_row[4]
            + """ ~ """
            + obj_alumni_row[6]
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
                                                                                            활동증명서 발급과 관련하여 궁금한 점이 있으실 경우 아래 연락처로 문의해주시기 바랍니다.
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
        message = MIMEMultipart()
        message["from"] = "Bluemove Portal <" + google_delegated_email + ">"
        message["to"] = obj_alumni_row[12]
        message["subject"] = obj_alumni_row[2] + " 블루무버님의 활동증명서입니다."
        main_type, sub_type = "application/pdf".split("/", 1)
        temp = open(str_cert_name, "rb")
        attachment = MIMEApplication(temp.read(), _subtype=sub_type)
        temp.close()
        attachment.add_header(
            "Content-Disposition", "attachment", filename=str_cert_name
        )
        message.attach(MIMEText(message_text, "html"))
        message.attach(attachment)
    # a mail for verification code
    elif str_v_code:
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + str_alumni_name
            + """님의 블루무버 얼럼나이 인증 코드입니다.</title>
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
                                                                                        <img align="left"
                                                                                            src="https://mcusercontent.com/8e85249d3fe980e2482c148b1/images/681b79e3-e459-6f97-567b-928c8229a6c9.png"
                                                                                            alt="블루무브 포털"
                                                                                            width="110"
                                                                                            style="max-width:1000px; padding-bottom: 0; display: inline !important; vertical-align: bottom;"
                                                                                            class="mcnRetinaImage">
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
            + str_alumni_name
            + """님의 블루무버 얼럼나이 인증 코드입니다.
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
            + str_alumni_name
            + """님!<br>
                                                                                            활동증명서 발급을 위한 블루무버 얼럼나이 인증 코드를 보내드립니다.
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
                                                                                            활동증명서 발급 페이지에서 위 10자리 코드를 입력해주시기 바랍니다.<br>
                                                                                            만약 블루무버 얼럼나이 인증 코드를 요청한 적이 없으실 경우 이 메일을 무시해주시기 바랍니다.
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
        message["to"] = str_alumni_email
        message["subject"] = str_alumni_name + "님의 블루무버 얼럼나이 인증 코드입니다."
    message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf8")}
    return message


def ncp_sens_message(str_to=None, str_vcode=None):
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
    message = f"[블루무브] 인증 코드는 {str_vcode} 입니다."
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


####
#### views
####
def checklist(request):
    # str
    q = request.GET.get("q")
    # get a register (public values)
    bluemover_list = (
        sheets_service.spreadsheets()
        .values()
        .get(
            spreadsheetId=register_id,
            range="register!A:F",
            majorDimension="ROWS",
        )
        .execute()
    ).get("values")
    del bluemover_list[0]
    bluemover_list.reverse()
    # search
    try:
        if len(q) > 1:
            bluemover_list_pre = [
                bluemover_row
                for bluemover_row in bluemover_list
                for bluemover_str in bluemover_row
                if q in bluemover_str
            ]
            bluemover_list = []
            for i in bluemover_list_pre:
                if i not in bluemover_list:
                    bluemover_list.append(i)
        else:
            pass
    except:
        q = None
    # paginator
    page = request.GET.get("page", 1)
    paginator = Paginator(bluemover_list, 15)
    try:
        bluemover_list = paginator.page(page)
    except PageNotAnInteger:
        bluemover_list = paginator.page(1)
    except EmptyPage:
        bluemover_list = paginator.page(paginator.num_pages)
    return render(
        request,
        "checknissue/checklist.html",
        {"bluemover_list": bluemover_list, "q": q},
    )


def checkcert(request):
    # str, lst
    alumni_id = request.POST.get("alumniId")
    d_code = request.POST.get("dCode")
    issue_date = ""
    alumni_list = []
    # boolean
    verified = None
    unable_to_verify = None
    if request.method == "POST":
        # get a certificate log
        cert_list = (
            sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=cert_log_id,
                range="certLog!A:F",
                majorDimension="ROWS",
            )
            .execute()
        ).get("values")
        del cert_list[0]
        for cert_row in cert_list:
            if alumni_id in cert_row and d_code in cert_row:
                verified = True
                issue_date = cert_row[0][:10]
                # get a register (private values)
                bluemover_list = (
                    sheets_service.spreadsheets()
                    .values()
                    .get(
                        spreadsheetId=register_id,
                        range="register!A:M",
                        majorDimension="ROWS",
                    )
                    .execute()
                ).get("values")
                del bluemover_list[0]
                alumni_list = [
                    bluemover_row
                    for bluemover_row in bluemover_list
                    if (
                        cert_row[1] in bluemover_row
                        and cert_row[2] in bluemover_row
                        and cert_row[3] in bluemover_row[12]
                    )
                ]
            else:
                unable_to_verify = True
    return render(
        request,
        "checknissue/checkcert.html",
        {
            # str, lst
            "alumni_id": alumni_id,
            "d_code": d_code,
            "issue_date": issue_date,
            "alumni_list": alumni_list,
            # boolean
            "verified": verified,
            "unable_to_verify": unable_to_verify,
        },
    )


def issuecert(request):
    # str, lst
    alumni_name = request.POST.get("alumniName")
    alumni_birth = request.POST.get("alumniBirth")
    alumni_phone = request.POST.get("alumniPhone")
    alumni_email = request.POST.get("alumniEmail")
    v_code_input = request.POST.get("vCode")
    old_cert_datetime = ""
    alumni_list = []
    # cmd
    cmd_get = request.GET.get("cmdGet")
    cmd_post = request.POST.get("cmdPost")
    # boolean
    alumni = None
    new_member = None
    unable_to_verify = None
    verified = None
    wrong_v_code = None
    issued = None
    init_required = None
    old_cert_exists = None
    # initialize verification
    if cmd_get == "init":
        v_code_obj = Issuecert.objects.filter(
            birthday=request.GET.get("bd"),
            phone_last=request.GET.get("pl"),
            email_host=request.GET.get("eh"),
        )
        v_code_obj.delete()
        return redirect("checknissue:issuecert")
    # get a register (private values)
    bluemover_list = (
        sheets_service.spreadsheets()
        .values()
        .get(
            spreadsheetId=register_id,
            range="register!A:M",
            majorDimension="ROWS",
        )
        .execute()
    ).get("values")
    del bluemover_list[0]
    alumni_list = [
        bluemover_row
        for bluemover_row in bluemover_list
        if (
            alumni_name in bluemover_row
            and alumni_birth in bluemover_row
            and alumni_phone in bluemover_row
            and alumni_email in bluemover_row
        )
    ]
    # issue a certificate
    if request.method == "POST" and cmd_post == "issue":
        cert_list = (
            sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=cert_log_id,
                range="certLog!A:F",
                majorDimension="ROWS",
            )
            .execute()
        ).get("values")
        del cert_list[0]
        for cert_row in cert_list:
            if v_code_input in cert_row:
                init_required = True
                return render(
                    request,
                    "checknissue/issuecert.html",
                    {
                        # str, lst
                        "alumni_name": alumni_name,
                        "alumni_birth": alumni_birth,
                        "alumni_phone": alumni_phone,
                        "alumni_email": alumni_email,
                        "v_code_input": v_code_input,
                        "alumni_list": alumni_list,
                        # boolean
                        "init_required": init_required,
                    },
                )
        for alumni_row in alumni_list:
            cert_id = (
                drive_service.files()
                .copy(
                    fileId=cert_temp_id,
                    supportsAllDrives=True,
                    body={
                        "name": "DEV_활동증명서"
                        + alumni_row[2]
                        + alumni_row[9][5:7]
                        + alumni_row[9][8:10]
                        + alumni_row[11][-4:]
                        + "_"
                        + datetime.date.today().strftime("%y%m%d"),
                        "parents": [cert_folder_id],
                    },
                    fields="id",
                )
                .execute()
                .get("id")
            )
            d_code = ""
            for i in range(16):
                d_code += random.choice(string.ascii_uppercase + string.digits)
            d_code = (
                d_code[0:4]
                + "-"
                + d_code[4:8]
                + "-"
                + d_code[8:12]
                + "-"
                + d_code[12:16]
            )
            slides_service.presentations().batchUpdate(
                presentationId=cert_id,
                body={
                    "requests": [
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ name }}",
                                    "matchCase": "true",
                                },
                                "replaceText": alumni_row[2],
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ team_n_role }}",
                                    "matchCase": "true",
                                },
                                "replaceText": alumni_row[3],
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ id }}",
                                    "matchCase": "true",
                                },
                                "replaceText": alumni_row[0],
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ d_code }}",
                                    "matchCase": "true",
                                },
                                "replaceText": d_code,
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ activity_detail }}",
                                    "matchCase": "true",
                                },
                                "replaceText": alumni_row[8],
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ activity_period }}",
                                    "matchCase": "true",
                                },
                                "replaceText": alumni_row[4].split("-")[0]
                                + "년 "
                                + alumni_row[4].split("-")[1]
                                + "월 "
                                + alumni_row[4].split("-")[2]
                                + "일 ~ "
                                + end_date(alumni_row[6]),
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ period }}",
                                    "matchCase": "true",
                                },
                                "replaceText": alumni_row[1],
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ issue_date }}",
                                    "matchCase": "true",
                                },
                                "replaceText": datetime.date.today().strftime("%Y")
                                + "년 "
                                + datetime.date.today().strftime("%m")
                                + "월 "
                                + datetime.date.today().strftime("%d")
                                + "일",
                            }
                        },
                    ]
                },
            ).execute()
            cert = drive_service.files().export(
                fileId=cert_id, mimeType="application/pdf"
            )
            cert_name = (
                "블루무브포털_활동증명서"
                + alumni_row[2]
                + v_code_input
                + "_"
                + datetime.date.today().strftime("%y%m%d")
                + ".pdf"
            )
            fh = io.FileIO(cert_name, "wb")
            downloader = MediaIoBaseDownload(fh, cert)
            done = False
            while done is False:
                done = downloader.next_chunk()
            fh.close()
            drive_service.files().delete(
                fileId=cert_id,
                supportsAllDrives=True,
            ).execute()
            for cert_row in cert_list:
                if alumni_name in cert_row and alumni_email.split("@")[1] in cert_row:
                    sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=cert_log_id,
                        body={
                            "requests": [
                                {
                                    "findReplace": {
                                        "find": cert_row[5],
                                        "replacement": "INVALID",
                                        "allSheets": True,
                                    }
                                },
                            ]
                        },
                    ).execute()
                    old_cert_exists = True
                    old_cert_datetime = (
                        cert_row[0][:4]
                        + "년 "
                        + cert_row[0][5:7]
                        + "월 "
                        + cert_row[0][8:10]
                        + "일 "
                        + cert_row[0][11:13]
                        + "시 "
                        + cert_row[0][14:16]
                        + "분"
                    )
            sheets_service.spreadsheets().values().append(
                spreadsheetId=cert_log_id,
                range="certLog!A1:F1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={
                    "values": [
                        [
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            alumni_row[0],
                            alumni_row[2],
                            alumni_email.split("@")[1],
                            v_code_input,
                            d_code,
                        ]
                    ]
                },
            ).execute()
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=cert_log_id,
                body={
                    "requests": [
                        {
                            "updateSpreadsheetProperties": {
                                "properties": {
                                    "title": "E01_활동증명서발급내역_"
                                    + datetime.datetime.now().strftime("%y%m%d")
                                },
                                "fields": "title",
                            }
                        },
                    ]
                },
            ).execute()
            mail_service.users().messages().send(
                userId=google_delegated_email,
                body=gmail_message(
                    str_cert_name=cert_name,
                    obj_alumni_row=alumni_row,
                ),
            ).execute()
            os.remove(cert_name)
            issued = True
    # verification code validation
    elif request.method == "POST" and v_code_input:
        v_code_obj = Issuecert.objects.filter(
            birthday=alumni_birth[5:7] + alumni_birth[8:10],
            phone_last=alumni_phone[-4:],
            email_host=alumni_email.split("@")[1],
            code=v_code_input,
        )
        if v_code_obj:
            v_code_obj.delete()
            verified = True
        else:
            wrong_v_code = True
    # membership check
    elif request.method == "POST":
        for bluemover_row in bluemover_list:
            if (
                alumni_name in bluemover_row
                and alumni_birth in bluemover_row
                and alumni_phone in bluemover_row
                and alumni_email in bluemover_row
                and "alumni_true" in bluemover_row
            ):
                v_code = ""
                try:
                    v_code_obj = Issuecert.objects.filter(
                        birthday=alumni_birth[5:7] + alumni_birth[8:10],
                        phone_last=alumni_phone[-4:],
                        email_host=alumni_email.split("@")[1],
                    )
                    v_code_obj.delete()
                except:
                    pass
                for i in range(10):
                    v_code += random.choice(string.ascii_uppercase + string.digits)
                Issuecert.objects.create(
                    birthday=alumni_birth[5:7] + alumni_birth[8:10],
                    phone_last=alumni_phone[-4:],
                    email_host=alumni_email.split("@")[1],
                    code=v_code,
                )
                mail_service.users().messages().send(
                    userId=google_delegated_email,
                    body=gmail_message(
                        str_v_code=v_code,
                        str_alumni_name=alumni_name,
                        str_alumni_email=alumni_email,
                    ),
                ).execute()
                alumni = True
            elif (
                alumni_name in bluemover_row
                and alumni_birth in bluemover_row
                and alumni_phone in bluemover_row
                and alumni_email in bluemover_row
                and "alumni_false" in bluemover_row
            ):
                new_member = True
            else:
                unable_to_verify = True
    return render(
        request,
        "checknissue/issuecert.html",
        {
            # str, lst
            "alumni_name": alumni_name,
            "alumni_birth": alumni_birth,
            "alumni_phone": alumni_phone,
            "alumni_email": alumni_email,
            "v_code_input": v_code_input,
            "alumni_list": alumni_list,
            "old_cert_datetime": old_cert_datetime,
            # boolean
            "alumni": alumni,
            "new_member": new_member,
            "unable_to_verify": unable_to_verify,
            "verified": verified,
            "wrong_v_code": wrong_v_code,
            "issued": issued,
            "init_required": init_required,
            "old_cert_exists": old_cert_exists,
        },
    )
