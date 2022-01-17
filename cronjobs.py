import requests


# applynsubmit
requests.get(
    "https://portal.bluemove.or.kr/applynsubmit/applymembership/cron-delete-all-expired-recruiting-data"
)

# draftnapprove
requests.get(
    "https://portal.bluemove.or.kr/draftnapprove/activityreport/cron-remind-approvers-about-all-activity-reports-in-the-queue"
)

# member
requests.get(
    "https://portal.bluemove.or.kr/member/cron-delete-all-inactive-users"
)