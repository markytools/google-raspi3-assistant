#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from multiprocess.managers import BaseManager
from linphonebase import LinphoneBase

class MyManager(BaseManager):
    pass

MyManager.register('LinphoneBase', LinphoneBase)

manager = MyManager()
manager.start()
linphoneBase = manager.LinphoneBase()
