#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from django.db import models
from django.utils.translation import ugettext as _

from common.utils import get_logger

from .base import AssetUser

logger = get_logger(__file__)


class AuthBook(AssetUser):
    """
    批量改密任务执行后，存放执行成功的 <username, asset> 对应关系
    """
    asset = models.ForeignKey(
        'assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset')
    )

    class Meta:
        get_latest_by = 'date_created'

    @classmethod
    def get_latest_item_by_username_asset(cls, username, asset):
        try:
            item = AuthBook.objects.filter(username=username, asset=asset).latest()
            return item
        except Exception as e:
            logger.debug(e)
            return None
