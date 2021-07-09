# django-cron (https://django-cron.readthedocs.io/en/latest/)
from django_cron import CronJobBase, Schedule
import datetime


class CronDeleteAllRecruitingData(CronJobBase):
    RUN_EVERY_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "applymembership.views.cron_delete_all_recruiting_data"

    def do(self):
        print("'cron_delete_all_recruiting_data' was executed at " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
