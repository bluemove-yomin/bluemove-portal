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
import base64
import time

# Notion
import requests, json

# Slack
from slack_sdk import WebClient
import re

# Mailchimp
from mailchimp_marketing import Client
import hashlib

# user-agents (https://github.com/selwin/python-user-agents)
import user_agents

# Beautiful Soup (https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
from bs4 import BeautifulSoup

# dateutil (https://github.com/dateutil/dateutil)
from dateutil import parser

# verification
import random, string

# multiple functions
import datetime
from django.http import HttpResponse
import ast

# secrets
google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID")
google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")
google_sa_secret = getattr(settings, "GOOGLE_SA_SECRET", "GOOGLE_SA_SECRET")
google_sa_creds = "googleSACreds.json"
google_delegated_email = getattr(
    settings, "GOOGLE_DELEGATED_EMAIL", "GOOGLE_DELEGATED_EMAIL"
)
notion_token = getattr(settings, "NOTION_TOKEN", "NOTION_TOKEN")
slack_bot_token = getattr(settings, "SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN")
mailchimp_key = getattr(settings, "MAILCHIMP_KEY", "MAILCHIMP_KEY")

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
mail_service = build("gmail", "v1", credentials=credentials_delegated)

# Notion API
notion_headers = {
    "Authorization": f"Bearer " + notion_token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-08-16",
}

# Oopy scraping
bs4_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
}

# Mailchimp API
mailchimp = Client()
mailchimp.set_config({"api_key": mailchimp_key, "server": mailchimp_key.split("-")[1]})

# Bluemove data
wanted_db_id = "7e8e8ec2-93c9-496e-ada9-40ab78572bbb"
management_all_channel_id = "CV3THBHJB"
management_dev_channel_id = "C01L8PETS5S"
register_id = "1HkfnZ-2udmQAgE3u8o54rj6ek6IpcDFPjsgX4ycFATs"
register_sheet_id = "2123333259"
mailchimp_bluemover_list_id = "275e141904"


####
#### utils
####
def wanted_datetime_day_split(int_datetime_day_num):
    if int_datetime_day_num == "1":
        return "(월)"
    elif int_datetime_day_num == "2":
        return "(화)"
    elif int_datetime_day_num == "3":
        return "(수)"
    elif int_datetime_day_num == "4":
        return "(목)"
    elif int_datetime_day_num == "5":
        return "(금)"
    elif int_datetime_day_num == "6":
        return "(토)"
    elif int_datetime_day_num == "0":
        return "(일)"
    else:
        return ""


def reception_closed(str_ISO_8601):
    return parser.parse(str_ISO_8601).strftime(
        "%Y-%m-%d %H:%M:%S"
    ) < datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def len_including_empty_lines(text):
    empty_lines_list = []
    for line in text:
        if line == "\n" or line == "\r\n":
            empty_lines_list.append(line)
    return len(text) - len(empty_lines_list)


def save_the_app(
    obj_app,
    str_wanted_title,
    str_self_intro,
    str_reason,
    str_plan,
    str_tracking,
    str_tracking_reference,
    str_tracking_etc,
    str_portfolio,
):
    obj_app.wanted_title = str_wanted_title
    obj_app.self_intro = str_self_intro
    obj_app.self_intro_len = len_including_empty_lines(str_self_intro)
    obj_app.reason = str_reason
    obj_app.reason_len = len_including_empty_lines(str_reason)
    obj_app.plan = str_plan
    obj_app.plan_len = len_including_empty_lines(str_plan)
    obj_app.tracking = str_tracking
    obj_app.tracking_reference = str_tracking_reference
    obj_app.tracking_etc = str_tracking_etc
    obj_app.portfolio = str_portfolio
    return obj_app.save()


def save_the_noti(
    request,
    obj_noti,
    str_wanted_title,
    str_title,
    str_passed_content,
    str_failed_content,
):
    obj_noti.wanted_title = str_wanted_title
    obj_noti.title = str_title
    obj_noti.passed_content = str_passed_content
    obj_noti.failed_content = str_failed_content
    obj_noti.saved_by = request.user
    return obj_noti.save()


def privacy_masking(
    str_name=None,
    str_birth=None,
    str_phone=None,
    str_email=None,
):
    masked_name = (
        str_name[:1] + re.sub("[\S]", "*", str_name[1:-1]) + str_name[-1:]
        if str_name
        else None
    )
    masked_birth = (
        re.sub("[\S]", "*", str_birth.split("-")[0])
        + "-"
        + str_birth.split("-")[1]
        + "-"
        + str_birth.split("-")[2]
        if str_birth
        else None
    )
    masked_phone = (
        str_phone.split("-")[0]
        + "-"
        + str_phone.split("-")[1]
        + "-"
        + re.sub("[\S]", "*", str_phone.split("-")[2])
        if str_phone
        else None
    )
    masked_email = (
        str_email.split("@")[0][:2]
        + re.sub("[\S]", "*", str_email.split("@")[0][2:])
        + "@"
        + str_email.split("@")[1][:1]
        + re.sub("[^.]", "*", str_email.split("@")[1][1:])
        if str_email
        else None
    )
    return masked_name, masked_birth, masked_phone, masked_email


