from django.shortcuts import render, redirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Google OAuth 2.0
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials

# Short.io
import requests, json
import dateutil.parser
import pytz

# multiple functions
import datetime
import re
from django.http import HttpResponse

# secrets
google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID")
google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")
google_sa_secret = getattr(settings, "GOOGLE_SA_SECRET", "GOOGLE_SA_SECRET")
google_sa_creds = "googleSACreds.json"
google_delegated_email = getattr(
    settings, "GOOGLE_DELEGATED_EMAIL", "GOOGLE_DELEGATED_EMAIL"
)
short_io_key = getattr(settings, "SHORT_IO_KEY", "SHORT_IO_KEY")

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

# Short.io API
short_io_headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": short_io_key,
}
short_io_querystring = {"domain_id": "364373", "limit": "150", "offset": "0"}


####
#### utils
####
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


def ISO_8601_to_local_datetime(str_ISO_8601):
    local_datetime = (
        dateutil.parser.parse(str_ISO_8601)
        .replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone("Asia/Seoul"))
    )
    return local_datetime


def datetime_with_day_kor(str_ISO_8601):
    datetime = ISO_8601_to_local_datetime(str_ISO_8601)
    datetime_day_num = str(datetime.strftime("%w"))
    datetime_day_kor = datetime_day_split(datetime_day_num)
    datetime_with_day_kor = str(datetime).split(" ")[0] + datetime_day_kor
    return datetime_with_day_kor


####
#### functions for incoming requests from outside
####
def cron_delete_all_expired_bmlinks(request):
    bmlink_list_raw = json.loads(
        requests.request(
            "GET",
            "https://api.short.io/api/links",
            headers=short_io_headers,
            params=short_io_querystring,
        ).text
    ).get("links")
    for bmlink_row in bmlink_list_raw:
        bmlink_id = bmlink_row.get("idString")
        bmlink_date_end = (
            ISO_8601_to_local_datetime(bmlink_row.get("title").split("#")[2])
            if bmlink_row.get("title").split("#")[2] != "무기한"
            else "무기한"
        )
        if (
            bmlink_date_end != "무기한"
            and bmlink_date_end
            < datetime.datetime.now()
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .replace(tzinfo=pytz.utc)
            .astimezone(pytz.timezone("Asia/Seoul"))
        ):
            requests.request(
                "DELETE",
                "https://api.short.io/links/" + bmlink_id,
                headers=short_io_headers,
            )
    return HttpResponse(status=200)


