#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Quantum Calculator
# Author: Hideto Manjo
# Licence: Apache License 2.0

from wx import App
from interface import Calculator, Menu, TextPanel
        
##########################################################################

if __name__ == '__main__':

    application = App()
    frame = Calculator()
    frame.Show()
    application.MainLoop()


