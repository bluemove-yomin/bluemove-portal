from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

# models
from django.contrib.auth.models import User
from .models import Profile

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
    masked_name = obj_user.last_name + obj_user.first_name.replace(
        obj_user.first_name[0], "*"
    )
    masked_phone = (
        obj_user.profile.phone.split("-")[0]
        + "-"
        + obj_user.profile.phone.split("-")[1]
        + "-****"
    )
    masked_email_pre = (
        re.sub(r"[A-Za-z0-9._%+-]", "*", obj_user.email.split("@")[0])
        + "@"
        + obj_user.email.split("@")[1]
    )
    masked_email = obj_user.email[:2] + masked_email_pre[2:]
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
    # str, lst
    last_name = request.POST.get("last_name")
    first_name = request.POST.get("first_name")
    phone = request.POST.get("phone")
    # boolean
    modified = None
    if request.method == "POST":
        user = User.objects.get(id=request.user.id)
        user.last_name = last_name
        user.first_name = first_name
        user.save()
        profile = Profile.objects.get(user=request.user)
        profile.phone = phone
        profile.save()
        modified = True
    return render(
        request,
        "member/myaccount.html",
        {
            # boolean
            "modified": modified
        },
    )