####
#### views
####
def sharebmlink(request):
    # str, lst
    q = request.GET.get("q")
    bmlink_edit_category = request.POST.get("bmlinkEditCategory")
    bmlink_edit_title = request.POST.get("bmlinkEditTitle")
    bmlink_edit_id = request.POST.get("bmlinkEditId")
    bmlink_edit_path = request.POST.get("bmlinkEditPath")
    bmlink_edit_original_url = request.POST.get("bmlinkEditOriginalUrl")
    bmlink_edit_date_end = request.POST.get("bmlinkEditDateEnd")
    bmlink_edit_public_or_not = request.POST.get("bmlinkEditPublicOrNot")
    bmlink_delete_id = request.POST.get("bmlinkDeleteId")
    bmlink_create_category = request.POST.get("bmlinkCreateCategory")
    bmlink_create_title = request.POST.get("bmlinkCreateTitle")
    bmlink_create_path = request.POST.get("bmlinkCreatePath")
    bmlink_create_original_url = request.POST.get("bmlinkCreateOriginalUrl")
    bmlink_create_date_end = request.POST.get("bmlinkCreateDateEnd")
    bmlink_create_public_or_not = request.POST.get("bmlinkCreatePublicOrNot")
    category_list = []
    bmlink_list = []
    # cmd
    cmd_get = request.GET.get("cmdGet")
    cmd_post = request.POST.get("cmdPost")
    ####
    #### template 01
    ####
    # edit Bmlink
    if cmd_post == "edit":
        requests.request(
            "POST",
            "https://api.short.io/links/" + bmlink_edit_id,
            json={
                "domain": "bluemove.link",
                "title": bmlink_edit_category
                + "#"
                + bmlink_edit_title
                + "#"
                + bmlink_edit_date_end
                + "#"
                + request.user.last_name
                + request.user.first_name
                + "#"
                + bmlink_edit_public_or_not,
                "path": bmlink_edit_path,
                "originalURL": bmlink_edit_original_url,
                "allowDuplicates": False,
            },
            headers=short_io_headers,
        )
    # delete Bmlink
    if cmd_post == "delete":
        requests.request(
            "DELETE",
            "https://api.short.io/links/" + bmlink_delete_id,
            headers=short_io_headers,
        )
    # create Bmlink
    if cmd_post == "create":
        requests.request(
            "POST",
            "https://api.short.io/links/",
            json={
                "domain": "bluemove.link",
                "title": bmlink_create_category
                + "#"
                + bmlink_create_title
                + "#"
                + bmlink_create_date_end
                + "#"
                + request.user.last_name
                + request.user.first_name
                + "#"
                + bmlink_create_public_or_not,
                "path": bmlink_create_path,
                "originalURL": bmlink_create_original_url,
                "allowDuplicates": False,
            },
            headers=short_io_headers,
        )
    # Bmlink list
    category_list_raw = drive_service.drives().list().execute().get("drives")
    for category_row in category_list_raw:
        category = category_row.get("name").replace("블뭅 ", "")
        category_list.append(category)
    bmlink_list_raw = json.loads(
        requests.request(
            "GET",
            "https://api.short.io/api/links",
            headers=short_io_headers,
            params=short_io_querystring,
        ).text
    ).get("links")
    for bmlink_row in bmlink_list_raw:
        if "title" not in bmlink_row:
            continue
        bmlink_category = bmlink_row.get("title").split("#")[0]
        bmlink_title = bmlink_row.get("title").split("#")[1]
        bmlink_id = bmlink_row.get("idString")
        bmlink_path = bmlink_row.get("path")
        bmlink_url = bmlink_row.get("shortURL")
        bmlink_original_url = bmlink_row.get("originalURL")
        bmlink_date_start = datetime_with_day_kor(bmlink_row.get("createdAt"))
        bmlink_date_end = (
            datetime_with_day_kor(bmlink_row.get("title").split("#")[2])
            if bmlink_row.get("title").split("#")[2] != "무기한"
            else "무기한"
        )
        bmlink_user = bmlink_row.get("title").split("#")[3]
        bmlink_public_or_not = bmlink_row.get("title").split("#")[4]
        if bmlink_path == "":
            continue
        if request.user.is_authenticated and "@bluemove.or.kr" in request.user.email:
            pass
        elif bmlink_public_or_not == "공개":
            bmlink_user = bmlink_user[0] + re.sub("[\S]", "*", bmlink_user[1:])
            bmlink_date_start = bmlink_date_start[:8] + re.sub(
                "[^-()~]", "*", bmlink_date_start[8:]
            )
            bmlink_date_end = bmlink_date_end[:8] + re.sub(
                "[^-()~]", "*", bmlink_date_end[8:]
            )
        elif bmlink_public_or_not == "비공개":
            bmlink_category = re.sub("[\S]", "*", bmlink_category)
            bmlink_title = re.sub("[\S]", "*", bmlink_title)
            bmlink_id = re.sub("[\S]", "*", bmlink_id)
            bmlink_path = re.sub("[\S]", "*", bmlink_path)
            bmlink_url = bmlink_url[:28] + re.sub("[^:/.]", "*", bmlink_url[28:])
            bmlink_original_url = re.sub("[^:/.]", "*", bmlink_original_url)
            bmlink_user = bmlink_user[0] + re.sub("[\S]", "*", bmlink_user[1:])
            bmlink_date_start = bmlink_date_start[:8] + re.sub(
                "[^-()~]", "*", bmlink_date_start[8:]
            )
            bmlink_date_end = bmlink_date_end[:8] + re.sub(
                "[^-()~]", "*", bmlink_date_end[8:]
            )
        bmlink_dict = {
            "category": bmlink_category,
            "title": bmlink_title,
            "id": bmlink_id,
            "slug": bmlink_path,
            "url": bmlink_url,
            "original_url": bmlink_original_url,
            "user": bmlink_user,
            "date_start": bmlink_date_start,
            "date_end": bmlink_date_end,
            "public_or_not": bmlink_public_or_not,
        }
        bmlink_list.append(bmlink_dict.copy())
    # search
    try:
        if len(q) > 1:
            bmlink_list_pre = [
                bmlink_row
                for bmlink_row in bmlink_list
                for bmlink_str in bmlink_row.values()
                if q in str(bmlink_str)
            ]
            bmlink_list = []
            for i in bmlink_list_pre:
                if i not in bmlink_list:
                    bmlink_list.append(i)
        else:
            pass
    except:
        q = None
    # paginator
    page = request.GET.get("page", 1)
    paginator = Paginator(bmlink_list, 10)
    try:
        bmlink_list = paginator.page(page)
    except PageNotAnInteger:
        bmlink_list = paginator.page(1)
    except EmptyPage:
        bmlink_list = paginator.page(paginator.num_pages)
    return render(
        request,
        "decidenshare/sharebmlink.html",
        {
            # str, lst
            "category_list": category_list,
            "bmlink_list": bmlink_list,
            "q": q,
            "edited_bmlink_id": bmlink_edit_id,
        },
    )