def gmail_message(
    request=None,
    obj_app=None,
    obj_noti=None,
    obj_queued_alumni=None,
    str_wanted_id=None,
    str_wanted_title=None,
    str_title=None,
    str_passed_content=None,
    str_failed_content=None,
    str_v_code=None,
    str_alumni_name=None,
    str_alumni_email=None,
    signal_removed_from_queue=None,
    signal_gone=None,
):
    # a mail to the applicant who submitted the application
    if obj_app:
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + obj_app.applicant.last_name
            + obj_app.applicant.first_name
            + """님의 지원서가 접수되었습니다.</title>
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
            + obj_app.applicant.last_name
            + obj_app.applicant.first_name
            + """님의 지원서가 접수되었습니다.
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
            + obj_app.applicant.last_name
            + obj_app.applicant.first_name
            + """님!<br>
                                                                                            """
            + obj_app.applicant.first_name
            + """님께서 작성해주신 소중한 지원서가 잘 접수되었습니다.
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
            + obj_app.applicant.last_name
            + obj_app.applicant.first_name
            + """<br>
                                                                                                        <b>공고명</b>: """
            + str_wanted_title
            + """<br>
                                                                                                        <b>접수일시</b>: """
            + obj_app.received_at.strftime("%Y-%m-%d %H:%M:%S")
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
                                                                                            블루무브 가입을 지원해주셔서 진심으로 감사드립니다.<br>
                                                                                            리크루팅과 관련하여 궁금한 점이 있으실 경우 아래 연락처로 문의해주시기 바랍니다.
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
                                                            class="mcnButtonBlock" style="min-width:100%;">
                                                            <tbody class="mcnButtonBlockOuter">
                                                                <tr>
                                                                    <td width="100%" valign="top" align="center" class="mcnButtonBlockInner"
                                                                        style="min-width:100%; padding-top:9px; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                        <a class="mcnButton" title="접수된 지원서 확인" href='"""
            + request.build_absolute_uri()
            + """#app' target="_blank"
                                                                            style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">
                                                                            <table border="0" cellpadding="0" cellspacing="0"
                                                                                width="100%" class="mcnButtonContentContainer"
                                                                                style="min-width:100%; border-collapse: separate !important;border-radius: 4px;background-color: #0077C8;">
                                                                                <tbody>
                                                                                    <tr>
                                                                                        <td align="center"
                                                                                            valign="middle" class="mcnButtonContent"
                                                                                            style="font-size: 16px; padding: 12px;">
                                                                                            접수된 지원서 확인
                                                                                        </td>
                                                                                    </tr>
                                                                                </tbody>
                                                                            </table>
                                                                        </a>
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
        message["to"] = obj_app.applicant.email
        message["subject"] = (
            obj_app.applicant.last_name
            + obj_app.applicant.first_name
            + "님의 지원서가 접수되었습니다."
        )
    # mails to passed applicants
    if obj_noti and str_passed_content:
        bcc_list = []
        apps_passed = Applymembership.objects.filter(
            wanted_id=str_wanted_id, received=True, pf="선발"
        )
        for app in apps_passed:
            bcc_list.append(app.applicant.email)
        if "\n" in str_passed_content:
            str_passed_content = str_passed_content.replace("\n", "<br>")
        elif "\r\n" in str_passed_content:
            str_passed_content = str_passed_content.replace("\r\n", "<br>")
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + str_title
            + """</title>
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
            + str_title
            + """
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
                                                                                            """
            + str_passed_content
            + """
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
                                                                                                        <b>선발자 유의 사항</b><br>
                                                                                                        블루무브 포털을 통해 제공해주신 개인정보를 포함한 모든 데이터는 약 24시간 후 삭제될 예정입니다.<br>
                                                                                                        데이터가 삭제되면 선발자를 식별할 수 없어 가입 확정이 불가하므로 유의하시기 바랍니다.
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
                                                            class="mcnButtonBlock" style="min-width:100%;">
                                                            <tbody class="mcnButtonBlockOuter">
                                                                <tr>
                                                                    <td width="100%" valign="top" align="center" class="mcnButtonBlockInner"
                                                                        style="min-width:100%; padding-top:9px; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                        <a class="mcnButton" title="가입 확정" href='"""
            + request.build_absolute_uri()
            + """#join' target="_blank"
                                                                            style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">
                                                                            <table border="0" cellpadding="0" cellspacing="0"
                                                                                width="100%" class="mcnButtonContentContainer"
                                                                                style="min-width:100%; border-collapse: separate !important;border-radius: 4px;background-color: #0077C8;">
                                                                                <tbody>
                                                                                    <tr>
                                                                                        <td align="center"
                                                                                            valign="middle" class="mcnButtonContent"
                                                                                            style="font-size: 16px; padding: 12px;">
                                                                                            가입 확정
                                                                                        </td>
                                                                                    </tr>
                                                                                </tbody>
                                                                            </table>
                                                                        </a>
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
        message["bcc"] = ",".join(bcc_list)
        message["subject"] = str_title
    # mails to failed applicants
    if obj_noti and str_failed_content:
        bcc_list = []
        apps_failed = Applymembership.objects.filter(
            wanted_id=str_wanted_id, received=True, pf="미선발"
        )
        for app in apps_failed:
            bcc_list.append(app.applicant.email)
        if "\n" in str_failed_content:
            str_failed_content = str_failed_content.replace("\n", "<br>")
        elif "\r\n" in str_failed_content:
            str_failed_content = str_failed_content.replace("\r\n", "<br>")
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + str_title
            + """</title>
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
            + str_title
            + """
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
                                                                                            """
            + str_failed_content
            + """
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
                                                                                                        <b>데이터 삭제 안내</b><br>
                                                                                                        블루무브 포털을 통해 제공해주신 개인정보를 포함한 모든 데이터는 약 24시간 후 삭제될 예정입니다.
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
        message["bcc"] = ",".join(bcc_list)
        message["subject"] = str_title
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
                                                                                            블루무브 탈퇴 신청을 위한 블루무버 얼럼나이 인증 코드를 보내드립니다.
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
                                                                                            블루무브 탈퇴 신청 페이지에서 위 10자리 코드를 입력해주시기 바랍니다.<br>
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
    # a mail to queued alumni
    if obj_queued_alumni:
        name = obj_queued_alumni.name
        email = base64.urlsafe_b64decode(
            bytes(obj_queued_alumni.email, "utf-8")
        ).decode("utf8")
        data_boolean = "동의함" if obj_queued_alumni.data_boolean == True else "동의하지 않음"
        reason = obj_queued_alumni.reason
        added_at = obj_queued_alumni.added_at.strftime("%Y-%m-%d %H:%M:%S")
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + name
            + """님의 탈퇴 신청이 접수되었습니다.</title>
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
            + name
            + """님의 탈퇴 신청이 접수되었습니다.
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
            + name
            + """ 블루무버님!<br>
                                                                                            블루무브 탈퇴 신청이 아래와 같이 접수되었습니다.
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
                                                                                                        <b>데이터 삭제·보존 동의 여부</b>: """
            + data_boolean
            + """<br><br>
                                                                                                        <b>탈퇴 신청 사유</b>: """
            + reason
            + """<br><br>
                                                                                                        <b>신청일시</b>: """
            + added_at
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
                                                                                            탈퇴 처리는 신청일시로부터 약 24시간 후 진행되며 그 전까지 블루무브 탈퇴 신청 페이지에서 신청을 취소하실 수 있습니다.<br>
                                                                                            블루무브 탈퇴 신청과 관련하여 궁금한 점이 있으실 경우 아래 연락처로 문의해주시기 바랍니다.
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
                                                            class="mcnButtonBlock" style="min-width:100%;">
                                                            <tbody class="mcnButtonBlockOuter">
                                                                <tr>
                                                                    <td width="100%" valign="top" align="center" class="mcnButtonBlockInner"
                                                                        style="min-width:100%; padding-top:9px; padding-right:18px; padding-bottom:9px; padding-left:18px;">
                                                                        <a class="mcnButton" title="블루무브 탈퇴 신청 페이지" href='"""
            + request.build_absolute_uri()
            + """' target="_blank"
                                                                            style="font-weight: bold;letter-spacing: normal;line-height: 100%;text-align: center;text-decoration: none;color: #FFFFFF;">
                                                                            <table border="0" cellpadding="0" cellspacing="0"
                                                                                width="100%" class="mcnButtonContentContainer"
                                                                                style="min-width:100%; border-collapse: separate !important;border-radius: 4px;background-color: #0077C8;">
                                                                                <tbody>
                                                                                    <tr>
                                                                                        <td align="center"
                                                                                            valign="middle" class="mcnButtonContent"
                                                                                            style="font-size: 16px; padding: 12px;">
                                                                                            블루무브 탈퇴 신청 페이지
                                                                                        </td>
                                                                                    </tr>
                                                                                </tbody>
                                                                            </table>
                                                                        </a>
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
        message["to"] = email
        message["subject"] = name + "님의 탈퇴 신청이 접수되었습니다."
    # a mail to dequeued alumni
    if signal_removed_from_queue:
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + str_alumni_name
            + """님의 탈퇴 신청이 취소되었습니다.</title>
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
            + str_alumni_name
            + """님의 탈퇴 신청이 취소되었습니다.
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
            + """ 블루무버님!<br>
                                                                                            블루무브 탈퇴 신청이 취소되었음을 알려드립니다.<br><br>
                                                                                            돌아와주셔서 감사드리며 """
            + str_alumni_name
            + """ 블루무버님께 더욱 가치 있는 경험을 제공할 수 있는 블루무브가 되도록 노력하겠습니다.<br>
                                                                                            좋은 하루 보내시길 바라요! 🥰
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
        message["subject"] = str_alumni_name + "님의 탈퇴 신청이 취소되었습니다."
    # a mail to withdrawn alumni
    if signal_gone:
        name = obj_queued_alumni.name
        email = base64.urlsafe_b64decode(
            bytes(obj_queued_alumni.email, "utf-8")
        ).decode("utf8")
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>"""
            + name
            + """님의 블루무브 탈퇴가 완료되었습니다.</title>
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
            + name
            + """님의 블루무브 탈퇴가 완료되었습니다.
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
            + name
            + """님!<br>"""
            + name
            + """님의 블루무브 탈퇴가 완료되었습니다.<br><br>그동안 블루무버로서 함께해주신 """
            + name
            + """님께 진심으로 감사드립니다.<br>보다 나은 블루무브의 모습으로 다시 만나뵐 수 있기를 바랍니다.
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
        message["to"] = email
        message["subject"] = name + "님의 블루무브 탈퇴가 완료되었습니다."
    message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf8")}
    return message


