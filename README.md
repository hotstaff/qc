# Quantum Calculator 
![screenshot](https://raw.github.com/wiki/hotstaff/qc/images/screen_shot.png "screen shot")

Quantum Calculator with QISKit.

## Note

**At this time, the program no longer works properly due to specification changes of QISkit.**

There are plans to correspond current specification soon.


## Overview

It is possible to add a natural number expressed by n Qubits.  Since the result also needs to be represented by n Qubits, if it is more than n Qubits it will be Over Range (OR). The H button means that the Hadamard gate acts on the input gate, at that time the input gate simultaneously shows the state of (0, 1, 2, ... , 2^n-1), which enables quantum parallel computation.

## Usage

```
python3 qc.py
```

In order to calculate on IBM Q quantum device, it is necessary to set API token. Please edit Qconfig.py.

**Execution on the real device is possible by preparing Qconfig.py, but any operation using this program can not be guaranteed Please check it well before execution.**

## Requirement

 * [QISKit](https://www.qiskit.org/) >=0.4.7
 * [Python](https://www.python.org/) >=3.5 (this is required QISKit)
 * [wxPython](https://www.wxpython.org/) >=4.0?

### git

 * [qiskit-sdk-py](https://github.com/QISKit/qiskit-sdk-py)
 * [wxPython Project Phoenix](https://github.com/wxWidgets/Phoenix)

## How it works
In order to add or subtract, this program requires  2*n+2 Qubits quantum circuit where n is number of input qubits. The quantum algorithm of this adder was prepared with reference to  [quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184](https://arxiv.org/abs/quant-ph/0410184).

## Referece

 *  [Qiita, @converghub, 量子コンピュータ（シミュレータ）でモジュール化可能な加算器を作る](https://qiita.com/converghub/items/c61b2b91b311cf730e18)

 *  [Quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184](https://arxiv.org/abs/quant-ph/0410184)

## Version History

 * 2018/03/03  v0.0.2 **n Qubits + n Qubits = n Qubits addition and subtract support.** 
 * 2017/01/28 v0.0.1 **3 Qubits + 3 Qubits = 3 Qubits addition supports.**

## Author

Hideto Manjo

## Licence

[Apache Licence 2.0](https://raw.githubusercontent.com/hotstaff/qc/master/LICENSE)
