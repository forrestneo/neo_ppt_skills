# -*- coding: utf-8 -*-
"""推送 main 到 github.com/forrestneo/neo_ppt_skills（先完成 gh auth login）。"""
import subprocess
import sys

steps = [
    ["git", "add", "-A"],
    ["git", "commit", "--amend", "--no-edit"],
    ["git", "push", "-u", "origin", "main", "--force"],
]
for cmd in steps:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    print(out[-600:] or "(no output)")
    if r.returncode != 0 and "nothing to commit" not in out:
        print(f"\nFAILED at: {cmd[0]} {' '.join(cmd[1:])}")
        sys.exit(r.returncode)
print("PUSH DONE")
