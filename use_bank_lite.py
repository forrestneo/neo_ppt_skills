# -*- coding: utf-8 -*-
"""bank-lite（精集合辑）调用工具 —— 与 use_bank_all.py 同用法，默认指向精简包"""
import os
os.environ["BANK_TPL"] = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "templates", "bank-lite")
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "use_bank_all.py"), encoding="utf-8").read())
