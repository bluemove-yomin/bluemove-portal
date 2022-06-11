from allauth.socialaccount import fields
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# models
from django.contrib.auth.models import User

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
import base64

# Notion
import requests, json, pytz

# Slack
from slack_sdk import WebClient

# user-agents (https://github.com/selwin/python-user-agents)
import user_agents

# activity report
import io, os
from googleapiclient.http import MediaIoBaseDownload

# multiple functions
import datetime
from django.http import HttpResponse
import ast
import re

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

# Google API (User)
# def google_api_credentials(request):
#     token = SocialToken.objects.get(
#         account__user=request.user, account__provider="google"
#     )
#     credentials = Credentials(
#         client_id=google_client_id,
#         client_secret=google_client_secret,
#         token_uri="https://oauth2.googleapis.com/token",
#         refresh_token=token.token_secret,
#         token=token.token,
#     )
#     return credentials


# def drive_service_user(request):
#     return build("drive", "v3", credentials=google_api_credentials(request))


# def docs_service_user(request):
#     return build("docs", "v1", credentials=google_api_credentials(request))


# Google API (SA)
sa_credentials = service_account.Credentials.from_service_account_file(
    google_sa_creds,
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/admin.directory.user",
    ],
)
credentials_delegated = sa_credentials.with_subject(google_delegated_email)
drive_service = build("drive", "v3", credentials=credentials_delegated)
docs_service = build("docs", "v1", credentials=credentials_delegated)
sheets_service = build("sheets", "v4", credentials=credentials_delegated)
slides_service = build("slides", "v1", credentials=credentials_delegated)
mail_service = build("gmail", "v1", credentials=credentials_delegated)
admin_service = build("admin", "directory_v1", credentials=credentials_delegated)

# Notion API
notion_headers = {
    "Authorization": f"Bearer " + notion_token,
    "Content-Type": "application/json",
    "Notion-Version": "2022-02-22",
}
kst = pytz.timezone("Asia/Seoul")

# Slack API
client = WebClient(token=slack_bot_token)

# Bluemove data
activity_report_temp_id = "1r9kcAI83dIxXLJ-I1an_OhDZU2Ii-Pf9_-sybJT6Um0"
activity_report_folder_id = "1MrXJipz1swpDpBUkl4TlTk9ot3Kl6nqS"
register_id = "1HkfnZ-2udmQAgE3u8o54rj6ek6IpcDFPjsgX4ycFATs"
project_db_id = "d17acacd-fb64-4e0d-9f75-462424c7cb81"
task_db_id = "45e43f3f-dfb3-4d34-8b02-1c95a745719d"
docs_log_id = "10-ROxf9XjSRIN7R71EIiAQCstre8jqOwrfxbEC_uRX4"
notice_all_channel_id = "C2EH6PNJU"
management_all_channel_id = "CV3THBHJB"
management_dev_channel_id = "C01L8PETS5S"


####
#### utils
####
def image_object_id(str_activity_report_id):
    image_object_id_list = list(
        docs_service.documents()
        .get(documentId=str_activity_report_id)
        .execute()
        .get("inlineObjects")
        .keys()
    )
    return image_object_id_list


def datetime_day_split(str_datetime_day_num):
    if str_datetime_day_num == "1":
        return "(월)"
    elif str_datetime_day_num == "2":
        return "(화)"
    elif str_datetime_day_num == "3":
        return "(수)"
    elif str_datetime_day_num == "4":
        return "(목)"
    elif str_datetime_day_num == "5":
        return "(금)"
    elif str_datetime_day_num == "6":
        return "(토)"
    elif str_datetime_day_num == "0":
        return "(일)"
    else:
        return ""


def spreadsheets_values(
    str_spreadsheet_id, str_range, boolean_del_first_index, boolean_reverse_list
):
    this_list = (
        sheets_service.spreadsheets()
        .values()
        .get(
            spreadsheetId=str_spreadsheet_id,
            range=str_range,
            majorDimension="ROWS",
        )
        .execute()
    ).get("values")
    if boolean_del_first_index == True:
        del this_list[0]
    if boolean_reverse_list == True:
        this_list.reverse()
    return this_list


def spreadsheets_range(
    str_sheet_name,
    str_activity_report_col_index_start,
    str_activity_report_col_index_end,
    int_activity_report_row_index,
):
    return (
        str_sheet_name
        + "!"
        + str_activity_report_col_index_start
        + str(int_activity_report_row_index)
        + ":"
        + str_activity_report_col_index_end
        + str(int_activity_report_row_index)
    )


def get_tasks_to_be_done(datetime_value):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    today = datetime.date.today()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    unfinished_task_status = (
        "yesterday"
        if datetime_value == yesterday
        else "today"
        if datetime_value == today
        else "tomorrow"
        if datetime_value == tomorrow
        else None
    )
    date_filter_condition = (
        "on_or_before" if unfinished_task_status == "yesterday" else "equals"
    )
    unfinished_task_list = []
    unfinished_task_list_pre = json.loads(
        requests.post(
            "https://api.notion.com/v1/databases/" + task_db_id + "/query",
            headers=notion_headers,
            data=json.dumps(
                {
                    "filter": {
                        "and": [
                            {
                                "property": "마감일",
                                "date": {
                                    f"{date_filter_condition}": str(
                                        datetime_value.isoformat()
                                    )[:10]
                                },
                            },
                            {"property": "완료", "checkbox": {"equals": False}},
                        ]
                    }
                }
            ),
        ).text
    ).get("results")
    for i in range(len(unfinished_task_list_pre)):
        task_title = (
            unfinished_task_list_pre[i]
            .get("properties")
            .get("태스크")
            .get("title")[0]
            .get("plain_text")
        )
        task_responsibility_email = (
            unfinished_task_list_pre[i]
            .get("properties")
            .get("태스크 담당자")
            .get("people")[0]
            .get("person")
            .get("email")
        )
        task_url = unfinished_task_list_pre[i].get("url")
        task_elapsed_days = (
            str(
                (
                    datetime.date.today()
                    - datetime.datetime.strptime(
                        unfinished_task_list_pre[i]
                        .get("properties")
                        .get("마감일")
                        .get("date")
                        .get("start"),
                        "%Y-%m-%d",
                    ).date()
                ).days
            )
            if datetime_value == yesterday
            else None
        )
        unfinished_task_list.append(
            [task_title, task_responsibility_email, task_url, task_elapsed_days]
        )
        unfinished_task_list.reverse()
    return unfinished_task_status, unfinished_task_list


def get_notion_user_info(str_notion_user_id):
    user_info = json.loads(
        requests.get(
            "https://api.notion.com/v1/users/" + str_notion_user_id,
            headers=notion_headers,
        ).text
    )
    return user_info


