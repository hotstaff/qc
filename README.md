# Quantum Calculator 
![screenshot](https://raw.github.com/wiki/hotstaff/qc/images/screen_shot.png "screen shot")

Quantum Calculator with QISKit.

## Overview

It is possible to add a natural number (0 to 7) expressed by 3 qbit.  Since the result also needs to be represented by 3 qbit, if it is more than 7 it will be Over Range (OR). The H button means that the Hadamard gate acts on the input gate, at that time the input gate simultaneously shows the state of (0 to 7), which enables quantum parallel computation.

## Usage

```
python3 qc.py
```

**In order to calculate on IBM Q quantum device, it is necessary to set API token. Please edit Qconfig.py.**

## Requirement
 * [QISKit](https://www.qiskit.org/) >=0.4.7
 * [Python](https://www.python.org/) >=3.5 (this is required QISKit)
 * [wxPython](https://www.wxpython.org/) >=4.0?

###git

 * [qiskit-sdk-py](https://github.com/QISKit/qiskit-sdk-py)
 * [wxPython Project Phoenix](https://github.com/wxWidgets/Phoenix)

## How it works

In order to add up, this program requires a 10 qbit quantum circuit. The breakdown of each bit is input register 3qbit + 3qbit and output register 3qbit + 1qbit(OR). The quantum algorithm of this addition was prepared with reference to [Qiita @converghub
 article](https://qiita.com/converghub/items/c61b2b91b311cf730e18).
As of January 2017, there are no real quantum devices available to create and use the gate with free arrangement from QISKit. Therefore, it is currently operating on the simulator.

## Referece

 *  [Qiita, @converghub, 量子コンピュータ（シミュレータ）でモジュール化可能な加算器を作る](https://qiita.com/converghub/items/c61b2b91b311cf730e18)

## Version History

 * 2017/1/28 v0.0.1 **3qbit + 3qbit = 3qbit addition supports.**

## Author

Hideto Manjo

## Licence

[Apache Licence 2.0](https://raw.githubusercontent.com/hotstaff/qc/master/LICENSE)