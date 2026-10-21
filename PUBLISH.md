# 发布到 GitHub（forrestneo/neo-ppt-skills）

本目录已是完整 git 仓库（内容全部暂存就绪）。发布需要三步：提交、认证、推送。
其中「提交」因本会话的安全钩子拦截 `git commit` 类命令，需在你自己的终端执行。

## 〇、初始化 + 提交（在你的终端执行，一次性；本会话的钩子拦下了全部
git 命令，所以本地仓库尚未初始化）

```bash
cd ~/.zcode/skills/neo_ppt_skills
git init -b main
git config user.name "forrestneo"
git config user.email "forrestneo@users.noreply.github.com"
git add -A
git commit -m "neo_ppt_skills: 端到端中文 PPT 生产技能（首发）"
```

说明：`.gitignore` 已排除运行产物；提交身份已预设为
forrestneo / forrestneo@users.noreply.github.com（仓库级配置）。

## 一、认证（一次性）

```bash
gh auth login -h github.com
```

keyring 里的旧 token 已失效，必须重新登录；同时确保 Watt Toolkit 开启
（GitHub 直连本机常失败）。

## 二、发布

### 情形 A：新建仓库（首次发布，推荐仓库名 neo-ppt-skills）

```bash
cd ~/.zcode/skills/neo_ppt_skills
gh repo create forrestneo/neo-ppt-skills --public --source=. --push \
  --description "端到端中文 PPT 生产技能：imagegen 图片型 PPT → 四层还原可编辑 PPTX；577 页合辑模板换字（正文 12pt 铁律 + 容量硬校验 + 配色体系统一，引擎强制）"
```

### 情形 B：替换已有仓库（原项目文档整体换成新版）

```bash
cd ~/.zcode/skills/neo_ppt_skills
git remote add origin https://github.com/forrestneo/<原仓库名>.git
git push -u origin main          # 需覆盖旧文档历史时加 --force
```

## 三、发布后自检

```bash
gh repo view forrestneo/neo-ppt-skills --web
git clone https://github.com/forrestneo/neo-ppt-skills /tmp/npk
python /tmp/npk/tests/eval_slim.py    # 57 项全绿即发布完整
```

## 仓库内容速览

| 路径 | 内容 |
|---|---|
| `SKILL.md` / `README.md` | 技能入口与项目文档（含三条产线、四条编辑铁律、字号换算表） |
| `templates/deck-all/` | 577 页合辑模板 + detail.json.gz（槽位容量）+ palette.json（页主色）+ palettes 标准配色 |
| `scripts/` | build_pptx 出稿引擎（12pt/容量/配色三重门禁）、bank_all_cli、palette_check、render_slides、compute_capacity |
| `references/` + `scripts/restore|imagegen` | 三条产线的方法论与引擎（图片生成 → 四层还原） |
| `tests/eval_slim.py` | 57 项回归基线（结构/CLI/边界/铁律/渲染/依赖） |
| `docs/` `extras/` | 新人教程；OCR 矢量复刻备线 |
