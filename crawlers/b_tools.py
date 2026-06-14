import requests
import time
from datetime import datetime
import pandas as pd
import os
import json
import re

_ILLEGAL_UNICODE = re.compile(
    '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f'
    '\u00ad\u0600-\u0605\u061c\u06dd\u070f\u08e2\u180e'
    '\u200b-\u200f\u2028-\u202f\u2060-\u2066'
    '\u2067-\u206e\u206f\ufdd0-\ufdef\ufeff\ufff9-\ufffb'
    '\U0001fffe-\U0001ffff\U0002fffe-\U0002ffff'
    '\U0003fffe-\U0003ffff\U0004fffe-\U0004ffff'
    '\U0005fffe-\U0005ffff\U0006fffe-\U0006ffff'
    '\U0007fffe-\U0007ffff\U0008fffe-\U0008ffff'
    '\U0009fffe-\U0009ffff\U000afffe-\U000affff'
    '\U000bfffe-\U000bffff\U000cfffe-\U000cffff'
    '\U000dfffe-\U000dffff\U000efffe-\U000effff'
    '\U000ffffe-\U000fffff\U0010fffe-\U0010ffff]'
)


def clean_excel_value(val):
    """Remove characters illegal for openpyxl Excel output."""
    if isinstance(val, str):
        return _ILLEGAL_UNICODE.sub('', val)
    return val

def trans_date(v_timestamp):
    v_timestamp = float(v_timestamp)
    timeArray = time.localtime(v_timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime

def fecth_everything(comment):
    user_id = comment["member"]["mid"]
    username = comment["member"]["uname"]
    gender = comment["member"]["sex"]
    time_un = comment["ctime"]
    publish_time = trans_date(time_un)
    if "location" in comment.get("reply_control", {}):
        IP = comment["reply_control"]["location"].replace("IP\u5c5e\u5730\uff1a", "")
    else:
        IP = "\u672a\u77e5"
    content = comment["content"]["message"].strip().replace('\n', ' ')
    num = comment["like"]
    return user_id, username, gender, publish_time, IP, content, num

def fetch_comments(video_bv, headers, max_pages):
    all_comments_list = []
    for page in range(1, max_pages + 1):
        url = f'https://api.bilibili.com/x/v2/reply/main?next={page}&type=1&oid={video_bv}&mode=3'
        print(f"\U0001f4e1 \u6b63\u5728\u6293\u53d6: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"\u2705 \u7b2c {page} \u9875\u5df2\u83b7\u53d6\u5b8c\u6bd5\uff01")
                if data.get('data') is None or data['data'].get('replies') is None:
                    print("\U0001f3c1 \u5df2\u7ecf\u5230\u8fbe\u8bc4\u8bba\u533a\u672b\u5c3e\uff0c\u6ca1\u6709\u66f4\u591a\u6570\u636e\u3002")
                    break
                for comment in data['data']['replies']:
                    user_id, username, gender, publish_time, IP, content, num = fecth_everything(comment)
                    all_comments_list.append({
                        "User_ID": user_id, "User_Name": username, "Gender": gender,
                        "Publish_Time": publish_time, "IP_Location": IP, "Content": content, "Likes": num
                    })
                    if comment.get("replies"):
                        for child in comment["replies"]:
                            c_user_id, c_username, c_gender, c_publish_time, c_IP, c_content, c_num = fecth_everything(child)
                            all_comments_list.append({
                                "User_ID": c_user_id, "User_Name": c_username, "Gender": c_gender,
                                "Publish_Time": c_publish_time, "IP_Location": c_IP, "Content": c_content, "Likes": c_num
                            })
            else:
                print(f"\u274c \u7f51\u9875\u72b6\u6001\u7801\u5f02\u5e38: {response.status_code}")
                break
        except requests.RequestException as e:
            print(f"\u8bf7\u6c42\u51fa\u9519: {e}")
            break
        time.sleep(2)
    return all_comments_list

if __name__ == "__main__":
    # --- \u8bfb\u53d6 config.json ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    if os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        user_agent = cfg.get("user_agent", "").strip()
        cookie = cfg.get("cookie", "").strip()
        print("[+] \u5df2\u4ece config.json \u8bfb\u53d6\u914d\u7f6e")
    else:
        print("[-] \u672a\u627e\u5230 config.json\uff0c\u8bf7\u5148\u914d\u7f6e")
        exit(1)
    
    headers = {
        'User-Agent': user_agent,
        'Cookie': cookie
    }
    max_pages_to_crawl = 40

    # --- \u8bfb\u53d6 bvid_courses.txt ---
    course_path = os.path.join(script_dir, "bvid_courses.txt")
    courses = []
    if os.path.isfile(course_path):
        with open(course_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines()]
        current = None
        for line in lines:
            if not line:
                continue
            if line.startswith("BV"):
                if current is not None:
                    for bv in line.split():
                        if bv.startswith("BV"):
                            courses[-1][1].append(bv)
            else:
                current = line
                courses.append([line, []])
    
    if not courses:
        print("[-] bvid_courses.txt \u65e0\u914d\u7f6e")
        exit()

    # --- \u9010\u4e2a\u5904\u7406 ---
    for ci, (course_name, bvid_list) in enumerate(courses, 1):
        out_dir = "./crawledData/" + course_name
        os.makedirs(out_dir, exist_ok=True)
        print(f"\n{'='*50}")
        print(f"[{ci}/{len(courses)}] {course_name} ({len(bvid_list)} \u4e2a\u89c6\u9891)")
        print(f"{'='*50}")
        for idx, bv in enumerate(bvid_list, 1):
            if idx > 1:
                print("  \u7b49\u5f85 20 \u79d2\uff08\u907f\u514d\u98ce\u63a7\uff09...")
                time.sleep(20)
            print(f"\n  [{idx}/{len(bvid_list)}] {bv} \u5f00\u59cb\u722c\u53d6...")
            parsed_data = fetch_comments(video_bv=bv, headers=headers, max_pages=max_pages_to_crawl)
            if parsed_data:
                fn = f'{out_dir}/bilibili_comments_{bv}.xlsx'
                df = pd.DataFrame(parsed_data)
                columns_order = ["User_ID", "User_Name", "Gender", "Publish_Time", "IP_Location", "Content", "Likes"]
                df = df[columns_order]
                df = df.map(clean_excel_value)
                df.to_excel(fn, index=False)
                print(f"  [{idx}/{len(bvid_list)}] {bv}: \u5b8c\u6210 ({len(parsed_data)} \u6761) -> {fn}")
            else:
                print(f"  [{idx}/{len(bvid_list)}] {bv}: \u65e0\u6570\u636e")

    print(f"\n[+] \u5168\u90e8\u5b8c\u6210\uff01\u5171\u5904\u7406 {len(courses)} \u95e8\u8bfe\u7a0b")
