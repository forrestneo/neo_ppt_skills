# -*- coding: utf-8 -*-
"""bank-lite（精集合辑）调用工具 —— 与 use_bank_all.py 同用法，默认指向精简包"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import use_bank_all

use_bank_all.TPL = os.path.normpath(os.path.join(HERE, "templates", "bank-lite"))
use_bank_all.main(sys.argv[1:])
