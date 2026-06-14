# -*- coding: utf-8 -*-
"""
一次性 Cookie 提取工具 (需以管理员身份运行一次)
用法：以管理员身份打开终端，运行：
  python crawlers/extract_cookies.py

之后运行 b_tools.py 就会自动读取保存的 Cookie，无需再手动输入。
"""
import browser_cookie3 as bc
import json
import os

if __name__ == "__main__":
    print("=" * 55)
    print("  Bilibili Cookie 提取工具（一次性的）")
    print("=" * 55)
    print()

    cookie_jar = None
    for browser_name, loader in [
        ("Edge", bc.edge),
        ("Chrome", bc.chrome),
        ("Chromium", bc.chromium),
    ]:
        try:
            cookie_jar = loader(domain_name="bilibili.com")
            print(f"✅ 已从 {browser_name} 读取到 Bilibili Cookie")
            break
        except Exception as e:
            print(f"  {browser_name}: {e}")
            continue

    if cookie_jar is None:
        print("❌ 未能从任何浏览器获取 Cookie，请确认已登录 Bilibili。")
        exit(1)

    cookie_list = []
    for c in cookie_jar:
        cookie_list.append({
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
        })

    save_path = os.path.join(os.path.dirname(__file__), "..", "cookies.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(cookie_list, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Cookie 已保存至: {save_path}")
    print(f"   共提取 {len(cookie_list)} 条 Cookie 记录")
    print(f"\n现在可以直接运行 b_tools.py 了，它会自动读取此文件！")
