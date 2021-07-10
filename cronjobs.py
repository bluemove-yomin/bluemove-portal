import requests


# applynsubmit
requests.get(
    "https://portal.bluemove.or.kr/applynsubmit/applymembership/cron-delete-all-expired-recruiting-data"
)

# member
requests.get(
    "https://portal.bluemove.or.kr/member/cron-delete-all-inactive-users"
)