# -*- coding: utf-8 -*-
"""
b_playwright.py - Playwright 爬取 B 站评论（无 412）

使用已登录的 Edge 配置文件，在浏览器中直接 fetch() API，
因为是真实浏览器请求，不会被 412 拦截。

用法:
  1. 关闭 Edge 浏览器
  2. python crawlers/b_playwright.py
  3. 输入 Bvid 号
"""
import asyncio, json, os, sys, time
import pandas as pd
from playwright.async_api import async_playwright

EDGE = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")

def trans_date(v):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(v)))

def parse_comment(c):
    uid = c["member"]["mid"]; uname = c["member"]["uname"]
    gender = c["member"]["sex"]; pt = trans_date(c["ctime"])
    ip = c.get("reply_control",{}).get("location","")
    if ip.startswith("IP"): ip = ip.split("\uff1a",1)[-1]
    if not ip: ip = "\u672a\u77e5"
    text = c["content"]["message"].strip().replace("\n"," ")
    return uid, uname, gender, pt, ip, text, c["like"]

async def run(bvid, max_p=40):
    all_c = []
    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=EDGE, channel="msedge",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        p = await ctx.new_page()
        p.set_default_timeout(30000)
        await p.goto("https://www.bilibili.com/", wait_until="domcontentloaded")
        await p.wait_for_timeout(2000)

        cookies = await ctx.cookies()
        bc = [c for c in cookies if "bilibili" in c.get("domain","")]
        logged = any("SESSDATA" in c["name"] for c in bc)
        if not logged:
            print("[-] B\u7ad9\u672a\u767b\u5f55\uff0c\u8bf7\u786e\u8ba4 Edge \u4e2d\u5df2\u767b\u5f55")
            await ctx.close(); return []
        print(f"[+] \u767b\u5f55\u6001\u6b63\u5e38 ({len(bc)} cookies)")

        for n in range(1, max_p+1):
            fetch_url = f"https://api.bilibili.com/x/v2/reply/main?next={n}&type=1&oid={bvid}&mode=3"
            print(f"[*] \u7b2c {n} \u9875...", end="", flush=True)
            try:
                js = rf"""
async () => {{
    try {{
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 15000);
        const r = await fetch("{fetch_url}", {{
            signal: ctrl.signal,
            credentials: "include",
            headers: {{ Referer: "https://www.bilibili.com/video/{bvid}" }}
        }});
        clearTimeout(tid);
        return JSON.stringify(await r.json());
    }} catch(e) {{
        return JSON.stringify({{"__err__": e.message}});
    }}
}}
"""
                r = json.loads(await p.evaluate(js))
                if "__err__" in r:
                    print(f"\n[-] {r['__err__']}"); break
                if r.get("data") is None or r["data"].get("replies") is None:
                    print(" \u5df2\u5230\u672b\u5c3e"); break
                keys = ["User_ID","User_Name","Gender","Publish_Time","IP_Location","Content","Likes"]
                cnt = 0
                for cm in r["data"]["replies"]:
                    all_c.append(dict(zip(keys, parse_comment(cm)))); cnt += 1
                    for ch in (cm.get("replies") or []):
                        all_c.append(dict(zip(keys, parse_comment(ch)))); cnt += 1
                print(f" +{cnt}\u6761(\u7d2f\u8ba1{len(all_c)})")
            except Exception as e:
                print(f"\n[-] {e}"); break
            time.sleep(3)
        await ctx.close()
    return all_c

if __name__ == "__main__":
    bvid = input("Bvid\u53f7: ").strip()
    if not os.path.isdir(EDGE):
        print(f"[-] \u672a\u627e\u5230 Edge: {EDGE}"); exit(1)
    print("[*] \u8bf7\u786e\u8ba4 Edge \u5df2\u5173\u95ed")
    data = asyncio.run(run(bvid))
    if data:
        os.makedirs("./crawledData", exist_ok=True)
        fn = f"./crawledData/bilibili_comments_{bvid}.xlsx"
        cols = ["User_ID","User_Name","Gender","Publish_Time","IP_Location","Content","Likes"]
        df = pd.DataFrame(data)[cols]; df.to_excel(fn, index=False)
        print(f"\n[+] \u5171{len(data)}\u6761 -> {fn}")
    else:
        print("\n[-] \u65e0\u6570\u636e")
