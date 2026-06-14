# -*- coding: utf-8 -*-
import requests, json, os, time
import urllib.parse
import pandas as pd

if __name__ == "__main__":
    def fmt_duration(d):
        if not d: return ""
        parts = d.split(":")
        try:
            if len(parts) == 2:
                m = int(parts[0])
                h = m // 60; m = m % 60
                return f"{h}\u5c0f\u65f6{m}\u5206\u949f" if h > 0 else f"{m}\u5206\u949f"
            elif len(parts) == 3:
                return f"{int(parts[0])}\u5c0f\u65f6{int(parts[1])}\u5206\u949f"
        except: pass
        return d

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config_homepage.json")
    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        user_agent = cfg.get("user_agent", "").strip()
        cookie = cfg.get("cookie", "").strip()
        print("[+] 已读取配置")
    else:
        print("[-] 未找到 config_homepage.json，请先配置 Cookie 和 User-Agent"); exit(1)

    keyword = input("请输入搜索关键词: ").strip()
    if not keyword:
        print("[-] 关键词不能为空"); exit(1)

    headers = {
        "User-Agent": user_agent,
        "Cookie": cookie,
        "Referer": "https://search.bilibili.com/all?keyword=" + urllib.parse.quote(keyword),
    }

    all_videos = []
    total_results = 0
    for page in range(1, 6):
        encoded_keyword = urllib.parse.quote(keyword)
        url = ("https://api.bilibili.com/x/web-interface/search/type"
               "?search_type=video&keyword=" + encoded_keyword +
               "&order=click&page=" + str(page))
        print(f"[*] 第 {page} 页...", end=" ", flush=True)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"状态码 {resp.status_code}"); break
            data = resp.json()
            if data.get("code") != 0:
                print(f"API错误: {data.get('message','')}"); break

            results = data.get("data", {}).get("result", [])
            if not results:
                print("无更多结果"); break

            if page == 1:
                total_results = data.get("data", {}).get("numResults", 0)
            for v in results:
                title = v.get("title", "").replace("<em class=\"keyword\">","").replace("</em>","")
                all_videos.append({
                    "BV号": v.get("bvid", ""),
                    "视频标题": title,
                    "UP主": v.get("author", ""),
                    "分类": v.get("typename", ""),
                    "时长": fmt_duration(v.get("duration", "")),
                    "播放量": v.get("play", 0),
                    "弹幕数": v.get("video_review", 0),
                    "收藏数": v.get("favorites", 0),
                    "点赞数": v.get("like", 0),
                    "评论数": v.get("review", 0),
                })

            print(f"{len(results)} 条")
            time.sleep(2)

        except Exception as e:
            print(f"请求失败: {e}"); break

    if not all_videos:
        print("[-] 未获取到数据"); exit()

    # 在表格末尾加一行汇总
    all_videos.append({
        "BV号": "",
        "视频标题": f"\u5171 {total_results} \u4e2a\u7ed3\u679c\uff0c\u672c\u8868\u5c55\u793a {len(all_videos)} \u4e2a",
        "UP主": "",
        "分类": "",
        "时长": "",
        "播放量": "",
        "弹幕数": "",
        "收藏数": "",
        "点赞数": "",
        "评论数": "",
    })

    os.makedirs("./crawledData", exist_ok=True)
    fn = f"./crawledData/{keyword}\u8bfe\u7a0b.xlsx"
    df = pd.DataFrame(all_videos)
    df.to_excel(fn, index=False)
    print(f"\n[+] 成功！共 {len(all_videos)} 个视频")
    print(f"[+] 已保存: {fn}")
