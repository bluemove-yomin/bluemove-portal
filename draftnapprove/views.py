from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Google OAuth 2.0
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials

# Gmail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import base64

# Notion
import requests, json

# multiple functions
import datetime

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
sheets_service = build("sheets", "v4", credentials=credentials_delegated)
slides_service = build("slides", "v1", credentials=credentials_delegated)
mail_service = build("gmail", "v1", credentials=credentials_delegated)
admin_service = build("admin", "directory_v1", credentials=credentials_delegated)

# Notion API
notion_headers = {
    "Authorization": f"Bearer " + notion_token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-08-16",
}

# Bluemove data
docs_log_id = "10-ROxf9XjSRIN7R71EIiAQCstre8jqOwrfxbEC_uRX4"
project_db_id = "d17acacd-fb64-4e0d-9f75-462424c7cb81"


####
#### views
####
def activityreport(request):
    # str, lst
    q = request.GET.get("q")
    project_list = []
    bluemover_list = []
    # boolean
    write = None
    # cmd
    cmd_get = request.GET.get("cmdGet")
    cmd_post = request.POST.get("cmdPost")
    ####
    #### template 02
    ####
    # write an activity report
    if cmd_post == "write" and request.user.is_authenticated:
        write = True
        project_list_pre = json.loads(
            requests.post(
                "https://api.notion.com/v1/databases/" + project_db_id + "/query",
                headers=notion_headers,
                data=(
                    '{ "filter": {"property": "종료일", "date": {"on_or_after": "'
                    + str(datetime.datetime.now().isoformat())
                    + '"} }, "sorts": [ {"property": "완료", "direction": "ascending"}, {"property": "종료일", "direction": "ascending"} ] }'
                ).encode("utf-8"),
            ).text
        )
        for i in range(len(project_list_pre.get("results"))):
            project_title = (
                project_list_pre.get("results")[i]
                .get("properties")
                .get("프로젝트")
                .get("title")[0]
                .get("plain_text")
            )
            project_url = project_list_pre.get("results")[i].get("url")
            project_list.append(tuple((project_title, project_url)))
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
                bluemover_email = bluemover_directory[i].get("emails")[0].get("address")
                bluemover_list.append([bluemover_name, bluemover_email, bluemover_org_unit])
        return render(
            request,
            "draftnapprove/activityreport.html",
            {
                # str, lst
                "project_list_pre": project_list_pre,
                "project_list": project_list,
                "bluemover_list": bluemover_list,
                # boolean
                "write": write,
            },
        )
    ####
    #### template 01
    ####
    # get the activity report log
    activity_report_list = (
        sheets_service.spreadsheets()
        .values()
        .get(
            spreadsheetId=docs_log_id,
            range="activityReportLog!A:H",
            majorDimension="ROWS",
        )
        .execute()
    ).get("values")
    del activity_report_list[0]
    activity_report_list.reverse()
    # search
    try:
        if len(q) > 1:
            activity_report_list_pre = [
                activity_report_row
                for activity_report_row in activity_report_list
                for activity_report_str in activity_report_row
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
        {"activity_report_list": activity_report_list, "q": q},
    )
