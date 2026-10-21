# -*- coding: utf-8 -*-
"""deck_cli.py 补 --theme 透传。"""
p = "scripts/deck_cli.py"
s = open(p, encoding="utf-8").read()

a1 = "    allow_small_font = allow_mixed = False"
b1 = "    allow_small_font = allow_mixed = False\n    theme_id = None"
a2 = '''    if "--allow-mixed-palette" in argv:
        allow_mixed = True
        argv.remove("--allow-mixed-palette")'''
b2 = '''    if "--allow-mixed-palette" in argv:
        allow_mixed = True
        argv.remove("--allow-mixed-palette")
    if "--theme" in argv:
        i = argv.index("--theme")
        theme_id = argv[i + 1]; del argv[i:i + 2]'''
a3 = "                          detail=detail_path, allow_small_font=allow_small_font,\n                          allow_mixed_palette=allow_mixed)"
b3 = "                          detail=detail_path, allow_small_font=allow_small_font,\n                          allow_mixed_palette=allow_mixed, theme=theme_id)"

for a, b in ((a1, b1), (a2, b2), (a3, b3)):
    assert a in s, "anchor missing: " + a[:40]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("deck_cli --theme 透传完成")
