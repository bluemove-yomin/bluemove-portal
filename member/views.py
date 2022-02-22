from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

# models
from django.contrib.auth.models import User
from .models import Profile
from applynsubmit.models import Applymembership

# Slack
from slack_sdk import WebClient

# multiple functions
import re
import datetime
from django.http import HttpResponse

# secrets
slack_bot_token = getattr(settings, "SLACK_BOT_TOKEN", "SLACK_BOT_TOKEN")

# Bluemove data
management_all_channel_id = "CV3THBHJB"
management_dev_channel_id = "C01L8PETS5S"


####
#### utils
####
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
    # boolean
    modified = None
    unable_to_delete = None
    wrong_delete_msg = None
    scroll_to_modify = None
    scroll_to_delete = None
    if request.method == "POST" and not delete_msg:
        user = User.objects.get(id=request.user.id)
        user.last_name = last_name
        user.first_name = first_name
        user.save()
        profile = Profile.objects.get(user=request.user)
        profile.phone = phone
        profile.save()
        modified = True
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
            "modified": modified,
            "unable_to_delete": unable_to_delete,
            "wrong_delete_msg": wrong_delete_msg,
            "scroll_to_modify": scroll_to_modify,
            "scroll_to_delete": scroll_to_delete,
        },
    )
