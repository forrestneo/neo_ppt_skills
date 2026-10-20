# -*- coding: utf-8 -*-
"""一键发布：删除原仓库 → 重建 → 推送 neo_ppt_skills 2.0.0

前置（一次性，在你的终端执行）：
  gh auth login -h github.com                 # 重新认证（旧 token 已失效）
  gh auth refresh -h github.com -s delete_repo  # 补充删库权限 scope

然后运行：python _push.py
  步骤：1) 删除原仓库 forrestneo/neo_ppt_skills
        2) 重建同名公开仓库（带简介）
        3) 强制推送 main（本仓库全部新内容）
"""
import subprocess
import sys

USER_REPO = "forrestneo/neo_ppt_skills"
DESC = ("端到端中文/双语 PPT 生产技能：imagegen 图片型 PPT → 四层还原可编辑 PPTX；"
        "577 页合辑模板换字（正文 12pt 铁律 + 容量硬校验 + 配色体系统一，引擎强制）")


def run(cmd, ok_msg=None, fatal=True):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if ok_msg:
        print(ok_msg)
    elif out:
        print(out[-600:])
    if r.returncode != 0 and fatal:
        print(f"\nFAILED at: {' '.join(cmd)}")
        if out:
            print(out[-800:])
        sys.exit(r.returncode)
    return r


def main():
    gh_ok = run(["gh", "auth", "status", "-h", "github.com"], fatal=False)
    # gh auth status 非零即未认证，直接失败退出
    if gh_ok.returncode != 0:
        print("ERROR: GitHub 认证不可用。请先执行：\n"
              "  gh auth login -h github.com\n"
              "  gh auth refresh -h github.com -s delete_repo")
        sys.exit(4)

    print("== 1/3 删除原仓库 ==")
    run(["gh", "repo", "delete", USER_REPO, "--yes"],
        ok_msg="原仓库已删除")

    print("== 2/3 重建仓库 ==")
    run(["gh", "repo", "create", USER_REPO, "--public",
         "--description", DESC], ok_msg="仓库已重建")

    print("== 3/3 推送新代码 ==")
    run(["git", "add", "-A"])
    # 容错：若无新变更 commit 会失败，忽略
    run(["git", "commit", "-m", "neo_ppt_skills 2.0.0"], fatal=False)
    run(["git", "push", "-u", "origin", "main", "--force"],
        ok_msg="推送完成")
    print("\nPUBLISH DONE -> https://github.com/" + USER_REPO)


if __name__ == "__main__":
    main()
