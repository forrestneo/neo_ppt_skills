# -*- coding: utf-8 -*-
"""bank-lite（精集合辑）调用工具 —— 与 scripts/bank_all_cli.py 同用法，默认指向精简包"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import bank_all_cli

bank_all_cli.TPL = os.path.normpath(os.path.join(HERE, "templates", "bank-lite"))
bank_all_cli.main(sys.argv[1:])
