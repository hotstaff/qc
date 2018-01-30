#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Quantum Calculator
# Author: Hideto Manjo
# Licence: Apache License 2.0

import wx
import sys

from qiskit import QuantumProgram, QISKitError, RegisterSizeError
import Qconfig

version_text = '0.0.1'

class Calculator(wx.Frame):

    def __init__(self):

        super(Calculator, self).__init__(None, wx.ID_ANY, 'Quantum Calculator', size=(320, 270), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)

        # status bar
        self.CreateStatusBar()
        self.SetStatusText('QC')
        self.GetStatusBar().SetBackgroundColour(None)

        self.SetMenuBar(Menu())

        root_panel = wx.Panel(self, wx.ID_ANY)

        self.text_panel = TextPanel(root_panel)
        calcbutton_panel = CalcButtonPanel(root_panel)

        root_layout = wx.BoxSizer(wx.VERTICAL)
        root_layout.Add(self.text_panel, 0, wx.GROW | wx.ALL, border=10)
        root_layout.Add(calcbutton_panel, 0, wx.GROW| wx.ALL, border=10)
        root_panel.SetSizer(root_layout)
        root_layout.Fit(root_panel)

        def selectMenu(event):
            menuid = event.GetId() 
            # Close
            if (menuid == 1):
                self.Close(True)
            elif(menuid == 21):
                qc.backend = 'local_qasm_simulator'
                qc.remote = False
                qc.load()
            elif(menuid == 22):
                qc.backend = 'ibmqx_qasm_simulator'
                qc.remote = True
                qc.load()
            elif(menuid == 23):
                qc.backend = 'ibmqx_hpc_qasm_simulator'
                qc.remote = True
                qc.load()
            elif(menuid == 9):
                box = wx.MessageDialog(None, 'Quantum Calculator v' + version_text + '\n\nhttps://github.com/hotstaff/qc\nApache Licence 2.0\n© 2017 Hideto Manjo','About Quantum Calculator',wx.OK | wx.ICON_NONE | wx.STAY_ON_TOP)
                box.ShowModal()
                box.Destroy()

        self.Bind(wx.EVT_MENU,selectMenu)

class Menu(wx.MenuBar):

    def __init__(self):

        super(Menu, self).__init__()
          
        menu_file = wx.Menu()
        menu_file.Append(1, 'Quit')

        menu_setting = wx.Menu()
        menu_setting.AppendRadioItem(21,'Local (local_qasm_simulator)')
        menu_setting.AppendRadioItem(22,'IBM Q (ibmqx_qasm_simulator)')
        menu_setting.AppendRadioItem(23,'IBM Q (ibmqx_hpc_qasm_simulator)')
        

        menu_help = wx.Menu()
        menu_help.Append(9,'About')
              
        self.Append(menu_file, 'File')
        self.Append(menu_setting, 'Backend')
        self.Append(menu_help, 'Help')