def gmail_message(
    str_activity_report_name,
    str_activity_report_title,
    str_activity_report_date,
    str_activity_report_time_duration,
    str_activity_report_address,
    str_activity_report_approver,
    str_activity_report_approver_email,
    str_activity_report_approver_phone,
):
    # a mail to the applicant who submitted the application
    if str_activity_report_name:
        message_text = (
            """
            <!doctype html>
            <html xmlns="http://www.w3.org/1999/xhtml">

            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>'"""
            + str_activity_report_title
            + """' 일일활동보고서입니다.</title>
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
                                                                                            '"""
            + str_activity_report_title
            + """' 일일활동보고서입니다.
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
                                                                                            안녕하세요, 파란물결 블루무브입니다.<br>'"""
            + str_activity_report_title
            + """' 일일활동보고서를 첨부 파일로 제출드립니다.
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
                                                                                                        <b>활동명</b>: """
            + str_activity_report_title
            + """<br>
                                                                                                        <b>활동 연월일</b>: """
            + str_activity_report_date
            + """<br>
                                                                                                        <b>활동 시간</b>: """
            + str_activity_report_time_duration
            + """<br>
                                                                                                        <b>활동 장소</b>: """
            + str_activity_report_address
            + """<br>
                                                                                                        <b>담당자</b>: """
            + str_activity_report_approver
            + """ 매니저 ( """
            + str_activity_report_approver_email
            + """ / """
            + str_activity_report_approver_phone
            + """ )
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
                                                                                            특이 사항이 있을 경우 담당자에게 연락해주시기 바랍니다.<br>
                                                                                            감사합니다.
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
        message["to"] = "jawon@sb.go.kr"
        message["subject"] = "'" + str_activity_report_title + "' 일일활동보고서입니다."
        main_type, sub_type = "application/pdf".split("/", 1)
        temp = open(str_activity_report_name, "rb")
        attachment = MIMEApplication(temp.read(), _subtype=sub_type)
        temp.close()
        attachment.add_header(
            "Content-Disposition", "attachment", filename=str_activity_report_name
        )
        message.attach(MIMEText(message_text, "html"))
        message.attach(attachment)
    message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf8")}
    return message


def slack_blocks_and_text(
    request=None,
    str_project=None,
    str_title=None,
    str_drafter_datetime=None,
    str_drafter=None,
    str_drafter_email=None,
    str_approver_datetime=None,
    str_approver=None,
    str_approver_email=None,
    str_rejection_reason=None,
    str_activity_report_id=None,
    str_unfinished_task_status=None,
    lst_unfinished_task_list=None,
    lst_msg_item_list=None,
    lst_finished_task_list=None,
    boolean_reminder=None,
):
    # message blocks and a text for the activity report receipt notification
    if (
        request
        and str_project
        and str_title
        and str_drafter_datetime
        and str_drafter
        and str_drafter_email
        and str_approver_email
        and str_activity_report_id
    ):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📝 '" + str_title + "' 일일활동보고서 접수됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<@"
                    + str_drafter_email.replace("@bluemove.or.kr", "").lower()
                    + ">님이 <@"
                    + str_approver_email.replace("@bluemove.or.kr", "").lower()
                    + ">님에게 일일활동보고서를 제출했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*프로젝트:*\n" + str_project,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*활동명:*\n" + str_title,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*기안일시:*\n" + str_drafter_datetime,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*기안자:*\n" + str_drafter,
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
                            "text": "접수된 보고서 확인",
                            "emoji": True,
                        },
                        "url": request.build_absolute_uri()
                        + "?activity_report_id="
                        + str_activity_report_id,
                    }
                ],
            },
        ]
        text = f"📝 '{str_title}' 일일활동보고서 접수됨"
    # message blocks and a text for the activity report approval notification
    elif (
        request
        and str_project
        and str_title
        and str_drafter_email
        and str_approver_datetime
        and str_approver
        and str_approver_email
        and str_activity_report_id
        and not str_rejection_reason
    ):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✔️ '" + str_title + "' 일일활동보고서 승인됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<@"
                    + str_approver_email.replace("@bluemove.or.kr", "").lower()
                    + ">님이 <@"
                    + str_drafter_email.replace("@bluemove.or.kr", "").lower()
                    + ">님의 일일활동보고서를 승인했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*프로젝트:*\n" + str_project,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*활동명:*\n" + str_title,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*결재일시:*\n" + str_approver_datetime,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*결재자:*\n" + str_approver,
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
                            "text": "승인된 보고서 확인",
                            "emoji": True,
                        },
                        "url": request.build_absolute_uri(),
                    }
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "ℹ️ 일일활동보고서가 승인됨에 따라 1365 자원봉사센터에 자동 전송되었습니다.",
                    },
                ],
            },
        ]
        text = f"✔️ '{str_title}' 일일활동보고서 승인됨"
        # message blocks and a text for the activity report rejection notification
    elif (
        request
        and str_project
        and str_title
        and str_drafter_email
        and str_approver_datetime
        and str_approver
        and str_approver_email
        and str_rejection_reason
        and str_activity_report_id
    ):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⛔ '{str_title}' 일일활동보고서 반려됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<@"
                    + str_approver_email.replace("@bluemove.or.kr", "").lower()
                    + ">님이 <@"
                    + str_drafter_email.replace("@bluemove.or.kr", "").lower()
                    + ">님의 일일활동보고서를 반려했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*프로젝트:*\n{str_project}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*활동명:*\n{str_title}",
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*결재일시:*\n{str_approver_datetime}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*결재자:*\n{str_approver}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*반려 사유:*\n{str_rejection_reason}",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "반려된 보고서 확인",
                            "emoji": True,
                        },
                        "url": request.build_absolute_uri(),
                    }
                ],
            },
        ]
        text = f"⛔ '{str_title}' 일일활동보고서 반려됨"
    # message blocks and a text for the reminder
    elif (
        str_project
        and str_title
        and str_drafter_datetime
        and str_drafter
        and str_drafter_email
        and str_approver_email
        and str_activity_report_id
        and boolean_reminder
    ):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⌛ '" + str_title + "' 일일활동보고서 결재 지연됨",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "<@"
                    + str_drafter_email.replace("@bluemove.or.kr", "").lower()
                    + ">님이 <@"
                    + str_approver_email.replace("@bluemove.or.kr", "").lower()
                    + ">님에게 일일활동보고서를 제출했으나 결재가 지연되고 있습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*프로젝트:*\n" + str_project,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*활동명:*\n" + str_title,
                    },
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*기안일시:*\n" + str_drafter_datetime,
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*기안자:*\n" + str_drafter,
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
                            "text": "접수된 보고서 확인",
                            "emoji": True,
                        },
                        "url": "https://portal.bluemove.or.kr/draftnapprove/activityreport"
                        + "?activity_report_id="
                        + str_activity_report_id,
                    }
                ],
            },
        ]
        text = f"⌛ '{str_title}' 일일활동보고서 결재 지연됨"
    # message blocks and a text for the error notification
    elif request and str_activity_report_id:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠ '일일활동보고서' 페이지 오류 발생",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "사용자가 '일일활동보고서' 페이지를 이용하는 도중 오류가 발생했습니다.",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*ACTIVITY_REPORT_ID:*\n" + str_activity_report_id,
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
        text = f"⚠ '일일활동보고서' 페이지 오류 발생"
    # message blocks and a text for the notification about tasks done
    elif lst_finished_task_list:
        finished_task_list = []
        for task in lst_finished_task_list:
            item = (
                "• <"
                + task[3]
                + "|"
                + task[1]
                + "> (<@"
                + task[2].replace("@bluemove.or.kr", "").lower()
                + ">, "
                + task[4]
                + " 마감)"
            )
            finished_task_list.append(item)
        title = "🟢 새로 완료된 태스크가 " + str(len(lst_finished_task_list)) + "개 있음"
        contents = (
            str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            + " 기준 새로 완료된 태스크가 있습니다! 👏"
        )
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": contents},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*해당 태스크:*\n" + "\n".join(finished_task_list),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*확인일시:*\n"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        ]
        text = title
    # message blocks and a text for the notification about tasks to be done
    elif str_unfinished_task_status and lst_unfinished_task_list:
        if str_unfinished_task_status == "yesterday":
            title = "🔴 지연된 태스크가 " + str(len(lst_unfinished_task_list)) + "개 있음"
            contents = (
                "마감일이 지난 태스크 "
                + str(len(lst_unfinished_task_list))
                + "개를 서둘러 완료해주시기 바랍니다."
            )
        elif str_unfinished_task_status == "today":
            title = "🟠 오늘 완료되어야 할 태스크가 " + str(len(lst_unfinished_task_list)) + "개 있음"
            contents = (
                "마감일이 "
                + str(datetime.date.today().strftime("%Y-%m-%d"))
                + "로 설정된 태스크가 있습니다."
            )
        elif str_unfinished_task_status == "tomorrow":
            title = "🟡 내일 완료되어야 할 태스크가 " + str(len(lst_unfinished_task_list)) + "개 있음"
            contents = (
                "마감일이 "
                + str(
                    (datetime.date.today() + datetime.timedelta(days=1)).strftime(
                        "%Y-%m-%d"
                    )
                )
                + "로 설정된 태스크가 있습니다."
            )
        unfinished_task_list = []
        for task in lst_unfinished_task_list:
            item = (
                "• <"
                + task[2]
                + "|"
                + task[0]
                + "> (<@"
                + task[1].replace("@bluemove.or.kr", "").lower()
                + ">, "
                + task[3]
                + "일 지연)"
                if str_unfinished_task_status == "yesterday"
                else "• <"
                + task[2]
                + "|"
                + task[0]
                + "> (<@"
                + task[1].replace("@bluemove.or.kr", "").lower()
                + ">)"
            )
            unfinished_task_list.append(item)
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": contents},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*해당 태스크:*\n" + "\n".join(unfinished_task_list),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*확인일시:*\n"
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
        ]
        text = title
    # message blocks and a text for the notification about projects or tasks that require action
    elif lst_msg_item_list:
        msg_project_list = []
        msg_task_list = []
        for item in lst_msg_item_list:
            item_responsibility_email = item[4] if item[4] != None else item[2]
            inner_item = (
                "• <"
                + item[5]
                + "|"
                + item[3].replace("<", "").replace(">", "")
                + "> (<@"
                + item_responsibility_email.replace("@bluemove.or.kr", "").lower()
                + ">, "
                + item[1]
                + ")"
            )
            if item[0] == "프로젝트":
                msg_project_list.append(inner_item)
            if item[0] == "태스크":
                msg_task_list.append(inner_item)
        category = (
            "프로젝트"
            if len(msg_project_list) > 0 and len(msg_task_list) == 0
            else "태스크"
            if len(msg_project_list) == 0 and len(msg_task_list) > 0
            else "프로젝트 및 태스크"
            if len(msg_project_list) > 0 and len(msg_task_list) > 0
            else None
        )
        title = "⛔ 조치가 필요한 " + category + "가 " + str(len(lst_msg_item_list)) + "개 있음"
        contents = "유효하지 않은 " + category + "에 대해 서둘러 조치해주시기 바랍니다."
        if category == "프로젝트":
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": title},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": contents},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*해당 프로젝트:*\n" + "\n".join(msg_project_list),
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*확인일시:*\n"
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
            ]
        elif category == "태스크":
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": title},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": contents},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*해당 태스크:*\n" + "\n".join(msg_task_list),
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*확인일시:*\n"
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
            ]
        elif category == "프로젝트 및 태스크":
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": title},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": contents},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*해당 프로젝트:*\n" + "\n".join(msg_project_list),
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*해당 태스크:*\n" + "\n".join(msg_task_list),
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*확인일시:*\n"
                        + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
            ]
        text = title
    return blocks, text


####
#### functions for incoming requests from outside
####
def cron_remind_approvers_about_all_activity_reports_in_the_queue(request):
    activity_report_list = spreadsheets_values(
        docs_log_id, "activityReportLog!A:R", False, False
    )
    for activity_report_row in activity_report_list:
        if (
            "대기" in activity_report_row[8]
            and datetime.datetime.now()
            > datetime.datetime.strptime(
                activity_report_row[2].split("(")[0]
                + " "
                + activity_report_row[2].split(") ")[1],
                "%Y-%m-%d %H:%M",
            )
            + datetime.timedelta(days=1)
        ):
            try:
                client.conversations_join(channel=management_all_channel_id)
            except:
                pass
            blocks, text = slack_blocks_and_text(
                str_project=activity_report_row[0],
                str_title=activity_report_row[1],
                str_drafter_datetime=activity_report_row[2],
                str_drafter=activity_report_row[3],
                str_drafter_email=activity_report_row[4],
                str_approver_email=activity_report_row[7],
                str_activity_report_id=activity_report_row[9].replace(
                    "https://docs.google.com/document/d/", ""
                ),
                boolean_reminder=True,
            )
            client.chat_postMessage(
                channel=management_all_channel_id,
                link_names=True,
                as_user=True,
                blocks=blocks,
                text=text,
            )
    return HttpResponse(status=200)


def cron_notify_about_tasks_done(request):
    if ("07:59" < datetime.datetime.now().strftime("%H:%M") < "08:01") or (
        "17:59" < datetime.datetime.now().strftime("%H:%M") < "18:01"
    ):
        finished_task_list = []
        finished_task_list_pre = json.loads(
            requests.post(
                f"https://api.notion.com/v1/databases/{task_db_id}/query",
                headers=notion_headers,
                data=json.dumps(
                    {
                        "filter": {
                            "and": [
                                {
                                    "property": "상태",
                                    "formula": {
                                        "string": {"does_not_contain": "⛔ MSG"}
                                    },
                                },
                                {"property": "완료", "checkbox": {"equals": True}},
                                {
                                    "property": "완료 Slack 메시지 URL",
                                    "url": {"is_empty": True},
                                },
                            ]
                        }
                    }
                ),
            ).text
        ).get("results")
        for i in range(len(finished_task_list_pre)):
            task_id = finished_task_list_pre[i].get("id")
            try:
                task_title_length = len(
                    finished_task_list_pre[i].get("properties").get("태스크").get("title")
                )
                task_title_list = []
                for j in range(task_title_length):
                    task_title_raw = (
                        finished_task_list_pre[i]
                        .get("properties")
                        .get("태스크")
                        .get("title")[j]
                        .get("plain_text")
                    )
                    task_title_list.append(task_title_raw)
                task_title = "".join(task_title_list)
            except:
                task_title = (
                    finished_task_list_pre[i]
                    .get("properties")
                    .get("태스크")
                    .get("title")[0]
                    .get("plain_text")
                )
            task_responsibility_email = (
                finished_task_list_pre[i]
                .get("properties")
                .get("태스크 담당자")
                .get("people")[0]
                .get("person")
                .get("email")
            )
            task_url = finished_task_list_pre[i].get("url")
            task_deadline = (
                finished_task_list_pre[i]
                .get("properties")
                .get("마감일")
                .get("date")
                .get("start")
            )
            finished_task_list.append(
                [
                    task_id,
                    task_title,
                    task_responsibility_email,
                    task_url,
                    task_deadline,
                ]
            )
            finished_task_list.reverse()
        if len(finished_task_list) > 0:
            try:
                client.conversations_join(channel=notice_all_channel_id)
            except:
                pass
            blocks, text = slack_blocks_and_text(
                lst_finished_task_list=finished_task_list,
            )
            slack_response = client.chat_postMessage(
                channel=notice_all_channel_id,
                link_names=True,
                as_user=True,
                blocks=blocks,
                text=text,
            )
            channel = slack_response.get("channel")
            ts = slack_response.get("ts").replace(".", "")
            slack_message_url = f"https://bwbluemove.slack.com/archives/{channel}/p{ts}"
            for task in finished_task_list:
                task_id = task[0]
                requests.patch(
                    f"https://api.notion.com/v1/pages/{task_id}",
                    data=json.dumps(
                        {
                            "properties": {
                                "완료 Slack 메시지 URL": {"url": f"{slack_message_url}"}
                            }
                        }
                    ),
                    headers=notion_headers,
                )
    return HttpResponse(status=200)


def cron_notify_about_tasks_to_be_done(request):
    if ("07:59" < datetime.datetime.now().strftime("%H:%M") < "08:01") or (
        "17:59" < datetime.datetime.now().strftime("%H:%M") < "18:01"
    ):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        for datetime_value in [tomorrow, today, yesterday]:
            unfinished_task_status, unfinished_task_list = get_tasks_to_be_done(
                datetime_value
            )
            if len(unfinished_task_list) > 0:
                try:
                    client.conversations_join(channel=notice_all_channel_id)
                except:
                    pass
                blocks, text = slack_blocks_and_text(
                    str_unfinished_task_status=unfinished_task_status,
                    lst_unfinished_task_list=unfinished_task_list,
                )
                client.chat_postMessage(
                    channel=notice_all_channel_id,
                    link_names=True,
                    as_user=True,
                    blocks=blocks,
                    text=text,
                )
    return HttpResponse(status=200)


def cron_notify_about_msg(request):
    if "07:59" < datetime.datetime.now().strftime("%H:%M") < "22:01":
        msg_item_list = []
        for db_id, item_category in [(project_db_id, "프로젝트"), (task_db_id, "태스크")]:
            msg_item_list_pre = json.loads(
                requests.post(
                    f"https://api.notion.com/v1/databases/{db_id}/query",
                    headers=notion_headers,
                    data=json.dumps(
                        {
                            "filter": {
                                "and": [
                                    {
                                        "property": "상태",
                                        "formula": {"string": {"contains": "⛔ MSG"}},
                                    },
                                    {
                                        "timestamp": "last_edited_time",
                                        "last_edited_time": {
                                            "before": (
                                                datetime.datetime.now(
                                                    datetime.timezone.utc
                                                ).astimezone(kst)
                                                - datetime.timedelta(minutes=5)
                                            ).isoformat()
                                        },
                                    },
                                ]
                            }
                        }
                    ),
                ).text
            ).get("results")
            for i in range(len(msg_item_list_pre)):
                item_status = (
                    msg_item_list_pre[i]
                    .get("properties")
                    .get("상태")
                    .get("formula")
                    .get("string")
                    .replace("⛔ MSG: ", "")
                )
                item_created_by_email_pre = (
                    msg_item_list_pre[i].get("created_by").get("id")
                )
                item_created_by_email = (
                    get_notion_user_info(item_created_by_email_pre)
                    .get("person")
                    .get("email")
                )
                try:
                    item_title = (
                        msg_item_list_pre[i]
                        .get("properties")
                        .get(item_category)
                        .get("title")[0]
                        .get("plain_text")
                    )
                except:
                    item_title = f"제목 없는 {item_category}"
                try:
                    item_responsibility_email = (
                        msg_item_list_pre[i]
                        .get("properties")
                        .get(f"{item_category} 담당자")
                        .get("people")[0]
                        .get("person")
                        .get("email")
                    )
                except:
                    item_responsibility_email = None
                item_url = msg_item_list_pre[i].get("url")
                msg_item_list.append(
                    [
                        item_category,
                        item_status,
                        item_created_by_email,
                        item_title,
                        item_responsibility_email,
                        item_url,
                    ]
                )
                msg_item_list.reverse()
        if len(msg_item_list) > 0:
            try:
                client.conversations_join(channel=notice_all_channel_id)
            except:
                pass
            blocks, text = slack_blocks_and_text(
                lst_msg_item_list=msg_item_list,
            )
            client.chat_postMessage(
                channel=notice_all_channel_id,
                link_names=True,
                as_user=True,
                blocks=blocks,
                text=text,
            )
    return HttpResponse(status=200)


####
#### views
####
def activityreport(request):
    # str, lst
    activity_report_id = (
        request.GET.get("activity_report_id")
        if request.method == "GET"
        else request.POST.get("activityReportIdPost")
    )
    activity_report_list = []
    if request.POST.get("activityReportProject"):
        project = request.POST.get("activityReportProject").split("#")[0]
        approver = request.POST.get("activityReportProject").split("#")[1]
        approver_email = request.POST.get("activityReportProject").split("#")[2]
        project_folder_url = request.POST.get("activityReportProject").split("#")[3]
        project_url = request.POST.get("activityReportProject").split("#")[4]
    title = request.POST.get("activityReportTitle")
    date = request.POST.get("activityReportDate")
    time_start = request.POST.get("activityReportTimeStart")
    time_end = request.POST.get("activityReportTimeEnd")
    duration = request.POST.get("activityReportDuration")
    address = request.POST.get("activityReportAddress")
    drafter = request.POST.get("activityReportDrafter")
    drafter_email = (
        request.user.email.lower() if request.user.is_authenticated else None
    )
    content = request.POST.get("activityReportContent")
    image_one_id = request.POST.get("activityReportImageOneId")
    image_two_id = request.POST.get("activityReportImageTwoId")
    image_three_id = request.POST.get("activityReportImageThreeId")
    participant = request.POST.get("activityReportParticipantAddedNameNumberEmail")
    rejection_reason_post = request.POST.get("activityReportRejectionReasonPost")
    q = request.GET.get("q")
    project_list = []
    bluemover_list = []
    bluemover_list_self = []
    # boolean
    approve = None
    reject = None
    trashed = None
    wrong_url = None
    submit = None
    write = None
    # cmd
    cmd_get = request.GET.get("cmdGet")
    cmd_post = request.POST.get("cmdPost")
    ####
    #### template 03
    ####
    if (
        not activity_report_id == None
        and request.user.is_authenticated
        and "@bluemove.or.kr" in request.user.email
    ):
        # activity report details
        try:
            drive_service.files().get(
                fileId=activity_report_id, supportsAllDrives=True
            ).execute()
            if (
                drive_service.files()
                .get(
                    fileId=activity_report_id, supportsAllDrives=True, fields="trashed"
                )
                .execute()
                .get("trashed")
                == True
            ):
                trashed = True
                try:
                    client.conversations_join(channel=management_dev_channel_id)
                except:
                    pass
                blocks, text = slack_blocks_and_text(
                    request=request, str_activity_report_id=activity_report_id
                )
                client.chat_postMessage(
                    channel=management_dev_channel_id,
                    link_names=True,
                    as_user=True,
                    blocks=blocks,
                    text=text,
                )
            else:
                activity_report_list_raw = spreadsheets_values(
                    docs_log_id, "activityReportLog!A:S", True, False
                )
                for i, activity_report_row in enumerate(activity_report_list_raw):
                    if (
                        "https://docs.google.com/document/d/" + activity_report_id
                        in activity_report_row
                    ):
                        activity_report_project = activity_report_row[0]
                        activity_report_title = activity_report_row[1]
                        activity_report_drafter_datetime = activity_report_row[2]
                        activity_report_drafter = activity_report_row[3]
                        activity_report_drafter_email = activity_report_row[4]
                        activity_report_approver_datetime = activity_report_row[5]
                        activity_report_approver = activity_report_row[6]
                        activity_report_approver_email = activity_report_row[7]
                        activity_report_status = activity_report_row[8]
                        activity_report_id = activity_report_row[9].replace(
                            "https://docs.google.com/document/d/", ""
                        )
                        activity_report_url = activity_report_row[9]
                        activity_report_project_folder_url = activity_report_row[10]
                        activity_report_project_url = activity_report_row[11]
                        activity_report_date = activity_report_row[12]
                        activity_report_time_duration = activity_report_row[13]
                        activity_report_address = activity_report_row[14]
                        activity_report_content = activity_report_row[15]
                        activity_report_image_one_id = activity_report_row[16].split(
                            "#"
                        )[0]
                        activity_report_image_two_id = activity_report_row[16].split(
                            "#"
                        )[1]
                        activity_report_image_three_id = activity_report_row[16].split(
                            "#"
                        )[2]
                        activity_report_participant = ast.literal_eval(
                            base64.urlsafe_b64decode(
                                bytes(activity_report_row[17], "utf-8")
                            ).decode("utf8")
                        )
                        activity_report_rejection_reason = activity_report_row[18]
                        activity_report_row_index = i + 2
                        # approve the activity report
                        if cmd_post == "approve":
                            for i in range(len(activity_report_participant)):
                                participant_birth = activity_report_participant[i][2]
                                participant_phone = activity_report_participant[i][3]
                                docs_service.documents().batchUpdate(
                                    documentId=activity_report_id,
                                    body={
                                        "requests": [
                                            {
                                                "replaceAllText": {
                                                    "containsText": {
                                                        "text": activity_report_approver
                                                        + " / 대기",
                                                        "matchCase": "true",
                                                    },
                                                    "replaceText": activity_report_approver
                                                    + " / 승인",
                                                }
                                            },
                                            {
                                                "replaceAllText": {
                                                    "containsText": {
                                                        "text": participant_birth.replace(
                                                            participant_birth[:4],
                                                            "****",
                                                        ),
                                                        "matchCase": "true",
                                                    },
                                                    "replaceText": participant_birth,
                                                }
                                            },
                                            {
                                                "replaceAllText": {
                                                    "containsText": {
                                                        "text": participant_phone.replace(
                                                            participant_phone[-4:],
                                                            "****",
                                                        ),
                                                        "matchCase": "true",
                                                    },
                                                    "replaceText": participant_phone,
                                                }
                                            },
                                        ]
                                    },
                                ).execute()
                            activity_report = drive_service.files().export(
                                fileId=activity_report_id, mimeType="application/pdf"
                            )
                            activity_report_name = (
                                "블루무브포털_일일활동보고서"
                                + activity_report_title.replace(" ", "")
                                + activity_report_id[:5]
                                + "_"
                                + datetime.date.today().strftime("%y%m%d")
                                + ".pdf"
                            )
                            fh = io.FileIO(activity_report_name, "wb")
                            downloader = MediaIoBaseDownload(fh, activity_report)
                            done = False
                            while done is False:
                                done = downloader.next_chunk()
                            fh.close()
                            mail_service.users().messages().send(
                                userId=google_delegated_email,
                                body=gmail_message(
                                    activity_report_name,
                                    activity_report_title,
                                    activity_report_date,
                                    activity_report_time_duration,
                                    activity_report_address,
                                    activity_report_approver,
                                    activity_report_approver_email,
                                    request.user.profile.phone,
                                ),
                            ).execute()
                            for i in range(len(activity_report_participant)):
                                participant_birth = activity_report_participant[i][2]
                                participant_phone = activity_report_participant[i][3]
                                docs_service.documents().batchUpdate(
                                    documentId=activity_report_id,
                                    body={
                                        "requests": [
                                            {
                                                "replaceAllText": {
                                                    "containsText": {
                                                        "text": participant_birth,
                                                        "matchCase": "true",
                                                    },
                                                    "replaceText": participant_birth.replace(
                                                        participant_birth[:4], "****"
                                                    ),
                                                }
                                            },
                                            {
                                                "replaceAllText": {
                                                    "containsText": {
                                                        "text": participant_phone,
                                                        "matchCase": "true",
                                                    },
                                                    "replaceText": participant_phone.replace(
                                                        participant_phone[-4:], "****"
                                                    ),
                                                }
                                            },
                                        ]
                                    },
                                ).execute()
                            drive_service.files().update(
                                fileId=activity_report_id,
                                supportsAllDrives=True,
                                addParents=activity_report_project_folder_url.replace(
                                    "https://drive.google.com/drive/folders/", ""
                                ),
                                body={
                                    "contentRestrictions": [
                                        {
                                            "readOnly": "true",
                                            "reason": "일일활동보고서 승인",
                                        }
                                    ]
                                },
                            ).execute()
                            os.remove(activity_report_name)
                            sheets_service.spreadsheets().values().update(
                                spreadsheetId=docs_log_id,
                                range=spreadsheets_range(
                                    "activityReportLog",
                                    "A",
                                    "I",
                                    activity_report_row_index,
                                ),
                                valueInputOption="USER_ENTERED",
                                body={
                                    "values": [
                                        [
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            datetime.datetime.now().strftime("%Y-%m-%d")
                                            + datetime_day_split(
                                                datetime.datetime.now().strftime("%w")
                                            )
                                            + datetime.datetime.now().strftime(
                                                " %H:%M"
                                            ),
                                            None,
                                            None,
                                            "승인",
                                        ]
                                    ]
                                },
                            ).execute()
                            sheets_service.spreadsheets().batchUpdate(
                                spreadsheetId=docs_log_id,
                                body={
                                    "requests": [
                                        {
                                            "updateSpreadsheetProperties": {
                                                "properties": {
                                                    "title": "E01_문서대장_"
                                                    + datetime.datetime.now().strftime(
                                                        "%y%m%d"
                                                    )
                                                },
                                                "fields": "title",
                                            }
                                        },
                                    ]
                                },
                            ).execute()
                            activity_report_list_raw = spreadsheets_values(
                                docs_log_id,
                                spreadsheets_range(
                                    "activityReportLog",
                                    "A",
                                    "I",
                                    activity_report_row_index,
                                ),
                                False,
                                False,
                            )
                            activity_report_approver_datetime = [
                                activity_report_row[5]
                                for activity_report_row in activity_report_list_raw
                            ][0]
                            activity_report_status = [
                                activity_report_row[8]
                                for activity_report_row in activity_report_list_raw
                            ][0]
                            try:
                                client.conversations_join(
                                    channel=management_all_channel_id
                                )
                            except:
                                pass
                            blocks, text = slack_blocks_and_text(
                                request=request,
                                str_project=activity_report_project,
                                str_title=activity_report_title,
                                str_drafter_email=activity_report_drafter_email,
                                str_approver_datetime=activity_report_approver_datetime,
                                str_approver=activity_report_approver,
                                str_approver_email=activity_report_approver_email,
                                str_activity_report_id=activity_report_id,
                            )
                            client.chat_postMessage(
                                channel=management_all_channel_id,
                                link_names=True,
                                as_user=True,
                                blocks=blocks,
                                text=text,
                            )
                            approve = True
                        if cmd_post == "reject":
                            docs_service.documents().batchUpdate(
                                documentId=activity_report_id,
                                body={
                                    "requests": [
                                        {
                                            "replaceAllText": {
                                                "containsText": {
                                                    "text": activity_report_approver
                                                    + " / 대기",
                                                    "matchCase": "true",
                                                },
                                                "replaceText": activity_report_approver
                                                + " / 반려",
                                            }
                                        },
                                    ]
                                },
                            ).execute()
                            drive_service.files().update(
                                fileId=activity_report_id,
                                addParents="1pYlB7YlAC_3nybHce38wRhOCWt-GpxdR",
                                body={
                                    "contentRestrictions": [
                                        {
                                            "readOnly": "true",
                                            "reason": "일일활동보고서 반려",
                                        }
                                    ]
                                },
                            ).execute()
                            sheets_service.spreadsheets().values().update(
                                spreadsheetId=docs_log_id,
                                range=spreadsheets_range(
                                    "activityReportLog",
                                    "A",
                                    "S",
                                    activity_report_row_index,
                                ),
                                valueInputOption="USER_ENTERED",
                                body={
                                    "values": [
                                        [
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            datetime.datetime.now().strftime("%Y-%m-%d")
                                            + datetime_day_split(
                                                datetime.datetime.now().strftime("%w")
                                            )
                                            + datetime.datetime.now().strftime(
                                                " %H:%M"
                                            ),
                                            None,
                                            None,
                                            "반려",
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            None,
                                            rejection_reason_post,
                                        ]
                                    ]
                                },
                            ).execute()
                            sheets_service.spreadsheets().batchUpdate(
                                spreadsheetId=docs_log_id,
                                body={
                                    "requests": [
                                        {
                                            "updateSpreadsheetProperties": {
                                                "properties": {
                                                    "title": "E01_문서대장_"
                                                    + datetime.datetime.now().strftime(
                                                        "%y%m%d"
                                                    )
                                                },
                                                "fields": "title",
                                            }
                                        },
                                    ]
                                },
                            ).execute()
                            activity_report_list_raw = spreadsheets_values(
                                docs_log_id,
                                spreadsheets_range(
                                    "activityReportLog",
                                    "A",
                                    "S",
                                    activity_report_row_index,
                                ),
                                False,
                                False,
                            )
                            activity_report_approver_datetime = [
                                activity_report_row[5]
                                for activity_report_row in activity_report_list_raw
                            ][0]
                            activity_report_status = [
                                activity_report_row[8]
                                for activity_report_row in activity_report_list_raw
                            ][0]
                            activity_report_rejection_reason = [
                                activity_report_row[18]
                                for activity_report_row in activity_report_list_raw
                            ][0]
                            try:
                                client.conversations_join(
                                    channel=management_all_channel_id
                                )
                            except:
                                pass
                            blocks, text = slack_blocks_and_text(
                                request=request,
                                str_project=activity_report_project,
                                str_title=activity_report_title,
                                str_drafter_email=activity_report_drafter_email,
                                str_approver_datetime=activity_report_approver_datetime,
                                str_approver=activity_report_approver,
                                str_approver_email=activity_report_approver_email,
                                str_rejection_reason=rejection_reason_post,
                                str_activity_report_id=activity_report_id,
                            )
                            client.chat_postMessage(
                                channel=management_all_channel_id,
                                link_names=True,
                                as_user=True,
                                blocks=blocks,
                                text=text,
                            )
                            reject = True
                        activity_report_dict = {
                            "project": activity_report_project,
                            "title": activity_report_title,
                            "drafter_datetime": activity_report_drafter_datetime,
                            "drafter": activity_report_drafter,
                            "drafter_email": activity_report_drafter_email,
                            "approver_datetime": activity_report_approver_datetime,
                            "approver": activity_report_approver,
                            "approver_email": activity_report_approver_email,
                            "status": activity_report_status,
                            "id": activity_report_id,
                            "url": activity_report_url,
                            "project_folder_url": activity_report_project_folder_url,
                            "project_url": activity_report_project_url,
                            "date": activity_report_date,
                            "time_duration": activity_report_time_duration,
                            "address": activity_report_address,
                            "content": activity_report_content,
                            "image_one_id": activity_report_image_one_id,
                            "image_two_id": activity_report_image_two_id,
                            "image_three_id": activity_report_image_three_id,
                            "participant": activity_report_participant,
                            "rejection_reason": activity_report_rejection_reason,
                        }
                        activity_report_list.append(activity_report_dict.copy())
                return render(
                    request,
                    "draftnapprove/activityreport.html",
                    {
                        # str, lst
                        "activity_report_list": activity_report_list,
                        # boolean
                        "approve": approve,
                        "reject": reject,
                    },
                )
        except:
            wrong_url = True
    elif not activity_report_id == None and (
        request.user.is_anonymous
        or (
            request.user.is_authenticated
            and not "@bluemove.or.kr" in request.user.email
        )
    ):
        return redirect("draftnapprove:activityreport")
    ####
    #### template 02
    ####
    # submit the activity report
    if cmd_post == "submit" and "@bluemove.or.kr" in request.user.email:
        submit = True
        directory_code = (
            drive_service.files()
            .get(
                fileId=project_folder_url.replace(
                    "https://drive.google.com/drive/folders/", ""
                ),
                supportsAllDrives=True,
                fields="name",
            )
            .execute()
            .get("name")[:3]
        )
        activity_report_id = (
            drive_service.files()
            .copy(
                fileId=activity_report_temp_id,
                supportsAllDrives=True,
                body={
                    "name": directory_code
                    + "_일일활동보고서"
                    + title.replace(" ", "")
                    + "_"
                    + datetime.date.today().strftime("%y%m%d"),
                    "parents": [activity_report_folder_id],
                },
                fields="id",
            )
            .execute()
            .get("id")
        )
        image_one_object_id = image_object_id(activity_report_id)[1]
        image_two_object_id = image_object_id(activity_report_id)[2]
        image_three_object_id = image_object_id(activity_report_id)[0]
        docs_service.documents().batchUpdate(
            documentId=activity_report_id,
            body={
                "requests": [
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ project }}",
                                "matchCase": "true",
                            },
                            "replaceText": project,
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ title }}",
                                "matchCase": "true",
                            },
                            "replaceText": title,
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ date }}",
                                "matchCase": "true",
                            },
                            "replaceText": date,
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ time_duration }}",
                                "matchCase": "true",
                            },
                            "replaceText": time_start
                            + "~"
                            + time_end
                            + " ("
                            + duration
                            + ")",
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ address }}",
                                "matchCase": "true",
                            },
                            "replaceText": address,
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ drafter }}",
                                "matchCase": "true",
                            },
                            "replaceText": drafter,
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ approver }}",
                                "matchCase": "true",
                            },
                            "replaceText": approver,
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ status }}",
                                "matchCase": "true",
                            },
                            "replaceText": "대기",
                        }
                    },
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": "{{ content }}",
                                "matchCase": "true",
                            },
                            "replaceText": content,
                        }
                    },
                    {
                        "replaceImage": {
                            "imageObjectId": image_one_object_id,
                            "uri": "https://lh3.googleusercontent.com/d/"
                            + image_one_id,
                            "imageReplaceMethod": "CENTER_CROP",
                        }
                    },
                    {
                        "replaceImage": {
                            "imageObjectId": image_two_object_id,
                            "uri": "https://lh3.googleusercontent.com/d/"
                            + image_two_id,
                            "imageReplaceMethod": "CENTER_CROP",
                        }
                    },
                    {
                        "replaceImage": {
                            "imageObjectId": image_three_object_id,
                            "uri": "https://lh3.googleusercontent.com/d/"
                            + image_three_id,
                            "imageReplaceMethod": "CENTER_CROP",
                        }
                    },
                ]
            },
        ).execute()
        bluemover_list = spreadsheets_values(register_id, "register!A:L", True, True)
        participant_list = []
        for i in range(len(participant.split(","))):
            participant_name = participant.split(",")[i].split("#")[0]
            participant_number = participant.split(",")[i].split("#")[1]
            participant_birth = [
                bluemover_row[9]
                for bluemover_row in bluemover_list
                if participant_number in bluemover_row
            ][0]
            participant_phone = [
                bluemover_row[11]
                for bluemover_row in bluemover_list
                if participant_number in bluemover_row
            ][0]
            participant_list.append(
                [
                    participant_name,
                    participant_number,
                    participant_birth,
                    participant_phone,
                ]
            )
            docs_service.documents().batchUpdate(
                documentId=activity_report_id,
                body={
                    "requests": [
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(i + 1) + " }}",
                                    "matchCase": "true",
                                },
                                "replaceText": str(i + 1),
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(i + 1) + "_name }}",
                                    "matchCase": "true",
                                },
                                "replaceText": participant_name,
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(i + 1) + "_sn }}",
                                    "matchCase": "true",
                                },
                                "replaceText": participant_number,
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(i + 1) + "_birth }}",
                                    "matchCase": "true",
                                },
                                "replaceText": participant_birth.replace(
                                    participant_birth[:4], "****"
                                ),
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(i + 1) + "_phone }}",
                                    "matchCase": "true",
                                },
                                "replaceText": participant_phone.replace(
                                    participant_phone[9:], "****"
                                ),
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(i + 1) + "_time_duration }}",
                                    "matchCase": "true",
                                },
                                "replaceText": time_start
                                + "~"
                                + time_end
                                + " ("
                                + duration
                                + ")",
                            }
                        },
                    ]
                },
            ).execute()
        for i in range(15 - len(participant.split(","))):
            docs_service.documents().batchUpdate(
                documentId=activity_report_id,
                body={
                    "requests": [
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(15 - i) + " }}",
                                    "matchCase": "true",
                                },
                                "replaceText": "",
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(15 - i) + "_name }}",
                                    "matchCase": "true",
                                },
                                "replaceText": "",
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(15 - i) + "_sn }}",
                                    "matchCase": "true",
                                },
                                "replaceText": "",
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(15 - i) + "_birth }}",
                                    "matchCase": "true",
                                },
                                "replaceText": "",
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(15 - i) + "_phone }}",
                                    "matchCase": "true",
                                },
                                "replaceText": "",
                            }
                        },
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": "{{ p_" + str(15 - i) + "_time_duration }}",
                                    "matchCase": "true",
                                },
                                "replaceText": "",
                            }
                        },
                    ]
                },
            ).execute()
        drive_service.permissions().create(
            fileId=activity_report_id,
            sendNotificationEmail=False,
            body={
                "role": "reader",
                "type": "domain",
                "domain": "bluemove.or.kr",
            },
        ).execute()
        drive_service.revisions().update(
            fileId=activity_report_id,
            revisionId="1",
            body={
                "publishAuto": "true",
                "published": "true",
                "publishedOutsideDomain": "false",
            },
        ).execute()
        sheets_service.spreadsheets().values().append(
            spreadsheetId=docs_log_id,
            range="activityReportLog!A1:S1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [
                    [
                        project,
                        title,
                        datetime.datetime.now().strftime("%Y-%m-%d")
                        + datetime_day_split(datetime.datetime.now().strftime("%w"))
                        + datetime.datetime.now().strftime(" %H:%M"),
                        drafter,
                        drafter_email,
                        "-",
                        approver,
                        approver_email,
                        "대기",
                        "https://docs.google.com/document/d/" + activity_report_id,
                        project_folder_url,
                        project_url,
                        date,
                        time_start + "~" + time_end + " (" + duration + ")",
                        address,
                        content,
                        image_one_id + "#" + image_two_id + "#" + image_three_id,
                        base64.urlsafe_b64encode(
                            bytes(str(participant_list), "utf-8")
                        ).decode("utf8"),
                        "-",
                    ]
                ]
            },
        ).execute()
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=docs_log_id,
            body={
                "requests": [
                    {
                        "updateSpreadsheetProperties": {
                            "properties": {
                                "title": "E01_문서대장_"
                                + datetime.datetime.now().strftime("%y%m%d")
                            },
                            "fields": "title",
                        }
                    },
                ]
            },
        ).execute()
        try:
            client.conversations_join(channel=management_all_channel_id)
        except:
            pass
        blocks, text = slack_blocks_and_text(
            request=request,
            str_project=project,
            str_title=title,
            str_drafter_datetime=datetime.datetime.now().strftime("%Y-%m-%d")
            + datetime_day_split(datetime.datetime.now().strftime("%w"))
            + datetime.datetime.now().strftime(" %H:%M"),
            str_drafter=drafter,
            str_drafter_email=drafter_email,
            str_approver_email=approver_email,
            str_activity_report_id=activity_report_id,
        )
        client.chat_postMessage(
            channel=management_all_channel_id,
            link_names=True,
            as_user=True,
            blocks=blocks,
            text=text,
        )
    # write an activity report
    if cmd_post == "write" and "@bluemove.or.kr" in request.user.email:
        write = True
        project_list_pre = json.loads(
            requests.post(
                f"https://api.notion.com/v1/databases/{project_db_id}/query",
                headers=notion_headers,
                data=json.dumps(
                    {
                        "filter": {
                            "property": "종료일",
                            "date": {
                                "on_or_after": (
                                    datetime.datetime.now(
                                        datetime.timezone.utc
                                    ).astimezone(kst)
                                ).isoformat()
                            },
                        },
                        "sorts": [
                            {"property": "완료 여부", "direction": "ascending"},
                            {"property": "종료일", "direction": "ascending"},
                        ],
                    }
                ),
            ).text
        ).get("results")
        for i in range(len(project_list_pre)):
            project_title = (
                project_list_pre[i]
                .get("properties")
                .get("프로젝트")
                .get("title")[0]
                .get("plain_text")
            )
            project_approver = (
                project_list_pre[i]
                .get("properties")
                .get("프로젝트 담당자")
                .get("people")[0]
                .get("name")
            )
            project_approver_email = (
                project_list_pre[i]
                .get("properties")
                .get("프로젝트 담당자")
                .get("people")[0]
                .get("person")
                .get("email")
            )
            project_folder_url = (
                project_list_pre[i].get("properties").get("프로젝트 폴더 URL").get("url")
            )
            project_url = project_list_pre[i].get("url")
            project_list.append(
                [
                    project_title,
                    project_approver,
                    project_approver_email,
                    project_folder_url,
                    project_url,
                ]
            )
        bluemover_directory = (
            admin_service.users()
            .list(domain="bluemove.or.kr", orderBy="familyName")
            .execute()
            .get("users")
        )
        for i in range(len(bluemover_directory)):
            bluemover_org_unit = (
                bluemover_directory[i].get("orgUnitPath").replace("/", "")
            )
            if bluemover_org_unit:
                bluemover_name = bluemover_directory[i].get("name").get("fullName")
                bluemover_number = (
                    bluemover_directory[i].get("externalIds")[0].get("value")
                )
                bluemover_email = bluemover_directory[i].get("emails")[0].get("address")
                if not request.user.email in bluemover_email:
                    bluemover_list.append(
                        [
                            bluemover_name,
                            bluemover_org_unit,
                            bluemover_number,
                            bluemover_email,
                        ]
                    )
                if request.user.email in bluemover_email:
                    bluemover_list_self.append(
                        [
                            bluemover_name,
                            bluemover_org_unit,
                            bluemover_number,
                            bluemover_email,
                        ]
                    )
        bluemover_list.sort()
        return render(
            request,
            "draftnapprove/activityreport.html",
            {
                # str, lst
                "project_list": project_list,
                "bluemover_list": bluemover_list,
                "bluemover_list_self": bluemover_list_self,
                # boolean
                "write": write,
            },
        )
    ####
    #### template 01
    ####
    # get the activity report log
    activity_report_list_raw = spreadsheets_values(
        docs_log_id, "activityReportLog!A:J", True, True
    )
    for activity_report_row in activity_report_list_raw:
        activity_report_project = activity_report_row[0]
        activity_report_title = activity_report_row[1]
        activity_report_drafter_datetime = activity_report_row[2]
        activity_report_drafter = activity_report_row[3]
        activity_report_drafter_email = activity_report_row[4]
        activity_report_approver_datetime = activity_report_row[5]
        activity_report_approver = activity_report_row[6]
        activity_report_approver_email = activity_report_row[7]
        activity_report_status = activity_report_row[8]
        activity_report_id = activity_report_row[9].replace(
            "https://docs.google.com/document/d/", ""
        )
        if request.user.is_authenticated and "@bluemove.or.kr" in request.user.email:
            pass
        else:
            activity_report_drafter_datetime = activity_report_drafter_datetime[
                :8
            ] + re.sub("[^-() :]", "*", activity_report_drafter_datetime[8:])
            activity_report_drafter = activity_report_drafter[0] + re.sub(
                "[\S]", "*", activity_report_drafter[1:]
            )
            if not activity_report_approver_datetime == "-":
                activity_report_approver_datetime = activity_report_approver_datetime[
                    :8
                ] + re.sub("[^-() :]", "*", activity_report_approver_datetime[8:])
            activity_report_approver = activity_report_approver[0] + re.sub(
                "[\S]", "*", activity_report_approver[1:]
            )
        activity_report_dict = {
            "project": activity_report_project,
            "title": activity_report_title,
            "drafter_datetime": activity_report_drafter_datetime,
            "drafter": activity_report_drafter,
            "drafter_email": activity_report_drafter_email,
            "approver_datetime": activity_report_approver_datetime,
            "approver": activity_report_approver,
            "approver_email": activity_report_approver_email,
            "status": activity_report_status,
            "id": activity_report_id,
        }
        activity_report_list.append(activity_report_dict.copy())
    # search
    try:
        if len(q) > 1:
            activity_report_list_pre = [
                activity_report_row
                for activity_report_row in activity_report_list
                for activity_report_str in activity_report_row.values()
                if q in activity_report_str
            ]
            activity_report_list = []
            for i in activity_report_list_pre:
                if i not in activity_report_list:
                    activity_report_list.append(i)
        else:
            pass
    except:
        q = None
    # paginator
    page = request.GET.get("page", 1)
    paginator = Paginator(activity_report_list, 15)
    try:
        activity_report_list = paginator.page(page)
    except PageNotAnInteger:
        activity_report_list = paginator.page(1)
    except EmptyPage:
        activity_report_list = paginator.page(paginator.num_pages)
    return render(
        request,
        "draftnapprove/activityreport.html",
        {
            # str, lst
            "activity_report_list": activity_report_list,
            "q": q,
            # boolean
            "submit": submit,
            "trashed": trashed,
            "wrong_url": wrong_url,
        },
    )
