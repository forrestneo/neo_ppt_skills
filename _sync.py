# -*- coding: utf-8 -*-
"""临时同步脚本：提交并推送本轮排版蒸馏（用后即删）。"""
import subprocess
import sys

MSG = (
    "stylekit 排版四门蒸馏：9 引擎版式几何/防溢出/验收协议/编辑保真 "
    "+ layout_audit 孤字检测（评测 80 项）"
)

def run(*args):
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    print(r.stdout[-800:])
    if r.returncode != 0:
        print(r.stderr[-800:], file=sys.stderr)
    return r.returncode

rc = run("add", "-A")
rc |= run("commit", "-m", MSG) and 0  # 无新提交时容错
rc |= run("push", "origin", "main")
sys.exit(1 if rc else 0)