class TextPanel(wx.Panel):

    def __init__(self, parent):
        super(TextPanel, self).__init__(parent, wx.ID_ANY)
          
        self.calc_text = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_RIGHT | wx.TE_READONLY )
        font = wx.Font(20, wx.FONTFAMILY_DEFAULT, 
               wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.calc_text.SetFont(font)
        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(self.calc_text, 1)
        self.SetSizer(layout)

  
class CalcButtonPanel(wx.Panel):

    def __init__(self, parent):
        super(CalcButtonPanel, self).__init__(parent, wx.ID_ANY)

        frame = parent.GetParent()
        self.calc_text = frame.text_panel.calc_text
        self.seq = []
        self.busy = False

        # (label, buttonid, display)
        button_collection = [ ('7', 107, '7'),
                              ('8', 108, '8'),
                              ('9', 109, '9'),
                              ('CE',200, ''),
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
                              ('H', 300, '(0~7)'),
                              ('=', 203, '=')
                                ]
        
        # buttons
        self.button = {}
        self.buttonid2label={}
        for (label, buttonid, display) in button_collection:
            if (buttonid==401):
                self.button[label] = wx.Button(self, buttonid, '', size=(30,30))
                continue
            self.button[label] = wx.Button(self, buttonid, label, size=(30,30))
            self.buttonid2label[str(buttonid)] = (label, display)

        # button layout
        layout = wx.GridSizer(4, 4, 3, 3)
        for (label, buttonid, display) in button_collection:
            layout.Add(self.button[label], 1, wx.GROW)
        self.SetSizer(layout)

        # 8, 9, B buttons are disabled 
        self.button['-'].Disable()
        self.button['B'].Disable()
        self.button['8'].Disable()
        self.button['9'].Disable()

        def disable_num_button():
            for i in range(8):
                self.button[str(i)].Disable()
            self.button['H'].Disable()

        def enable_num_button():
            for i in range(8):
                self.button[str(i)].Enable()
            self.button['H'].Enable()

        def disable_ope_button():
            self.button['+'].Disable()
            # self.button['-'].Disable()
            
        def enable_ope_button():
            self.button['+'].Enable()
            # self.button['-'].Enable()

        def resetSeq():
            self.seq=[]

        def addSeq(buttonid):
            (label, display) = self.buttonid2label[str(buttonid)]
            self.seq.append(label)
            print(self.seq)
            return (label, display)

        def init_button():
            self.button['='].Enable()
            enable_num_button()
            enable_ope_button()

        def change_button():
            if(len(self.seq) % 2 == 0):
                enable_num_button()
                disable_ope_button()         
            elif(len(self.seq) % 2 == 1):
                enable_ope_button()
                disable_num_button()

            if(len(self.seq) == 3):
                disable_num_button()
                disable_ope_button()
                self.button['='].Enable()

        def newCalc():
            self.busy = True
            [a, ope, b] = self.seq[0:3]
            ans = qc.execCalc(a, ope, b)
            self.busy = False
            return ans

        # button click bind functions
        def click_num_button(event):
            if(len(self.seq)==0):
                self.calc_text.Clear()
            (label, display) = addSeq(event.GetId())
            self.calc_text.AppendText(display)
            change_button()

        def click_CE_button(event):
            self.calc_text.Clear()
            resetSeq()
            init_button()
            frame.SetStatusText('Clear')    

        def click_OPE_button(event):
            if( len(self.seq) != 0):
                (label, display) = addSeq(event.GetId())
                self.calc_text.AppendText(display)
                change_button()
            
        def click_E_button(event):
            if( len(self.seq) == 3 and self.busy==False):
                self.button['='].Disable()
                frame.SetStatusText('Wait. Calculating on ' + qc.backend)
                ans = newCalc()
                self.calc_text.SetValue(str(ans))
                resetSeq()
                init_button()

        # bind button event
        for i in range(8):
            self.button[str(i)].Bind(wx.EVT_BUTTON, click_num_button)
        self.button['H'].Bind(wx.EVT_BUTTON, click_num_button)

        self.button['CE'].Bind(wx.EVT_BUTTON, click_CE_button)
        self.button['+'].Bind(wx.EVT_BUTTON, click_OPE_button)
        # self.button['-'].Bind(wx.EVT_BUTTON, click_OPE_button)
        self.button['='].Bind(wx.EVT_BUTTON, click_E_button)
        
#########################################################################

class QC():
    def __init__(self):
        self.phase=[
                ['0','initialized.']
                ]

        self.backend = 'local_qasm_simulator'
        self.remote = False

        self.load()

    def load(self):
        frame.SetStatusText('Loading ' + self.backend + '...')
        # Create a QuantumProgram object instance.
        self.qp = QuantumProgram()
        if(self.remote):
            self.qp.set_api(Qconfig.APItoken, Qconfig.config["url"], verify=False,
                        hub=Qconfig.config["hub"],
                        group=Qconfig.config["group"],
                        project=Qconfig.config["project"])
        self.backends = self.qp.available_backends()
        frame.SetStatusText('Ready to use ' + self.backend)

    def _progress(self, phasename, text):
        self.phase.append([str(phasename), str(text)])
        text = "Phase " + str(phasename) + ": " + str(text)
        sys.stdout.write( text+ "\n")
        frame.SetStatusText(text)
        sys.stdout.flush()

    def _qadd(self, a, b):
        self._progress('1', 'Initialize quantum registers and circuit')
        # Define Registers
        q = self.qp.create_quantum_register("q", 10)
        c = self.qp.create_classical_register("c", 10)
        # Define the circuit
        qadd = self.qp.create_circuit("qadd", [q], [c])

        self._progress('2', 'Define input state')
        shots=2
        # Define Input registers
        if (a == 'H'):
            bina = 'HHH'
            shots = 128
        else:
            bina = format(int(a), "03b")
        if (b == 'H'):
            binb = 'HHH'
            shots = 128
        else:
            binb = format(int(b), "03b")
        qinput = (bina[::-1] + binb[::-1])

        i = 0
        for bit in qinput:
            if( bit =='1'):
                qadd.x(q[i])
                sys.stdout.write( "quantum resister " + str(i) + " -> add NOT gate\n" )
            elif(bit == 'H'):
                qadd.h(q[i])
                sys.stdout.write( "quantum resister " + str(i) + " -> add Hadamard gate\n" )
            i = i + 1    
        sys.stdout.flush()

        self._progress( '3', 'Define quantum circuit')
        # Define quantum circuit
        qadd.ccx(q[0],q[3],q[7])
        qadd.cx(q[0],q[3])
        qadd.ccx(q[6],q[3],q[7])
        qadd.ccx(q[1],q[4],q[8])
        qadd.cx(q[1],q[4])
        qadd.ccx(q[7],q[4],q[8])
        qadd.ccx(q[2],q[5],q[9])
        qadd.cx(q[2],q[5])
        qadd.ccx(q[8],q[5],q[9])
        qadd.cx(q[2],q[5])
        qadd.cx(q[2],q[5])
        qadd.cx(q[8],q[5])
        qadd.ccx(q[7],q[4],q[8])
        qadd.cx(q[1],q[4])
        qadd.ccx(q[1],q[4],q[8])
        qadd.cx(q[1],q[4])
        qadd.cx(q[7],q[4])
        qadd.ccx(q[6],q[3],q[7])
        qadd.cx(q[0],q[3])
        qadd.ccx(q[0],q[3],q[7])
        qadd.cx(q[0],q[3])
        qadd.cx(q[6],q[3])

        qadd.measure(q[3], c[0])
        qadd.measure(q[4], c[1])
        qadd.measure(q[5], c[2])
        qadd.measure(q[9], c[9])

        self._progress( '4', 'Execute quantum circuit')
        # Execute the circuit
        result = self.qp.execute(["qadd"], backend=self.backend, shots=shots, seed=1, timeout=300)

        self._progress( '5', 'Return result')
        return result

    def _showAlart(self, title, text, style=wx.OK):
        dialog = wx.MessageDialog(None, text, title, style=wx.OK)
        dialog.ShowModal()
        dialog.Destroy()

    def execCalc(self, a, ope, b):

        # Fail flag
        fail = False

        sys.stdout.write( "===========start===========\n")
        sys.stdout.flush()    

        try:
            # calculation
            result = self._qadd(a, b)

        except QISKitError as ex:
            msg = 'There was an error in the circuit!. Error = {}\n'.format(ex)
            fail = True
        except RegisterSizeError as ex:
            msg = 'Error in the number of registers!. Error = {}\n'.format(ex)
            fail = True
        finally:
            sys.stdout.write( "============end===========\n")
            sys.stdout.flush()    


        if(fail):
            self._showAlart('Error', msg, wx.ICON_EXCLAMATION )
            sys.stdout.write(msg)
            sys.stdout.flush()
            return None

        # Show the results status.
        frame.SetStatusText(str(result))

        data = result.get_data("qadd")
        print(data)
        counts = data['counts']
        sortedcounts = sorted(counts.items(), key=lambda x:-x[1])
        sortedans = []
        for count in sortedcounts:
            if(count[0][0] == '1' ):
                print( 'ans: OR', 'bin:' , count[0], 'counts:', count[1])
                sortedans.append('OR')
            else:
                print( 'ans: ', str(int(count[0][-3:], 2)), 'bin:' , count[0], 'counts:', count[1])
                sortedans.append(str(int(count[0][-3:], 2)))

        return ','.join(sorted(set(sortedans), key=sortedans.index))

##########################################################################

if __name__ == '__main__':

    application = wx.App()
    frame = Calculator()
    frame.Show()
    qc = QC()
    application.MainLoop()
