#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from django.db import models
from django.utils.translation import ugettext as _

from .base import AssetUser


class AuthBook(AssetUser):
    """
    批量改密任务执行后，存放执行成功的 <username, asset> 对应关系
    """
    asset = models.ForeignKey(
        'assets.Asset', on_delete=models.CASCADE, verbose_name=_('Asset')
    )
