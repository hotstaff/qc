#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Quantum Calculator User Interface Module
Author: Hideto Manjo
Licence: Apache License 2.0
'''

import sys
import time
import threading
import os
import configparser
import wx

from libqc import QC

VERSION_TEXT = '0.0.2'
CONFIG_FILENAME = './default.conf'

# default configure load
CONF = configparser.ConfigParser()
if os.path.isfile(CONFIG_FILENAME) is False:
    sys.stdout.write('{0} not found -> init\n'.format(CONFIG_FILENAME))
    CONF['DEFAULT'] = {
        'backend': 'local_qasm_simulator',
        'remote': 'no',
        'qubits': '3',
        'qubits_max': '8',
        'qubits_min': '1'
        }
    with open(CONFIG_FILENAME, 'w') as fp:
        CONF.write(fp)
CONF.read(CONFIG_FILENAME)


class Calculator(wx.Frame):
    '''
    Calculator Frame
    '''
    # pylint: disable=too-many-ancestors

    def __init__(self):
        super(Calculator, self).__init__(None,
                                         wx.ID_ANY,
                                         'Quantum Calculator',
                                         size=(320, 270),
                                         style=(wx.DEFAULT_FRAME_STYLE ^
                                                wx.RESIZE_BORDER ^
                                                wx.MAXIMIZE_BOX))

        self.__qc = QC(backend=CONF['DEFAULT'].get('backend',
                                                   'local_qasm_simulator'),
                       remote=CONF['DEFAULT'].getboolean('remote'),
                       qubits=CONF['DEFAULT'].getint('qubits', 3))

        # flags
        self.busy = False
        self.init = True

        # variables
        self.base = 'dec'

        # status bar
        self.CreateStatusBar()
        self.GetStatusBar().SetBackgroundColour(None)
        self.SetStatusText('QC Ready.')

        # menu bar
        self.menu = Menu(self)
        self.SetMenuBar(self.menu)

        # panel class
        root_panel = wx.Panel(self, wx.ID_ANY)
        self.text_panel = TextPanel(root_panel)
        self.calcbutton_panel = CalcButtonPanel(root_panel)

        root_layout = wx.BoxSizer(wx.VERTICAL)
        root_layout.Add(self.text_panel, 0, wx.GROW | wx.ALL, border=10)
        root_layout.Add(self.calcbutton_panel, 0, wx.GROW | wx.ALL, border=10)
        root_panel.SetSizer(root_layout)
        root_layout.Fit(root_panel)

        self.Bind(wx.EVT_MENU, self.select_menu)

    # BIND FUNCTION
    def select_menu(self, event):
        '''
        select_menu
        '''
        menuid = event.GetId()
        if menuid == 1:
            self.Close(True)
        elif menuid >= 2000 and menuid < 3000:
            self.set_backend(self.menu.id2backend[menuid])
        elif menuid > 4000 and menuid < 5000:
            qubits = int(menuid - 4000)
            self.__qc.set_config({'qubits': qubits})
            self.SetStatusText('Set Qubit -> {0} (0-{1}),'
                               ' circuit requires {2} qubits at least.'
                               .format(qubits, 2**qubits - 1, qubits * 2 + 2))
            self.calcbutton_panel.check_calctext()
        elif menuid == 29:
            self.SetStatusText('Loading remote backend')
            self.menu.reload_backend_menu(remote=True)
            self.SetStatusText('Updated')
        elif menuid == 31:
            self.change_base('dec')
        elif menuid == 32:
            self.change_base('bin')
        elif menuid == 9:
            box = wx.MessageDialog(None,
                                   'Quantum Calculator v{}\n\n'
                                   'https://github.com/hotstaff/qc\n'
                                   'Apache Licence 2.0\n'
                                   '© 2017 Hideto Manjo'
                                   .format(VERSION_TEXT),
                                   'About Quantum Calculator',
                                   wx.OK | wx.ICON_NONE | wx.STAY_ON_TOP)
            box.ShowModal()
            box.Destroy()
    # BIND FUNCTION END
    def get_qc(self):
        '''
        return quantum calcurator
        '''
        return self.__qc

    def set_backend(self, backend):
        '''
        set_backend
        '''
        self.SetStatusText('Loading {}...'.format(backend))
        self.__qc.set_config({'backend': backend})
        if self.__qc.load():
            self.SetStatusText('Ready to use {}'.format(backend))
        else:
            self.SetStatusText('{} is busy'.format(backend))

    def change_base(self, base='dec'):
        '''
        change_base
        '''
        self.text_panel.calc_text.Clear()
        self.base = base
        self.change_button_visible()
        self.SetStatusText('Set input mode to {}'
                           .format('Binary' if base == 'bin' else 'Decimal'))

    def change_button_visible(self):
        '''
        change button visible
        '''
        if self.base == 'bin':
            self.calcbutton_panel.button['0'].Enable()
            self.calcbutton_panel.button['1'].Enable()
            for i in range(2, 10):
                self.calcbutton_panel.button[str(i)].Disable()
        else:
            for i in range(0, 10):
                self.calcbutton_panel.button[str(i)].Enable()


class Menu(wx.MenuBar):
    '''
    Menu
    '''
    # pylint: disable=too-few-public-methods

    def __init__(self, frame):

        super(Menu, self).__init__(wx.ID_ANY)

        self.frame = frame
        self.__qc = self.frame.get_qc()

        menu_view = wx.Menu()
        menu_view.AppendRadioItem(31, 'Decimal')
        menu_view.AppendRadioItem(32, 'Binary')

        self.menu_backend = wx.Menu()
        self.id2backend = {}
        self.reload_backend_menu()
        self.menu_backend.AppendSeparator()
        self.menu_backend.Append(29, 'Import Qconfig.py')

        menu_circuit = wx.Menu()
        qubits_max = CONF['DEFAULT'].getint('qubits_max', 8)
        qubits_min = CONF['DEFAULT'].getint('qubits_min', 1)
        for i in range(qubits_min, qubits_max + 1):
            menu_circuit.AppendRadioItem(4000 + i, str(i))

        menu_circuit.Check(4000 + int(self.__qc.qubits), True)

        menu_help = wx.Menu()
        menu_help.Append(9, 'About')

        self.Append(menu_view, 'Input')
        self.Append(menu_circuit, 'Qubit')
        self.Append(self.menu_backend, 'Backend')
        self.Append(menu_help, 'Help')

    def reload_backend_menu(self, remote=False):
        '''
        reload backend menu
        '''
        for ident in self.id2backend:
            self.menu_backend.Delete(ident)

        if remote is True:
            self.__qc.set_config({'remote': True})
            self.__qc.load()
        backends = self.__qc.backends

        disable_backends = [
            'local_unitary_simulator',
            'local_clifford_simulator',
            'ibmqx4'
            ]

        # disable
        for backend in backends[:]:
            for disable_backend in disable_backends:
                if backend == disable_backend:
                    backends.pop(backends.index(backend))
                    disable_backends.pop(disable_backends.index(backend))

        for i, backend in enumerate(backends):
            menuid = 2000 + i

            if 'local' in backend:
                menutitle = 'Local ({})'.format(backend)
            elif 'ibmqx' in backend:
                if 'simulator' in backend:
                    menutitle = 'IBM Q - Simulator ({})'.format(backend)
                else:
                    menutitle = 'IBM Q - Real device ({})'.format(backend)
            else:
                menutitle = 'Remote ({})'.format(backend)
            self.menu_backend.InsertRadioItem(i, menuid, menutitle)

            if backend == self.__qc.backend:
                self.menu_backend.Check(menuid, True)

            self.id2backend[2000 + i] = backend
            i = i + 1


class TextPanel(wx.Panel):
    '''
    TextPanel
    '''
    # pylint: disable=too-few-public-methods

    def __init__(self, parent):
        super(TextPanel, self).__init__(parent, wx.ID_ANY)
        self.calc_text = wx.TextCtrl(self,
                                     wx.ID_ANY,
                                     style=wx.TE_RIGHT | wx.TE_READONLY)

        font = wx.Font(20,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL)
        self.calc_text.SetFont(font)
        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(self.calc_text, 1)
        self.SetSizer(layout)


class CalcButtonPanel(wx.Panel):
    '''
    CalcButtonPanel
    '''

    def __init__(self, parent):
        super(CalcButtonPanel, self).__init__(parent, wx.ID_ANY)

        # frame property
        self.frame = parent.GetParent()
        self.__qc = self.frame.get_qc()
        self.calc_text = self.frame.text_panel.calc_text

        # (label, buttonid, display)
        button_collection = [
            ('7', 107, '7'),
            ('8', 108, '8'),
            ('9', 109, '9'),
            ('CE', 200, ''),
            ('4', 104, '4'),
            ('5', 105, '5'),
            ('6', 106, '6'),
            ('-', 201, '-'),
            ('1', 101, '1'),
            ('2', 102, '2'),
            ('3', 103, '3'),
            ('+', 202, '+'),
            ('0', 100, '0'),
            ('B', 401, ''),
            ('H', 300, 'H'),
            ('=', 203, '=')
            ]

        # buttons
        self.button = {}
        self.buttonid2label = {}
        for (label, buttonid, display) in button_collection:
            if buttonid == 401:
                self.button[label] = wx.Button(self,
                                               buttonid,
                                               '',
                                               size=(30, 30))
                continue
            self.button[label] = wx.Button(self,
                                           buttonid,
                                           label,
                                           size=(30, 30))
            self.buttonid2label[str(buttonid)] = (label, display)

        # button layout
        layout = wx.GridSizer(4, 4, 3, 3)
        for (label, buttonid, display) in button_collection:
            layout.Add(self.button[label], 1, wx.GROW)
        self.SetSizer(layout)

        # 8, 9, B buttons are disabled
        self.button['B'].Disable()

        # bind button event
        for i in range(10):
            self.Bind(wx.EVT_BUTTON,
                      self._click_num_button,
                      self.button[str(i)])

        self.Bind(wx.EVT_BUTTON, self._click_num_button, self.button['H'])

        self.Bind(wx.EVT_BUTTON, self._click_ce_button, self.button['CE'])
        self.Bind(wx.EVT_BUTTON, self._click_ope_button, self.button['+'])
        self.Bind(wx.EVT_BUTTON, self._click_ope_button, self.button['-'])
        self.Bind(wx.EVT_BUTTON, self._click_e_button, self.button['='])

    @staticmethod
    def show_alart(title, text):
        '''
        show_alart
        '''
        width = 128
        if len(text) > width:
            split_text = [text[i: i+width] for i in range(0, len(text), width)]
            text = "\n".join(split_text)
        dialog = wx.MessageDialog(None, text, title, style=wx.ICON_NONE)
        dialog.ShowModal()
        dialog.Destroy()

    # BIND FUNCTIONS
    def _click_num_button(self, event):
        if self.frame.busy:
            return False
        if self.frame.init:
            self.calc_text.Clear()
            self.frame.init = False
        display = self.buttonid2label[str(event.GetId())][1]
        self.calc_text.AppendText(display)
        self.check_calctext()
        return True

    def _click_ope_button(self, event):
        self._click_num_button(event)

    def _click_ce_button(self, _event):
        if self.frame.busy:
            return False
        self.button['='].Disable()
        self.calc_text.Clear()
        self.frame.SetStatusText('Clear')
        return True

    def _click_e_button(self, _event):
        if self.frame.busy is False and self.frame.init is False:
            self._calc()
    # BIND FUNCTIONS END

    def check_calctext(self):
        '''
        check calctext
        '''
        calc_string = str(self.calc_text.GetValue())
        self.button['='].Disable()
        if self.frame.busy is False:
            seq = self.__qc.get_seq(calc_string, self.frame.base)
            if seq:
                self.button['='].Enable()

    def _calc(self):
        # disable user input
        self.frame.busy = True
        self.button['='].Disable()

        # exec and draw job status
        qc_result = self.__qc.exec_calc(str(self.calc_text.GetValue()),
                                        self.frame.base)
        self._draw(qc_result)

        # init flag reset
        self.frame.init = True

        # wait for result of qc
        wait_th = threading.Thread(name='wait_th', target=self._wait_anser)
        wait_th.start()

    def _draw(self, qc_result):
        '''
        thread
            GUI functions require that are called on main thread,
            so use wx.CallAfter as caller function.
        '''
        [status, ans] = qc_result
        wx.CallAfter(self.frame.SetStatusText, str(status))
        if ans is not None and len(ans) > 15:
            wx.CallAfter(self.show_alart, 'Anser', str(ans))
        wx.CallAfter(self.calc_text.SetValue, str(ans))

    def _wait_anser(self):
        while True:
            time.sleep(0.5)
            wx.CallAfter(self.frame.SetStatusText,
                         'Phase {0} {1}'
                         .format(self.__qc.phase[-1][0], self.__qc.phase[-1][1]))
            if self.__qc.wait is False:
                self._draw(self.__qc.last)
                wx.CallAfter(self.button['='].Enable)
                self.frame.busy = False
                break
