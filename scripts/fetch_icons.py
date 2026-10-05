# -*- coding: utf-8 -*-
"""
fetch_icons.py — 图标接口工具（ppt-master 图标契约兼容）
用法:
  python3 fetch_icons.py <project_path> <collection/name> [...] [--source auto|api|local]
  collection: tabler | simple-icons | phosphor-duotone | tabler-filled | 任意iconify集合名
行为:
  auto(默认): 本地捆绑库有→直接复制；没有→从 iconify API 拉取
  api:        强制走 https://api.iconify.design
  local:      只用本地捆绑库（离线）
产物: <project>/icons/<collection>/<name>.svg（checker/exporter 契约位置）
注意: iconify 拉回的 tabler 图标是 stroke=currentColor 写法，会按技能契约改写为
      fill="currentColor" 以兼容 <use data-icon> 的 fill 用法。
"""
import os
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
def _find_skill_icons() -> Path:
    """便携解析：优先相对本文件定位 ppt-master（离线包布局），回退本机安装路径。"""
    here = Path(__file__).resolve().parent
    for cand in (here.parent / "ppt-master" / "templates" / "icons",
                 here / "ppt-master" / "templates" / "icons",
                 Path(r"C:\Users\w\.zcode\skills\ppt-master\templates\icons")):
        if cand.is_dir():
            return cand
    return Path(r"C:\Users\w\.zcode\skills\ppt-master\templates\icons")
SKILL_ICONS = _find_skill_icons()
API = "https://api.iconify.design/{}/{}/{}.svg"

def fix_currentcolor(svg: str) -> str:
    """tabler 系 stroke=currentColor → fill=currentColor（技能图标契约：<use> 只认 fill）"""
    if 'stroke="currentColor"' in svg and "fill=" not in svg.split(">")[0]:
        svg = svg.replace('fill="none" stroke="currentColor"', 'fill="currentColor" stroke="none"', 1)
    return svg

def fetch_one(project: Path, spec: str, source: str) -> str:
    collection, _, name = spec.partition("/")
    if not name:
        return f"SKIP {spec} (格式应为 collection/name)"
    dest = project / "icons" / collection / f"{name}.svg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return f"OK(exists) {spec}"

    local = SKILL_ICONS / collection / f"{name}.svg"
    if source in ("auto", "local") and local.exists():
        dest.write_bytes(local.read_bytes())
        return f"OK(local) {spec}"

    if source == "api":
        return f"SKIP {spec} (api 模式需联网；离线环境请用 --source local 或将图标放入项目 icons/)"
    return f"MISS {spec} (本地无且 source=local)"

def main():
    args = [a for a in sys.argv[1:]]
    source = "auto"
    if "--source" in args:
        i = args.index("--source")
        source = args[i + 1]
        del args[i:i + 2]
    project = Path(args[0])
    specs = args[1:]
    ok = 0
    for s in specs:
        line = fetch_one(project, s, source)
        print(line)
        if line.startswith("OK"):
            ok += 1
    print(f"--- {ok}/{len(specs)} ready under {project / 'icons'}")

if __name__ == "__main__":
    main()