def slack_blocks_and_text(
    request=None,
    str_wanted_id=None,
    str_wanted_title=None,
    obj_app=None,
    obj_noti=None,
    obj_queued_alumni=None,
    str_alumni_name=None,
    str_alumni_birth=None,
    str_alumni_phone=None,
    str_alumni_email=None,
    str_queued_alumni_count=None,
    signal_removed_from_queue=None,
    signal_cancel_the_application_for_withdrawal=None,
    signal_gone=None,
):
    # message blocks and a text for the application receipt notification
    if obj_app and not obj_app.notified:
        masked_name, masked_birth, masked_phone, masked_email = privacy_masking(
            str_name=obj_app.applicant.last_name + obj_app.applicant.first_name,
            str_phone=obj_app.applicant.profile.phone,
            str_email=obj_app.applicant.email,
        )
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📄 " + masked_name + "님 지원서 접수됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": masked_name + "님이 지원서를 제출했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*공고명:*\n" + str_wanted_title,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*접수일시:*\n"
                        + obj_app.received_at.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*휴대전화 번호:*\n" + masked_phone,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*이메일 주소:*\n" + masked_email,
                    },
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "접수된 지원서 확인",
                            "emoji": True,
                        },
                        "url": request.build_absolute_uri() + "#app",
                    }
                ],
            },
        ]
        text = f"📄 {masked_name}님 지원서 접수됨"
    # message blocks and a text for the sign-up completion notification
    elif obj_app and obj_app.notified:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 "
                    + obj_app.applicant.last_name
                    + obj_app.applicant.first_name
                    + "님이 가입을 확정함",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": obj_app.applicant.last_name
                    + obj_app.applicant.first_name
                    + "님이 최종적으로 가입을 확정했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*공고명:*\n" + str_wanted_title,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*확정일시:*\n"
                        + obj_app.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*휴대전화 번호:*\n" + obj_app.applicant.profile.phone,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*이메일 주소:*\n" + obj_app.applicant.email,
                    },
                ],
            },
        ]
        text = (
            f"🎉 {obj_app.applicant.last_name + obj_app.applicant.first_name}님이 가입을 확정함"
        )
    # message blocks and a text for the notification of cancellation of withdrawal request
    elif signal_removed_from_queue:
        number = obj_queued_alumni.number
        period = obj_queued_alumni.period
        name = obj_queued_alumni.name
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🥰 " + name + "님이 블루무브 탈퇴 신청을 취소함",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": name + "님이 블루무브 탈퇴 신청을 취소했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*회번:*\n" + number,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*기간:*\n" + period,
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*신청 취소일시:*\n"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        ]
        text = "🥰 " + name + "님이 블루무브 탈퇴 신청을 취소함"
    # message blocks and a text for editing messages after a leaver occurs
    elif signal_gone:
        number = re.sub("[\S]", "*", obj_queued_alumni.number)
        period = re.sub("[^-~() ]", "*", obj_queued_alumni.period)
        name = re.sub("[\S]", "*", obj_queued_alumni.name)
        data_boolean = "동의함" if obj_queued_alumni.data_boolean == True else "동의하지 않음"
        reason = obj_queued_alumni.reason
        added_at = re.sub(
            "[^-: ]", "*", obj_queued_alumni.added_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "😢 " + name + "님이 블루무브 탈퇴를 신청함",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + " 탈퇴 완료`\n"
                    + name
                    + "님이 블루무브 탈퇴를 신청하여 약 24시간 후 탈퇴 처리될 예정입니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*회번:*\n" + number,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*기간:*\n" + period,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*데이터 삭제·보존 동의 여부:*\n" + data_boolean,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*신청일시:*\n" + added_at,
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*탈퇴 신청 사유:*\n" + reason,
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ℹ️ 이 메시지는 탈퇴 신청자 개인정보 및 블루무버 정보 보호를 위해 "
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + "에 편집되었습니다.",
                    },
                ],
            },
        ]
        text = "😢 " + name + "님이 블루무브 탈퇴를 신청함"
    # message blocks and a text for notification of the occurrence of leavers
    elif str_queued_alumni_count:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "😭 얼럼나이 " + str_queued_alumni_count + "명 블루무브 탈퇴 완료됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "얼럼나이 " + str_queued_alumni_count + "명의 블루무브 탈퇴가 완료되었습니다.",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*탈퇴일시:*\n"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        ]
        text = "😭 얼럼나이 " + str_queued_alumni_count + "명 블루무브 탈퇴 완료됨"
    # message blocks and a text for editing messages after canceling the withdrawal request
    elif signal_cancel_the_application_for_withdrawal:
        number = obj_queued_alumni.number
        period = obj_queued_alumni.period
        name = obj_queued_alumni.name
        data_boolean = "동의함" if obj_queued_alumni.data_boolean == True else "동의하지 않음"
        reason = re.sub("[\S]", "*", obj_queued_alumni.reason)
        added_at = re.sub(
            "[^-: ]", "*", obj_queued_alumni.added_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "😢 " + name + "님이 블루무브 탈퇴를 신청함",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + " 탈퇴 신청 취소`\n"
                    + name
                    + "님이 블루무브 탈퇴를 신청하여 약 24시간 후 탈퇴 처리될 예정입니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*회번:*\n" + number,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*기간:*\n" + period,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*데이터 삭제·보존 동의 여부:*\n" + data_boolean,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*신청일시:*\n" + added_at,
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*탈퇴 신청 사유:*\n" + reason,
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ℹ️ 이 메시지는 탈퇴 신청자 개인정보 보호를 위해 "
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + "에 편집되었습니다.",
                    },
                ],
            },
        ]
        text = "😢 " + name + "님이 블루무브 탈퇴를 신청함"
        # message blocks and a text for the notification of occurrence of withdrawal applicants
    elif obj_queued_alumni:
        number = obj_queued_alumni.number
        period = obj_queued_alumni.period
        name = obj_queued_alumni.name
        data_boolean = "동의함" if obj_queued_alumni.data_boolean == True else "동의하지 않음"
        reason = obj_queued_alumni.reason
        added_at = obj_queued_alumni.added_at.strftime("%Y-%m-%d %H:%M:%S")
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "😢 " + name + "님이 블루무브 탈퇴를 신청함",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": name + "님이 블루무브 탈퇴를 신청하여 약 24시간 후 탈퇴 처리될 예정입니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*회번:*\n" + number,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*기간:*\n" + period,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*데이터 삭제·보존 동의 여부:*\n" + data_boolean,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*신청일시:*\n" + added_at,
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*탈퇴 신청 사유:*\n" + reason,
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ℹ️ 이 메시지는 탈퇴 신청자 개인정보 및 블루무버 정보 보호를 위해 약 24시간 후 편집될 예정입니다.",
                    },
                ],
            },
        ]
        text = "😢 " + name + "님이 블루무브 탈퇴를 신청함"
    # message blocks and a text for the error notification of wanted details page
    elif str_wanted_id:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠ '블루무브 가입 지원' 페이지 오류 발생",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "사용자가 '블루무브 가입 지원' 페이지를 이용하는 도중 오류가 발생했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*WANTED_ID:*\n" + str_wanted_id,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*DATETIME:*\n"
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*USERNAME:*\n" + request.user.username
                        if request.user.is_authenticated
                        else "*USERNAME:*\nAnonymousUser",
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*USER_AGENT:*\n"
                        + str(user_agents.parse(request.headers.get("User-Agent"))),
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*REQUEST_METHOD:*\n" + request.method,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*REQUEST_URI:*\n" + request.build_absolute_uri(),
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ℹ️ 이 메시지는 사용자가 위 URI 접속 시 오류가 발생하여 발송되었습니다.",
                    },
                ],
            },
        ]
        text = f"⚠ '블루무브 가입 지원' 페이지 오류 발생"
    # message blocks and a text for notification of recruiting data deletion
    elif obj_noti:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"✂️ '{obj_noti.wanted_title}' 데이터 자동 삭제됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"'{obj_noti.wanted_title}' 관련 모든 데이터가 자동 삭제되었습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*공고 ID:*\n" + obj_noti.wanted_id,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*삭제일시:*\n"
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                ],
            },
        ]
        text = f"✂️ '{obj_noti.wanted_title}' 데이터 자동 삭제됨"
    # message blocks and a text for the error notification of withdrawal page
    elif not obj_noti:
        masked_name, masked_birth, masked_phone, masked_email = privacy_masking(
            str_name=str_alumni_name,
            str_birth=str_alumni_birth,
            str_phone=str_alumni_phone,
            str_email=str_alumni_email,
        )
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠ '블루무브 탈퇴 신청' 페이지 오류 발생",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "사용자가 '블루무브 탈퇴 신청' 페이지를 이용하는 도중 오류가 발생했습니다.",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*DATETIME:*\n"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*ALUMNI_NAME:*\n" + masked_name,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*BLUEMOVER_BIRTHDAY:*\n" + masked_birth,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*BLUEMOVER_PHONE:*\n" + masked_phone,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*BLUEMOVER_EMAIL:*\n" + masked_email,
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ℹ️ 이 메시지는 사용자의 얼럼나이 여부가 명확하지 않은 관계로 오류가 발생하여 발송되었습니다.",
                    },
                ],
            },
        ]
        text = f"⚠ '블루무브 탈퇴 신청' 페이지 오류 발생"
    return blocks, text


