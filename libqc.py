#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Quantum Calculator - libqc
# Author: Hideto Manjo
# Licence: Apache License 2.0

import sys
import re
from datetime import datetime

from qiskit import QuantumProgram, QISKitError, RegisterSizeError
# from IBMQuantumExperience import IBMQuantumExperience


class QC():
    def __init__(self, backend='local_qasm_simulator', remote=False, qubits=3):
        self.phase = [
            ['0', 'initialized.']
            ]

        # config
        self.backend = backend
        self.remote = remote
        self.qubits = qubits

        # circuits variable
        self.shots = 2

        # async
        self.wait = False
        self.last = ['init', 'None']

        self.load()

    def load(self, api_info=True):
        # Create a QuantumProgram object instance.
        self.qp = QuantumProgram()
        if(self.remote):
            try:
                import Qconfig
                self.qp.set_api(Qconfig.APItoken, Qconfig.config["url"],
                                hub=Qconfig.config["hub"],
                                group=Qconfig.config["group"],
                                project=Qconfig.config["project"])

            except Exception as ex:
                msg = 'Error in loading Qconfig.py!. Error = {}\n'.format(ex)
                sys.stdout.write(msg)
                sys.stdout.flush()
                return False

            if(api_info is True):
                api = self.qp.get_api()
                sys.stdout.write('<IBM Quantum Experience API information>\n')
                sys.stdout.flush()
                sys.stdout.write('Version: {0}\n'.format(api.api_version()))
                sys.stdout.write('User jobs (last 5):\n')
                jobs = api.get_jobs(limit=500)

                def formatDate(x):
                    return datetime.strptime(x['creationDate'],
                                             '%Y-%m-%dT%H:%M:%S.%fZ')
                sortedjobs = sorted(jobs,
                                    key=formatDate)
                sys.stdout.write('  {0:<32} {1:<24} {2:<9} {3}\n'
                                 .format('id',
                                         'creationDate',
                                         'status',
                                         'backend'))
                sys.stdout.write('{:-^94}\n'.format(""))
                for job in sortedjobs[-5:]:
                    sys.stdout.write('  {0:<32} {1:<24} {2:<9} {3}\n'
                                     .format(job['id'],
                                             job['creationDate'],
                                             job['status'],
                                             job['backend']['name']))
                sys.stdout.write('There are {0} jobs on the server\n'
                                 .format(len(jobs)))
                sys.stdout.write('Credits: {0}\n'
                                 .format(api.get_my_credits()))
                sys.stdout.flush()

        self.backends = self.qp.available_backends()
        status = self.qp.get_backend_status(self.backend)

        if ('available' in status):
            if (status['available'] is False):
                return False
        return True

    def setConfig(self, config={}):
        if('backend' in config):
            self.backend = str(config['backend'])
            if ('local_' in self.backend):
                self.remote = False
            else:
                self.remote = True

        if('remote' in config):
            self.remote = config['remote']

        if('qubits' in config):
            self.qubits = int(config['qubits'])

        return True

    def _progress(self, phasename, text):
        self.phase.append([str(phasename), str(text)])
        text = "Phase {0}: {1}".format(phasename, text)
        sys.stdout.write("{}\n".format(text))
        sys.stdout.flush()

    def _initCircuit(self):
        self._progress('1', 'Initialize quantum registers and circuit')
        qubits = self.qubits

        quantum_registers = [
            {"name": "cin", "size": 1},
            {"name": "qa", "size": qubits},
            {"name": "qb", "size": qubits},
            {"name": "cout", "size": 1}
            ]

        classical_registers = [
            {"name": "ans", "size": qubits + 1}
            ]

        if('cin' in self.qp.get_quantum_register_names()):
            self.qp.destroy_quantum_registers(quantum_registers)
            self.qp.destroy_classical_registers(classical_registers)

        qr = self.qp.create_quantum_registers(quantum_registers)
        cr = self.qp.create_classical_registers(classical_registers)

        self.qp.create_circuit("qcirc", qr, cr)

    def _create_circuit_qadd(self):
        if ('add' in self.qp.get_circuit_names()):
            return True

        # quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
        def majority(circuit, a, b, c):
            circuit.cx(c, b)
            circuit.cx(c, a)
            circuit.ccx(a, b, c)

        def unmaj(circuit, a, b, c):
            circuit.ccx(a, b, c)
            circuit.cx(c, a)
            circuit.cx(a, b)

        def adder(circuit, cin, qa, qb, cout, qubits):
            majority(circuit, cin[0], qb[0], qa[0])
            for i in range(qubits - 1):
                majority(circuit, qa[i], qb[i + 1], qa[i + 1])

            circuit.cx(qa[qubits - 1], cout[0])

            for i in range(qubits - 1)[::-1]:
                unmaj(circuit, qa[i], qb[i + 1], qa[i + 1])
            unmaj(circuit, cin[0], qb[0], qa[0])

        qubits = self.qubits

        [cin, qa, qb, cout] = map(self.qp.get_quantum_register,
                                  ["cin", "qa", "qb", "cout"])
        ans = self.qp.get_classical_register('ans')

        # adder circuit
        qadder = self.qp.create_circuit("qadd", [cin, qa, qb, cout], [ans])
        adder(qadder, cin, qa, qb, cout, qubits)

    def _create_cicuit_qsub(self):
        if ('qsub' in self.qp.get_circuit_names()):
            return True
        if ('qadd' not in self.qp.get_circuit_names()):
            self._create_circuit_qadd()

        # subtractor circuit
        self.qp.add_circuit('qsub', self.qp.get_circuit('qadd'))
        qsubtractor = self.qp.get_circuit('qsub')
        qsubtractor.reverse()

    def _qadd(self, a, b=None, subtract=False, observe=False):

        def measure(circuit, qb, cout, ans, qubits):
            circuit.barrier()
            for i in range(qubits):
                circuit.measure(qb[i], ans[i])
            circuit.measure(cout[0], ans[qubits])

        def char2q(circuit, cbit, qbit):
            if(cbit == '1'):
                circuit.x(qbit)
            elif(cbit == 'H'):
                circuit.h(qbit)
                self.shots = 5 * (2**self.qubits)

        def inputState(circuit, a, b=None):
            # reverse bit order
            a = a[::-1]
            for i in range(self.qubits):
                char2q(circuit, a[i], qa[i])

            if b is not None:
                b = b[::-1]
                for i in range(self.qubits):
                    char2q(circuit, b[i], qb[i])

        def resetInput(circuit, cin, qa, cout, qubits):
            circuit.reset(cin)
            circuit.reset(cout)
            for i in range(qubits):
                circuit.reset(qa[i])

        qubits = self.qubits
        # get register
        [cin, qa, qb, cout] = map(self.qp.get_quantum_register,
                                  ["cin", "qa", "qb", "cout"])
        ans = self.qp.get_classical_register('ans')

        qcirc = self.qp.get_circuit('qcirc')

        self._progress('2', 'Define input state ({})'
                            .format(('QADD' if subtract is False else 'QSUB')))
        if(b is not None):
            if(subtract is True):
                # subtract
                inputState(qcirc, b, a)
            else:
                # add
                inputState(qcirc, a, b)
        else:
            resetInput(qcirc, cin, qa, cout, qubits)
            inputState(qcirc, a)

        self._progress('3', 'Define quantum circuit ({})'
                            .format(('QADD' if subtract is False else 'QSUB')))
        if(subtract is True):
            self._create_cicuit_qsub()
            qcirc.extend(self.qp.get_circuit('qsub'))
        else:
            self._create_circuit_qadd()
            qcirc.extend(self.qp.get_circuit('qadd'))

        if (observe is True):
            measure(qcirc, qb, cout, ans, qubits)

    def _qsub(self, a, b=None, observe=False):
        self._qadd(a, b, subtract=True, observe=observe)

    def _qope(self, a, operator, b=None, observe=False):
        if(operator == '+'):
            return self._qadd(a, b, observe=observe)
        elif(operator == '-'):
            return self._qsub(a, b, observe=observe)

    def _compile(self, name, cross_backend=None, print_qasm=False):
        self._progress('4', 'Compile quantum circuit')

        coupling_map = None
        if (cross_backend is not None):
            backend_conf = self.qp.get_backend_configuration(cross_backend)
            coupling_map = backend_conf.get('coupling_map', None)
            if(coupling_map is None):
                sys.stdout.write('backend: {} coupling_map not found'
                                 .format(cross_backend))

        qobj = self.qp.compile([name],
                               backend=self.backend,
                               shots=self.shots,
                               seed=1,
                               coupling_map=coupling_map)

        if(print_qasm is True):
            sys.stdout.write(self.qp.get_compiled_qasm(qobj, 'qcirc'))
            sys.stdout.flush()
        return qobj

    def _run(self, qobj):
        self._progress('5', 'Run quantum circuit (wait for answer)')
        result = self.qp.run(qobj, wait=5, timeout=100000)
        return result

    def _run_async(self, qobj):
        self._progress('5', 'Run quantum circuit')
        self.wait = True

        def async_result(result):
            self.wait = False
            self.last = self.resultParse(result)
        self.qp.run_async(qobj, wait=5, timeout=100000, callback=async_result)

    def _isRegularNumber(self, numstring, base):
        # return qbit string
        if (base == 'bin'):
            binstring = numstring
        elif (base == 'dec'):
            if (numstring == 'H'):
                binstring = 'H'*self.qubits
            else:
                binstring = format(int(numstring), "0{}b".format(self.qubits))

        if (len(binstring) != self.qubits):
            return None

        return binstring

    def getSeq(self, text, base='dec'):
        # convert seq and check it
        # if text is invalid, return the list of length 0.
        operators = u'(\+|\-)'
        seq = re.split(operators, text)

        # length check
        if (len(seq) % 2 == 0 or len(seq) == 1):
            return []

        # regex
        if (base == 'bin'):
            regex = re.compile(r'[01H]+')
        else:
            regex = re.compile(r'(^(?!.H)[0-9]+|H)')

        for i in range(0, len(seq), 2):
            match = regex.match(seq[i])
            if (match is None):
                return []
            num = match.group(0)
            seq[i] = self._isRegularNumber(num, base)

            if (seq[i] is None):
                return []

        return seq

    def resultParse(self, result):
        data = result.get_data("qcirc")
        sys.stdout.write("job id: {0}\n".format(result.get_job_id()))
        sys.stdout.write("raw result: {0}\n".format(data))
        sys.stdout.write("{:=^40}\n".format("answer"))

        counts = data['counts']
        sortedcounts = sorted(counts.items(),
                              key=lambda x: -x[1])

        sortedans = []
        for count in sortedcounts:
            if (count[0][0] == '1'):
                ans = 'OR'
            else:
                ans = str(int(count[0][-self.qubits:], 2))
            sortedans.append(ans)
            sys.stdout.write('Dec: {0:>2} Bin: {1} Count: {2} \n'
                             .format(ans, str(count[0]), str(count[1])))

        sys.stdout.write('{0:d} answer{1}\n'
                         .format(len(sortedans),
                                 '' if len(sortedans) == 1 else 's'))
        sys.stdout.write("{:=^40}\n".format(""))
        if('time' in data):
            sys.stdout.write("time: {0:<3} sec\n".format(data['time']))
        sys.stdout.write("All process done.\n")
        sys.stdout.flush()

        uniqanswer = sorted(set(sortedans), key=sortedans.index)

        ans = ",".join(uniqanswer)
        return [str(result), ans]

    def execCalc(self, text, base='dec', wait_result=False):
        # get sequence from calctext
        seq = self.getSeq(text, base)
        print('QC seq:', seq)
        if(seq == []):
            return ["Syntax error", None]

        # Fail flag
        fail = False
        sys.stdout.write("{:=^40}\n".format("start"))
        sys.stdout.flush()

        try:
            self._initCircuit()
            operators = seq[1::2]  # slice odd index
            numbers = seq[0::2]    # slice even index
            i = 1
            observe = False
            for oper in operators:
                if (i == len(numbers)-1):
                    observe = True
                if (i == 1):
                    self._qope(numbers[0], oper, numbers[1], observe=observe)
                else:
                    self._qope(numbers[i], oper, observe=observe)
                i = i + 1

            qobj = self._compile('qcirc')

            if(wait_result is True):
                [status, ans] = self.resultParse(self._run(qobj))
            else:
                self._run_async(qobj)
                [status, ans] = [
                    'Wait. Calculating on {0}'.format(self.backend),
                    '...'
                ]

        except QISKitError as ex:
            msg = 'There was an error in the circuit!. Error = {}\n'.format(ex)
            fail = True
        except RegisterSizeError as ex:
            msg = 'Error in the number of registers!. Error = {}\n'.format(ex)
            fail = True
        finally:
            sys.stdout.write("{:=^40}\n".format("end"))
            sys.stdout.flush()

        if(fail):
            sys.stdout.write(msg)
            sys.stdout.flush()
            return ["FAIL", None]

        return [status, ans]
