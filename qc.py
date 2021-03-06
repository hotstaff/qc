#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Quantum Calculator
Author: Hideto Manjo
Licence: Apache License 2.0
'''

from wx import App
from interface import Calculator

if __name__ == '__main__':

    APPLICATION = App()
    FRAME = Calculator()
    FRAME.Show()
    APPLICATION.MainLoop()