####
#### functions for incoming requests from outside
####
def cron_delete_all_expired_recruiting_data(request):
    apps_notified = Applymembership.objects.filter(notified=True)
    notis_sent = ApplymembershipNoti.objects.filter(sent=True)
    for app in apps_notified:
        if app.will_be_deleted_at < datetime.datetime.now():
            app.applicant.delete()
    for noti in notis_sent:
        if noti.will_be_deleted_at < datetime.datetime.now():
            client = WebClient(token=slack_bot_token)
            try:
                client.conversations_join(channel=management_all_channel_id)
            except:
                pass
            blocks, text = slack_blocks_and_text(obj_noti=noti)
            client.chat_postMessage(
                channel=management_all_channel_id,
                link_names=True,
                as_user=True,
                blocks=blocks,
                text=text,
            )
            noti.delete()
    return HttpResponse(status=200)


def cron_delete_delete_queued_alumni_data(request):
    all_queued_alumni = ApplymembershipwithdrawalQueue.objects.all()
    all_queued_alumni_list = []
    for queued_alumni in all_queued_alumni:
        if queued_alumni.will_be_deleted_at < datetime.datetime.now():
            # newsletter (Mailchimp)
            member_email = base64.urlsafe_b64decode(
                bytes(queued_alumni.email, "utf-8")
            ).decode("utf8")
            member_email_hash = hashlib.md5(
                member_email.encode("utf-8").lower()
            ).hexdigest()
            mailchimp.lists.delete_list_member_permanent(
                mailchimp_bluemover_list_id, member_email_hash
            )
            # register (Google Sheets)
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=register_id,
                body={
                    "requests": [
                        {
                            "deleteDimension": {
                                "range": {
                                    "sheetId": register_sheet_id,
                                    "dimension": "ROWS",
                                    "startIndex": int(queued_alumni.row_idx) - 1,
                                    "endIndex": int(queued_alumni.row_idx),
                                }
                            }
                        },
                        {
                            "updateSpreadsheetProperties": {
                                "properties": {
                                    "title": "E03_명부_"
                                    + datetime.datetime.now().strftime("%y%m%d")
                                },
                                "fields": "title",
                            }
                        },
                    ],
                },
            ).execute()
            mail_service.users().messages().send(
                userId=google_delegated_email,
                body=gmail_message(
                    request=request, signal_gone=True, obj_queued_alumni=queued_alumni
                ),
            ).execute()
            client = WebClient(token=slack_bot_token)
            try:
                client.conversations_join(channel=management_dev_channel_id)
            except:
                pass
            blocks, text = slack_blocks_and_text(
                signal_gone=True,
                obj_queued_alumni=queued_alumni,
            )
            client.chat_update(
                channel=management_dev_channel_id,
                link_names=True,
                as_user=True,
                ts=queued_alumni.slack_ts,
                blocks=blocks,
                text=text,
            )
            all_queued_alumni_list.append(queued_alumni)
            queued_alumni.delete()
    queued_alumni_count = len(all_queued_alumni_list)
    if queued_alumni_count > 0:
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(channel=management_dev_channel_id)
        except:
            pass
        blocks, text = slack_blocks_and_text(
            str_queued_alumni_count=str(queued_alumni_count),
        )
        client.chat_postMessage(
            channel=management_dev_channel_id,
            link_names=True,
            as_user=True,
            blocks=blocks,
            text=text,
        )
    return HttpResponse(status=200)


