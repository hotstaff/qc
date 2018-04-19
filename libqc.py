#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Quantum Calculator - libqc
Author: Hideto Manjo
Licence: Apache License 2.0
'''

import sys
import re
from datetime import datetime

from qiskit import QuantumProgram, QISKitError, RegisterSizeError


class QC():
    '''
    class QC
    '''
    # pylint: disable=too-many-instance-attributes
    def __init__(self, backend='local_qasm_simulator', remote=False, qubits=3):
        # private member
        # __qp
        self.__qp = None

        # calc phase
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
        '''
        load
        '''
        self.__qp = QuantumProgram()
        if self.remote:
            try:
                import Qconfig
                self.__qp.set_api(Qconfig.APItoken, Qconfig.config["url"],
                                  hub=Qconfig.config["hub"],
                                  group=Qconfig.config["group"],
                                  project=Qconfig.config["project"])

            except ImportError as ex:
                msg = 'Error in loading Qconfig.py!. Error = {}\n'.format(ex)
                sys.stdout.write(msg)
                sys.stdout.flush()
                return False

            if api_info is True:
                api = self.__qp.get_api()
                sys.stdout.write('<IBM Quantum Experience API information>\n')
                sys.stdout.flush()
                sys.stdout.write('Version: {0}\n'.format(api.api_version()))
                sys.stdout.write('User jobs (last 5):\n')
                jobs = api.get_jobs(limit=500)

                def format_date(job_item):
                    '''
                    format
                    '''
                    return datetime.strptime(job_item['creationDate'],
                                             '%Y-%m-%dT%H:%M:%S.%fZ')
                sortedjobs = sorted(jobs,
                                    key=format_date)
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

        self.backends = self.__qp.available_backends()
        status = self.__qp.get_backend_status(self.backend)

        if 'available' in status:
            if status['available'] is False:
                return False
        return True

    def set_config(self, config=None):
        '''
        set config
        '''
        if config is None:
            config = {}

        if 'backend' in config:
            self.backend = str(config['backend'])
            if 'local_' in self.backend:
                self.remote = False
            else:
                self.remote = True

        if 'remote' in config:
            self.remote = config['remote']

        if 'qubits' in config:
            self.qubits = int(config['qubits'])

        return True

    def _progress(self, phasename, text):
        self.phase.append([str(phasename), str(text)])
        text = "Phase {0}: {1}".format(phasename, text)
        sys.stdout.write("{}\n".format(text))
        sys.stdout.flush()

    def _init_circuit(self):
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

        if 'cin' in self.__qp.get_quantum_register_names():
            self.__qp.destroy_quantum_registers(quantum_registers)
            self.__qp.destroy_classical_registers(classical_registers)

        q_r = self.__qp.create_quantum_registers(quantum_registers)
        c_r = self.__qp.create_classical_registers(classical_registers)

        self.__qp.create_circuit("qcirc", q_r, c_r)

    def _create_circuit_qadd(self):
        # quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
        def majority(circuit, q_a, q_b, q_c):
            '''
            majority
            '''
            circuit.cx(q_c, q_b)
            circuit.cx(q_c, q_a)
            circuit.ccx(q_a, q_b, q_c)

        def unmaj(circuit, q_a, q_b, q_c):
            '''
            unmajority
            '''
            circuit.ccx(q_a, q_b, q_c)
            circuit.cx(q_c, q_a)
            circuit.cx(q_a, q_b)

        def adder(circuit, c_in, q_a, q_b, c_out, qubits):
            '''
            adder
            '''
            # pylint: disable=too-many-arguments
            majority(circuit, c_in[0], q_b[0], q_a[0])
            for i in range(qubits - 1):
                majority(circuit, q_a[i], q_b[i + 1], q_a[i + 1])

            circuit.cx(q_a[qubits - 1], c_out[0])

            for i in range(qubits - 1)[::-1]:
                unmaj(circuit, q_a[i], q_b[i + 1], q_a[i + 1])
            unmaj(circuit, c_in[0], q_b[0], q_a[0])

        if 'add' not in self.__qp.get_circuit_names():
            [c_in, q_a, q_b, c_out] = map(self.__qp.get_quantum_register,
                                          ["cin", "qa", "qb", "cout"])
            ans = self.__qp.get_classical_register('ans')
            qadder = self.__qp.create_circuit("qadd",
                                              [c_in, q_a, q_b, c_out],
                                              [ans])
            adder(qadder, c_in, q_a, q_b, c_out, self.qubits)

        return 'add' in self.__qp.get_circuit_names()

    def _create_circuit_qsub(self):
        circuit_names = self.__qp.get_circuit_names()
        if 'qsub' not in circuit_names:
            if 'qadd' not in circuit_names:
                self._create_circuit_qadd()

            # subtractor circuit
            self.__qp.add_circuit('qsub', self.__qp.get_circuit('qadd'))
            qsubtractor = self.__qp.get_circuit('qsub')
            qsubtractor.reverse()
        return 'qsub' in self.__qp.get_circuit_names()

    def _qadd(self, input_a, input_b=None, subtract=False, observe=False):
        # pylint: disable=too-many-locals

        def measure(circuit, q_b, c_out, ans):
            '''
            measure
            '''
            circuit.barrier()
            for i in range(self.qubits):
                circuit.measure(q_b[i], ans[i])
            circuit.measure(c_out[0], ans[self.qubits])

        def char2q(circuit, cbit, qbit):
            '''
            char2q
            '''
            if cbit == '1':
                circuit.x(qbit)
            elif cbit == 'H':
                circuit.h(qbit)
                self.shots = 5 * (2**self.qubits)

        def input_state(circuit, input_a, input_b=None):
            '''
            input state
            '''
            input_a = input_a[::-1]
            for i in range(self.qubits):
                char2q(circuit, input_a[i], q_a[i])

            if input_b is not None:
                input_b = input_b[::-1]
                for i in range(self.qubits):
                    char2q(circuit, input_b[i], q_b[i])

        def reset_input(circuit, c_in, q_a, c_out):
            '''
            reset input
            '''
            circuit.reset(c_in)
            circuit.reset(c_out)
            for i in range(self.qubits):
                circuit.reset(q_a[i])

        # get registers
        [c_in, q_a, q_b, c_out] = map(self.__qp.get_quantum_register,
                                      ["cin", "qa", "qb", "cout"])
        ans = self.__qp.get_classical_register('ans')
        qcirc = self.__qp.get_circuit('qcirc')

        self._progress('2',
                       'Define input state ({})'
                       .format('QADD' if subtract is False else 'QSUB'))
        if input_b is not None:
            if subtract is True:
                # subtract
                input_state(qcirc, input_b, input_a)
            else:
                # add
                input_state(qcirc, input_a, input_b)
        else:
            reset_input(qcirc, c_in, q_a, c_out)
            input_state(qcirc, input_a)

        self._progress('3',
                       'Define quantum circuit ({})'
                       .format('QADD' if subtract is False else 'QSUB'))
        if subtract is True:
            self._create_circuit_qsub()
            qcirc.extend(self.__qp.get_circuit('qsub'))
        else:
            self._create_circuit_qadd()
            qcirc.extend(self.__qp.get_circuit('qadd'))

        if observe is True:
            measure(qcirc, q_b, c_out, ans)

    def _qsub(self, input_a, input_b=None, observe=False):
        self._qadd(input_a, input_b, subtract=True, observe=observe)

    def _qope(self, input_a, operator, input_b=None, observe=False):
        if operator == '+':
            return self._qadd(input_a, input_b, observe=observe)
        elif operator == '-':
            return self._qsub(input_a, input_b, observe=observe)
        return None

    def _compile(self, name, cross_backend=None, print_qasm=False):
        self._progress('4', 'Compile quantum circuit')

        coupling_map = None
        if cross_backend is not None:
            backend_conf = self.__qp.get_backend_configuration(cross_backend)
            coupling_map = backend_conf.get('coupling_map', None)
            if coupling_map is None:
                sys.stdout.write('backend: {} coupling_map not found'
                                 .format(cross_backend))

        qobj = self.__qp.compile([name],
                                 backend=self.backend,
                                 shots=self.shots,
                                 seed=1,
                                 coupling_map=coupling_map)

        if print_qasm is True:
            sys.stdout.write(self.__qp.get_compiled_qasm(qobj, 'qcirc'))
            sys.stdout.flush()
        return qobj

    def _run(self, qobj):
        self._progress('5', 'Run quantum circuit (wait for answer)')
        result = self.__qp.run(qobj, wait=5, timeout=100000)
        return result

    def _run_async(self, qobj):
        '''
        _run_async
        '''
        self._progress('5', 'Run quantum circuit')
        self.wait = True

        def async_result(result):
            '''
            async call back
            '''
            self.wait = False
            self.last = self.result_parse(result)

        self.__qp.run_async(qobj,
                            wait=5, timeout=100000, callback=async_result)

    def _is_regular_number(self, numstring, base):
        '''
        returns input binary format string or None.
        '''
        if base == 'bin':
            binstring = numstring
        elif base == 'dec':
            if numstring == 'H':
                binstring = 'H'*self.qubits
            else:
                binstring = format(int(numstring), "0{}b".format(self.qubits))

        if len(binstring) != self.qubits:
            return None

        return binstring

    def get_seq(self, text, base='dec'):
        '''
        convert seq and check it
        if text is invalid, return the list of length 0.
        '''
        operators = u'(\\+|\\-)'
        seq = re.split(operators, text)

        # length check
        if len(seq) % 2 == 0 or len(seq) == 1:
            return []

        # regex
        if base == 'bin':
            regex = re.compile(r'[01H]+')
        else:
            regex = re.compile(r'(^(?!.H)[0-9]+|H)')

        for i in range(0, len(seq), 2):
            match = regex.match(seq[i])
            if match is None:
                return []
            num = match.group(0)
            seq[i] = self._is_regular_number(num, base)

            if seq[i] is None:
                return []

        return seq

    def result_parse(self, result):
        '''
        result_parse
        '''
        data = result.get_data("qcirc")
        sys.stdout.write("job id: {0}\n".format(result.get_job_id()))
        sys.stdout.write("raw result: {0}\n".format(data))
        sys.stdout.write("{:=^40}\n".format("answer"))

        counts = data['counts']
        sortedcounts = sorted(counts.items(),
                              key=lambda x: -x[1])

        sortedans = []
        for count in sortedcounts:
            if count[0][0] == '1':
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
        if 'time' in data:
            sys.stdout.write("time: {0:<3} sec\n".format(data['time']))
        sys.stdout.write("All process done.\n")
        sys.stdout.flush()

        uniqanswer = sorted(set(sortedans), key=sortedans.index)

        ans = ",".join(uniqanswer)

        return [str(result), ans]

    def exec_calc(self, text, base='dec', wait_result=False):
        '''
        exec_calc
        '''
        seq = self.get_seq(text, base)
        print('QC seq:', seq)
        if seq == []:
            return ["Syntax error", None]

        # fail message
        fail_msg = None

        try:
            self._init_circuit()
            numbers = seq[0::2]     # slice even index
            i = 1
            observe = False
            for oper in seq[1::2]:  # slice odd index
                if i == len(numbers) - 1:
                    observe = True
                if i == 1:
                    self._qope(numbers[0], oper, numbers[1], observe=observe)
                else:
                    self._qope(numbers[i], oper, observe=observe)
                i = i + 1

            qobj = self._compile('qcirc')

            if wait_result is True:
                [status, ans] = self.result_parse(self._run(qobj))
            else:
                self._run_async(qobj)
                [status, ans] = [
                    'Wait. Calculating on {0}'.format(self.backend),
                    '...'
                    ]

        except QISKitError as ex:
            fail_msg = ('There was an error in the circuit!. Error = {}\n'
                        .format(ex))
        except RegisterSizeError as ex:
            fail_msg = ('Error in the number of registers!. Error = {}\n'
                        .format(ex))

        if fail_msg is not None:
            sys.stdout.write(fail_msg)
            sys.stdout.flush()
            return ["FAIL", None]

        return [status, ans]
