# coding: utf-8
from celery import shared_task, subtask
from django.utils.translation import ugettext as _
from django.utils import timezone


from common.utils import get_logger, get_object_or_none, encrypt_password
from .celery.utils import register_as_period_task, after_app_shutdown_clean
from .models import Task, CommandExecution

logger = get_logger(__file__)


def rerun_task():
    pass


@shared_task
def run_ansible_task(tid, callback=None, **kwargs):
    """
    :param tid: is the tasks serialized data
    :param callback: callback function name
    :return:
    """
    task = get_object_or_none(Task, id=tid)
    if task:
        result = task.run()
        if callback is not None:
            subtask(callback).delay(result, task_name=task.name)
        return result
    else:
        logger.error("No task found")


@shared_task
def run_command_execution(cid, **kwargs):
    execution = get_object_or_none(CommandExecution, id=cid)
    return execution.run()


@shared_task
@register_as_period_task(interval=3600*24)
@after_app_shutdown_clean
def clean_tasks_adhoc_period():
    logger.debug("Start clean task adhoc and run history")
    tasks = Task.objects.all()
    for task in tasks:
        adhoc = task.adhoc.all().order_by('-date_created')[5:]
        for ad in adhoc:
            ad.history.all().delete()
            ad.delete()


@shared_task
def hello(name, callback=None):
    print("Hello {}".format(name))
    if callback is not None:
        subtask(callback).delay("Guahongwei")


@shared_task
def hello_callback(result):
    print(result)
    print("Hello callback")


def get_change_asset_password_tasks(username, password):
    tasks = list()
    tasks.append({
        'name': 'Change {} password'.format(username),
        'action': {
            'module': 'user',
            'args': 'name={} password={} update_password=always'.format(
                username, encrypt_password(password, salt="K3mIlKK")
            ),
        }
    })
    return tasks


@shared_task
def change_asset_password(username, assets, org_id, history, task_name):
    from assets.tasks import clean_hosts, const
    from assets.models import AuthBook
    from common.utils import random_password_gen
    from .utils import update_or_create_ansible_task

    password = random_password_gen()
    tasks = get_change_asset_password_tasks(username, password)
    hosts = clean_hosts(assets)
    if not hosts:
        return {}
    task, created = update_or_create_ansible_task(
        task_name=task_name, hosts=hosts, tasks=tasks, pattern='all',
        options=const.TASK_OPTIONS, run_as_admin=True,
        created_by=org_id,
    )
    result = task.run()

    summary = result[1]
    contacted = summary.get('contacted')
    if contacted:
        for hostname in contacted.keys():
            asset = assets.filter(hostname=hostname).first()
            AuthBook.create_item(
                username=username, password=password, asset=asset
            )

    history.result = summary
    history.is_finished = True
    history.date_finished = timezone.now()
    history.save()
    return result