####
#### views
####
def applymembership(request):
    # obj
    app = None
    apps_received = None
    apps_decided = None
    apps_passed = None
    apps_failed = None
    noti = None
    # str, lst
    wanted_id = (
        request.GET.get("wanted_id")
        if request.method == "GET"
        else request.POST.get("wantedIdPost")
    )
    wanted_list = []
    wanted = ""
    self_intro = request.POST.get("appSelfIntro")
    reason = request.POST.get("appReason")
    plan = request.POST.get("appPlan")
    tracking = request.POST.get("appTracking")
    tracking_reference = request.POST.get("appTrackingReference")
    tracking_etc = request.POST.get("appTrackingEtc")
    portfolio = request.POST.get("appPortfolio")
    pf = request.POST.get("appPf")
    title = request.POST.get("notiTitle")
    passed_content = request.POST.get("notiPassedContent")
    failed_content = request.POST.get("notiFailedContent")
    q = request.GET.get("q")
    # boolean
    error = None
    app_saved = None
    app_submitted = None
    noti_saved = None
    wrong_url = None
    wrong_portfolio = None
    timeout = None
    scroll_to_app = None
    scroll_to_join = None
    scroll_to_noti = None
    # cmd
    cmd_get = request.GET.get("cmdGet")
    cmd_post = request.POST.get("cmdPost")
    ####
    #### template 02
    ####
    if not wanted_id == None:
        # wanted details
        try:
            wanted_details = json.loads(
                requests.get(
                    "https://api.notion.com/v1/pages/" + wanted_id,
                    headers=notion_headers,
                ).text
            ).get("properties")
            wanted_team = wanted_details["담당"]["select"]["name"]
            wanted_title = wanted_details["공고명"]["title"][0]["plain_text"]
            wanted_datetime_start = wanted_details["모집 시작"]["date"]["start"]
            wanted_datetime_end = wanted_details["모집 종료"]["date"]["start"]
            wanted_datetime_day = wanted_details["요일"]["formula"]["string"]
            wanted_status = wanted_details["상태"]["formula"]["string"]
            wanted_dict = {
                "team": wanted_team,
                "title": wanted_title,
                "datetime": wanted_datetime_start.split("T")[0][:4]
                + "년 "
                + wanted_datetime_start.split("T")[0][5:7]
                + "월 "
                + wanted_datetime_start.split("T")[0][8:10]
                + "일"
                + wanted_datetime_day_split(wanted_datetime_day.split(",")[0])
                + " "
                + wanted_datetime_start.split("T")[1][:5]
                + " ~ "
                + wanted_datetime_end.split("T")[0][:4]
                + "년 "
                + wanted_datetime_end.split("T")[0][5:7]
                + "월 "
                + wanted_datetime_end.split("T")[0][8:10]
                + "일"
                + wanted_datetime_day_split(wanted_datetime_day.split(",")[1])
                + " "
                + wanted_datetime_end.split("T")[1][:5],
                "status": wanted_status,
            }
            wanted_list.append(wanted_dict.copy())
            # application
            if (
                request.user.is_authenticated
                and not "@bluemove.or.kr" in request.user.email
            ):
                try:
                    app = Applymembership.objects.get(
                        applicant=request.user, wanted_id=wanted_id
                    )
                except:
                    pass
                if reception_closed(wanted_datetime_end):
                    timeout = True
                # create an application
                if cmd_post == "create" and not app and not timeout:
                    scroll_to_app = True
                    app = Applymembership.objects.create(
                        applicant=request.user,
                        wanted_id=wanted_id,
                        wanted_title=wanted_title,
                    )
                # save or submit the application
                elif (
                    app
                    and not app.last_saved == True
                    and (
                        cmd_post == "save"
                        or (cmd_post == "submit" and not app.received == True)
                    )
                ):
                    scroll_to_app = True
                    save_the_app(
                        app,
                        wanted_title,
                        self_intro,
                        reason,
                        plan,
                        tracking,
                        tracking_reference,
                        tracking_etc,
                        portfolio,
                    )
                    try:
                        if (
                            portfolio == ""
                            or requests.get(portfolio, headers=bs4_headers).status_code
                            == 200
                        ):
                            if timeout:
                                app.last_saved = True
                                app.save()
                            if cmd_post == "save" and not timeout:
                                app_saved = True
                            elif cmd_post == "submit" and not timeout:
                                app.received = True
                                app.received_at = datetime.datetime.now()
                                app.save()
                                app_submitted = True
                                client = WebClient(token=slack_bot_token)
                                try:
                                    client.conversations_join(
                                        channel=management_all_channel_id
                                    )
                                except:
                                    pass
                                blocks, text = slack_blocks_and_text(
                                    request=request,
                                    str_wanted_title=wanted_title,
                                    obj_app=app,
                                )
                                client.chat_postMessage(
                                    channel=management_all_channel_id,
                                    link_names=True,
                                    as_user=True,
                                    blocks=blocks,
                                    text=text,
                                )
                                mail_service.users().messages().send(
                                    userId=google_delegated_email,
                                    body=gmail_message(
                                        request=request,
                                        obj_app=app,
                                        str_wanted_title=wanted_title,
                                    ),
                                ).execute()
                    except:
                        wrong_portfolio = True
                # delete the application
                elif cmd_post == "delete" and app:
                    scroll_to_app = True
                    app.delete()
                    app = None
                elif cmd_post == "join" and app and app.notified == True:
                    scroll_to_join = True
                    app.joined = True
                    app.save()
                    client = WebClient(token=slack_bot_token)
                    try:
                        client.conversations_join(channel=management_all_channel_id)
                    except:
                        pass
                    blocks, text = slack_blocks_and_text(
                        request=request,
                        str_wanted_title=wanted_title,
                        obj_app=app,
                    )
                    client.chat_postMessage(
                        channel=management_all_channel_id,
                        link_names=True,
                        as_user=True,
                        blocks=blocks,
                        text=text,
                    )
            elif (
                request.user.is_authenticated
                and "@bluemove.or.kr" in request.user.email
            ):
                apps_received = Applymembership.objects.filter(
                    wanted_id=wanted_id, received=True
                ).order_by("-received_at")
                apps_decided = apps_received.exclude(pf="미결정")
                apps_passed = apps_received.filter(pf="선발")
                apps_failed = apps_received.filter(pf="미선발")
                try:
                    noti = ApplymembershipNoti.objects.get(wanted_id=wanted_id)
                except:
                    pass
                if not pf == None:
                    scroll_to_app = True
                    applicant = pf.split("#")[0]
                    app = Applymembership.objects.get(
                        applicant=applicant, wanted_id=wanted_id
                    )
                    app.pf = pf.split("#")[1]
                    app.save()
                # create or save or send the notification
                elif (
                    apps_received.count() > 0
                    and apps_received.count() == apps_decided.count()
                    and (cmd_post == "noti_save" or cmd_post == "noti_send")
                ):
                    scroll_to_noti = True
                    if not noti:
                        noti = ApplymembershipNoti.objects.create(
                            wanted_id=wanted_id, saved_by=request.user
                        )
                    save_the_noti(
                        request,
                        noti,
                        wanted_title,
                        title,
                        passed_content,
                        failed_content,
                    )
                    if cmd_post == "noti_save":
                        noti_saved = True
                    if cmd_post == "noti_send":
                        if not noti.sent == True and not passed_content == None:
                            mail_service.users().messages().send(
                                userId=google_delegated_email,
                                body=gmail_message(
                                    request=request,
                                    obj_noti=noti,
                                    str_wanted_id=wanted_id,
                                    str_title=title,
                                    str_passed_content=passed_content,
                                ),
                            ).execute()
                        time.sleep(1)
                        if not noti.sent == True and not failed_content == None:
                            mail_service.users().messages().send(
                                userId=google_delegated_email,
                                body=gmail_message(
                                    obj_noti=noti,
                                    str_wanted_id=wanted_id,
                                    str_title=title,
                                    str_failed_content=failed_content,
                                ),
                            ).execute()
                        noti.sent = True
                        noti.will_be_deleted_at = (
                            datetime.datetime.now() + datetime.timedelta(days=1)
                        )
                        noti.save()
                        for app in apps_decided:
                            app.notified = True
                            app.will_be_deleted_at = (
                                datetime.datetime.now() + datetime.timedelta(days=1)
                            )
                            app.save()
                # delete the notification
                elif (
                    cmd_post == "noti_delete"
                    and noti
                    and apps_received.count() > 0
                    and apps_received.count() == apps_decided.count()
                ):
                    scroll_to_noti = True
                    noti.delete()
                    noti = None
            # wanted
            try:
                wanted_soup = BeautifulSoup(
                    requests.get(
                        "https://www.bluemove.or.kr/" + wanted_id,
                        headers=bs4_headers,
                    ).content,
                    "lxml",
                )
                wanted_raw = wanted_soup.find(class_="notion-page-content")
                del wanted_raw["style"]
                for style in wanted_raw.select("style"):
                    style.extract()
                wanted = str(wanted_raw)
                return render(
                    request,
                    "applynsubmit/applymembership.html",
                    {
                        # obj
                        "app": app,
                        "apps_received": apps_received,
                        "apps_decided": apps_decided,
                        "apps_passed": apps_passed,
                        "apps_failed": apps_failed,
                        "noti": noti,
                        # str, lst
                        "wanted_id": wanted_id,
                        "wanted_list": wanted_list,
                        "wanted": wanted,
                        "portfolio": portfolio,
                        # boolean
                        "app_saved": app_saved,
                        "app_submitted": app_submitted,
                        "noti_saved": noti_saved,
                        "scroll_to_app": scroll_to_app,
                        "scroll_to_join": scroll_to_join,
                        "scroll_to_noti": scroll_to_noti,
                        "wrong_portfolio": wrong_portfolio,
                        "timeout": timeout,
                    },
                )
            except:
                wanted_id_without_dash = wanted_id.replace("-", "")
                if (
                    "-" in wanted_id
                    and len(wanted_id_without_dash) == 32
                    and requests.get(
                        "https://www.notion.so/bluemove/" + wanted_id_without_dash
                    ).status_code
                    == 200
                ):
                    error = True
                    client = WebClient(token=slack_bot_token)
                    try:
                        client.conversations_join(channel=management_dev_channel_id)
                    except:
                        pass
                    blocks, text = slack_blocks_and_text(
                        request=request, str_wanted_id=wanted_id
                    )
                    client.chat_postMessage(
                        channel=management_dev_channel_id,
                        link_names=True,
                        as_user=True,
                        blocks=blocks,
                        text=text,
                    )
                    return render(
                        request,
                        "applynsubmit/applymembership.html",
                        {
                            # obj
                            "app": app,
                            "apps_received": apps_received,
                            "apps_decided": apps_decided,
                            "apps_passed": apps_passed,
                            "apps_failed": apps_failed,
                            "noti": noti,
                            # str, lst
                            "wanted_id": wanted_id,
                            "wanted_list": wanted_list,
                            "portfolio": portfolio,
                            # boolean
                            "error": error,
                            "app_saved": app_saved,
                            "app_submitted": app_submitted,
                            "noti_saved": noti_saved,
                            "scroll_to_app": scroll_to_app,
                            "scroll_to_join": scroll_to_join,
                            "scroll_to_noti": scroll_to_noti,
                            "wrong_portfolio": wrong_portfolio,
                            "timeout": timeout,
                        },
                    )
        ####
        #### template 01
        ####
        except:
            wrong_url = True
    # wanted list
    wanted_list_opened = json.loads(
        requests.post(
            "https://api.notion.com/v1/databases/" + wanted_db_id + "/query",
            headers=notion_headers,
            data='{ "filter": { "or": [ {"property": "상태", "text": {"contains": "접수 중"} }, {"property": "상태", "text": {"contains": "준비 중"} } ] }, "sorts": [ {"property": "상태", "direction": "descending"}, {"property": "모집 종료", "direction": "ascending"}, {"property": "공고명", "direction": "ascending"} ] }'.encode(
                "utf-8"
            ),
        ).text
    ).get("results")
    wanted_list_closed = json.loads(
        requests.post(
            "https://api.notion.com/v1/databases/" + wanted_db_id + "/query",
            headers=notion_headers,
            data='{ "filter": {"property": "상태", "text": {"contains": "마감"} }, "sorts": [ {"property": "모집 종료", "direction": "descending"}, {"property": "공고명", "direction": "ascending"} ] }'.encode(
                "utf-8"
            ),
        ).text
    ).get("results")
    wanted_list_raw = wanted_list_opened + wanted_list_closed
    for wanted_row in wanted_list_raw:
        wanted_status = wanted_row["properties"]["상태"]["formula"]["string"]
        if not "MSG" in wanted_status:
            wanted_id = wanted_row["id"]
            wanted_team = wanted_row["properties"]["담당"]["select"]["name"]
            wanted_title = wanted_row["properties"]["공고명"]["title"][0]["plain_text"]
            wanted_datetime_start = wanted_row["properties"]["모집 시작"]["date"]["start"]
            wanted_datetime_end = wanted_row["properties"]["모집 종료"]["date"]["start"]
            wanted_day = wanted_row["properties"]["요일"]["formula"]["string"]
            wanted_dict = {
                "id": wanted_id,
                "team": wanted_team,
                "title": wanted_title,
                "datetime": wanted_datetime_start.split("T")[0][:4]
                + "년 "
                + wanted_datetime_start.split("T")[0][5:7]
                + "월 "
                + wanted_datetime_start.split("T")[0][8:10]
                + "일"
                + wanted_datetime_day_split(wanted_day.split(",")[0])
                + " "
                + wanted_datetime_start.split("T")[1][:5]
                + " ~ "
                + wanted_datetime_end.split("T")[0][:4]
                + "년 "
                + wanted_datetime_end.split("T")[0][5:7]
                + "월 "
                + wanted_datetime_end.split("T")[0][8:10]
                + "일"
                + wanted_datetime_day_split(wanted_day.split(",")[1])
                + " "
                + wanted_datetime_end.split("T")[1][:5],
                "status": wanted_status,
            }
            wanted_list.append(wanted_dict.copy())
    # search
    try:
        if len(q) > 1:
            wanted_list_pre = [
                wanted_row
                for wanted_row in wanted_list
                for wanted_value in wanted_row.values()
                if q in wanted_value
            ]
            wanted_list = []
            for i in wanted_list_pre:
                if i not in wanted_list:
                    wanted_list.append(i)
        else:
            pass
    except:
        q = None
    # paginator
    page = request.GET.get("page", 1)
    paginator = Paginator(wanted_list, 10)
    try:
        wanted_list = paginator.page(page)
    except PageNotAnInteger:
        wanted_list = paginator.page(1)
    except EmptyPage:
        wanted_list = paginator.page(paginator.num_pages)
    return render(
        request,
        "applynsubmit/applymembership.html",
        {
            # str, lst
            "wanted_list": wanted_list,
            "q": q,
            # boolean
            "wrong_url": wrong_url,
        },
    )


