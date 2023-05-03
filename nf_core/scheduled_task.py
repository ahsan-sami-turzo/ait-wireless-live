from django_celery_beat.models import PeriodicTask, IntervalSchedule


def get_interval_schedule(*args, **kwargs):
    x_schedule = IntervalSchedule.objects.filter(**kwargs)
    if x_schedule.count() == 0:
        x_schedule, created = IntervalSchedule.objects.get_or_create(**kwargs)
        return x_schedule
    else:
        return x_schedule.last()


def schedule_x_task(*args, **kwargs):
    if "name" not in kwargs:
        return

    task_obj = PeriodicTask.objects.filter(name=kwargs['name'])

    if len(task_obj) > 0:
        task_obj = task_obj[0]
        for x_arg_key, x_arg_val in kwargs.items():
            setattr(task_obj, x_arg_key, x_arg_val)
        task_obj.save()
    else:
        try:
            PeriodicTask.objects.get_or_create(*args, **kwargs)
        except Exception as err:
            print(err)


schedule_1d = get_interval_schedule(
    every=1,
    period=IntervalSchedule.DAYS,
)

schedule_1min = get_interval_schedule(
    every=1,
    period=IntervalSchedule.MINUTES,
)

schedule_x_task(
    interval=schedule_1d,
    name='Run PG Partition',
    task='nf_core.tasks.createPgPartition'
)

schedule_x_task(
    interval=schedule_1min,
    name='Process Scheduled SMS',
    task='nf_core.tasks.processScheduledSMS'
)
