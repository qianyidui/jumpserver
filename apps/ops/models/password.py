# -*- coding: utf-8 -*-
#


import uuid
import json
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from orgs.mixins import OrgModelMixin
from common.validators import alphanumeric
from common.utils import get_signer
from ..tasks import change_asset_password

signer = get_signer()


class ChangeAssetPasswordTask(OrgModelMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    username = models.CharField(max_length=32, verbose_name=_('Username'), validators=[alphanumeric])
    hosts = models.ManyToManyField('assets.Asset')
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=128, null=True, verbose_name=_('Created by'))

    def __str__(self):
        return self.name

    def run(self):
        history = ChangeAssetPasswordTaskHistory()
        history.date_start = timezone.now()
        history.task = self
        task_name = _('Change asset password for user: {}'.format(self.username))
        assets = self.hosts.all()
        task = change_asset_password.delay(self.username, assets, self.org_id, history, task_name)
        return task


class ChangeAssetPasswordTaskHistory(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    task = models.ForeignKey('ops.ChangeAssetPasswordTask', on_delete=models.CASCADE, verbose_name=_('Change password task'))
    _result = models.TextField(blank=True, null=True, verbose_name=_('Result'))
    is_finished = models.BooleanField(default=False)
    date_start = models.DateTimeField(null=True)
    date_finished = models.DateTimeField(null=True)

    @property
    def result(self):
        if self._result:
            return json.loads(self._result)
        else:
            return {}

    @result.setter
    def result(self, item):
        self._result = json.dumps(item)