def applymembershipwithdrawal(request):
    # obj
    queued_alumni = None
    # str, lst
    alumni_name = request.POST.get("alumniName")
    alumni_birth = request.POST.get("alumniBirth")
    alumni_phone = request.POST.get("alumniPhone")
    alumni_email = request.POST.get("alumniEmail")
    agreement_checkbox = request.POST.get("agreementCheckbox")
    reason = request.POST.get("reason")
    v_code_input = request.POST.get("vCode")
    alumni_list = []
    # cmd
    cmd_get = request.GET.get("cmdGet")
    cmd_post = request.POST.get("cmdPost")
    # boolean
    alumni = None
    new_member = None
    active_alumni = None
    unable_to_verify = None
    verified = None
    wrong_v_code = None
    added_to_queue = None
    removed_from_queue = None
    # initialize verification
    if cmd_get == "init":
        v_code_obj = Applymembershipwithdrawal.objects.filter(
            birthday=request.GET.get("bd"),
            phone_last=request.GET.get("pl"),
            email_host=request.GET.get("eh"),
        )
        v_code_obj.delete()
        return redirect("applynsubmit:applymembershipwithdrawal")
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
    # remove from queue
    if request.method == "POST" and cmd_post == "remove from queue":
        queued_alumni = ApplymembershipwithdrawalQueue.objects.get(
            number=alumni_list[0][0],
            period=alumni_list[0][1]
            + " ("
            + alumni_list[0][4]
            + " ~ "
            + alumni_list[0][6]
            + ")",
            name=alumni_list[0][2],
            email=base64.urlsafe_b64encode(bytes(alumni_list[0][12], "utf-8")).decode(
                "utf8"
            ),
            role=alumni_list[0][3],
            activities=alumni_list[0][8],
        )
        mail_service.users().messages().send(
            userId=google_delegated_email,
            body=gmail_message(
                signal_removed_from_queue=True,
                str_alumni_name=alumni_name,
                str_alumni_email=alumni_email,
            ),
        ).execute()
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(channel=management_dev_channel_id)
        except:
            pass
        blocks, text = slack_blocks_and_text(
            signal_cancel_the_application_for_withdrawal=True,
            obj_queued_alumni=queued_alumni,
        )
        client.chat_update(
            channel=management_dev_channel_id,
            link_names=True,
            as_user=True,
            ts=queued_alumni.slack_ts,
            blocks=blocks,
            text=text,
        )
        blocks, text = slack_blocks_and_text(
            signal_removed_from_queue=True, obj_queued_alumni=queued_alumni
        )
        client.chat_postMessage(
            channel=management_dev_channel_id,
            link_names=True,
            as_user=True,
            blocks=blocks,
            text=text,
        )
        queued_alumni.delete()
        removed_from_queue = True
    # add to queue
    elif (
        request.method == "POST"
        and agreement_checkbox == "checked"
        and cmd_post == "add to queue"
    ):
        row_idx = (
            int(
                [
                    idx
                    for idx, bluemover_row in enumerate(bluemover_list)
                    if alumni_name in bluemover_row
                    and alumni_birth in bluemover_row
                    and alumni_phone in bluemover_row
                    and alumni_email in bluemover_row
                ][0]
            )
            + 2
        )
        queued_alumni = ApplymembershipwithdrawalQueue.objects.create(
            number=alumni_list[0][0],
            period=alumni_list[0][1]
            + " ("
            + alumni_list[0][4]
            + " ~ "
            + alumni_list[0][6]
            + ")",
            name=alumni_list[0][2],
            email=base64.urlsafe_b64encode(bytes(alumni_list[0][12], "utf-8")).decode(
                "utf8"
            ),
            role=alumni_list[0][3],
            activities=alumni_list[0][8],
            data_boolean=True,
            reason=reason,
            row_idx=row_idx,
            added_at=datetime.datetime.now(),
            will_be_deleted_at=datetime.datetime.now() + datetime.timedelta(days=1),
        )
        mail_service.users().messages().send(
            userId=google_delegated_email,
            body=gmail_message(
                request=request,
                obj_queued_alumni=queued_alumni,
            ),
        ).execute()
        client = WebClient(token=slack_bot_token)
        try:
            client.conversations_join(channel=management_dev_channel_id)
        except:
            pass
        blocks, text = slack_blocks_and_text(obj_queued_alumni=queued_alumni)
        slack = client.chat_postMessage(
            channel=management_dev_channel_id,
            link_names=True,
            as_user=True,
            blocks=blocks,
            text=text,
        )
        queued_alumni.slack_ts = slack["ts"]
        queued_alumni.save()
        added_to_queue = True
    # verification code validation
    elif request.method == "POST" and v_code_input:
        v_code_obj = Applymembershipwithdrawal.objects.filter(
            birthday=alumni_birth[5:7] + alumni_birth[8:10],
            phone_last=alumni_phone[-4:],
            email_host=alumni_email.split("@")[1],
            code=v_code_input,
        )
        if v_code_obj:
            v_code_obj.delete()
            verified = True
            try:
                queued_alumni = ApplymembershipwithdrawalQueue.objects.get(
                    number=alumni_list[0][0],
                    period=alumni_list[0][1]
                    + " ("
                    + alumni_list[0][4]
                    + " ~ "
                    + alumni_list[0][6]
                    + ")",
                    name=alumni_list[0][2],
                    email=base64.urlsafe_b64encode(
                        bytes(alumni_list[0][12], "utf-8")
                    ).decode("utf8"),
                    role=alumni_list[0][3],
                    activities=alumni_list[0][8],
                )
                added_to_queue = True if queued_alumni else False
            except:
                pass
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
                and not "현재" in bluemover_row
            ):
                v_code = ""
                try:
                    v_code_obj = Applymembershipwithdrawal.objects.filter(
                        birthday=alumni_birth[5:7] + alumni_birth[8:10],
                        phone_last=alumni_phone[-4:],
                        email_host=alumni_email.split("@")[1],
                    )
                    v_code_obj.delete()
                except:
                    pass
                for i in range(10):
                    v_code += random.choice(string.ascii_uppercase + string.digits)
                Applymembershipwithdrawal.objects.create(
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
            elif (
                alumni_name in bluemover_row
                and alumni_birth in bluemover_row
                and alumni_phone in bluemover_row
                and alumni_email in bluemover_row
                and "현재" in bluemover_row
            ):
                active_alumni = True
            else:
                unable_to_verify = True
    return render(
        request,
        "applynsubmit/applymembershipwithdrawal.html",
        {
            # obj
            "queued_alumni": queued_alumni,
            # str, lst
            "alumni_name": alumni_name,
            "alumni_birth": alumni_birth,
            "alumni_phone": alumni_phone,
            "alumni_email": alumni_email,
            "v_code_input": v_code_input,
            "alumni_list": alumni_list,
            # boolean
            "alumni": alumni,
            "new_member": new_member,
            "active_alumni": active_alumni,
            "unable_to_verify": unable_to_verify,
            "verified": verified,
            "wrong_v_code": wrong_v_code,
            "added_to_queue": added_to_queue,
            "removed_from_queue": removed_from_queue,
        },
    )
