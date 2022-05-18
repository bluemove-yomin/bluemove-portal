import requests


# applynsubmit
requests.get(
    "https://portal.bluemove.or.kr/applynsubmit/applymembership/cron-delete-all-expired-recruiting-data"
)

requests.get(
    "https://portal.bluemove.or.kr/applynsubmit/applymembershipwithdrawal/cron-delete-queued-alumni-data"
)

# decidenshare
requests.get(
    "https://portal.bluemove.or.kr/decidenshare/sharebmlink/cron-delete-all-expired-bmlinks"
)

# draftnapprove
requests.get(
    "https://portal.bluemove.or.kr/draftnapprove/activityreport/cron-remind-approvers-about-all-activity-reports-in-the-queue"
)

requests.get(
    "https://portal.bluemove.or.kr/draftnapprove/activityreport/cron-notify-about-tasks-done"
)

requests.get(
    "https://portal.bluemove.or.kr/draftnapprove/activityreport/cron-notify-about-tasks-to-be-done"
)

requests.get(
    "https://portal.bluemove.or.kr/draftnapprove/activityreport/cron-notify-about-msg"
)

# member
requests.get(
    "https://portal.bluemove.or.kr/member/cron-delete-all-expired-v-codes"
)
requests.get(
    "https://portal.bluemove.or.kr/member/cron-delete-all-inactive-users"
)