# -*- coding: utf-8 -*-
import os, sys, re
import pandas as pd

def parse_minutes(d):
    d = str(d).strip()
    if not d or d == "nan":
        return 0
    total = 0
    mh = re.search(r"(\d+)小时", d)
    mm = re.search(r"(\d+)分钟", d)
    if mh: total += int(mh.group(1)) * 60
    if mm: total += int(mm.group(1))
    return total

def find_xlsx(sd: str, cname: str):
    """查找课程对应的 xlsx 文件，忽略大小写差异"""
    cd = os.path.abspath(os.path.join(sd, "..", "crawledData"))
    target = cname + "课程.xlsx"
    for f in os.listdir(cd):
        if f.lower() == target.lower():
            return os.path.join(cd, f)
    return None

def save_cleaned_xlsx(df_clean, cname: str, sd: str):
    """将清洗后的 DataFrame 导出到清洗后的课程目录"""
    out_dir = os.path.abspath(os.path.join(sd, "..", "清洗后的课程"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, cname + "课程.xlsx")
    df_clean.to_excel(out_path, index=False)
    return out_path

if __name__ == "__main__":
    NL = chr(10)
    sd = os.path.dirname(os.path.abspath(__file__))
    txt = os.path.abspath(os.path.join(sd, "..", "crawlers", "bvid_courses.txt"))
    if not os.path.isfile(txt):
        print("[-] missing:", txt); exit(1)

    with open(txt, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = raw.split(NL)

    courses = [l.strip() for l in lines if l.strip() and not l.strip().startswith("BV")]
    if not courses:
        print("[-] no courses"); exit(1)

    print(f"[*] {len(courses)} courses to clean" + NL)
    new_lines = list(lines)
    updated = 0
    STATS = []

    for cname in courses:
        xlsx = find_xlsx(sd, cname)
        if not xlsx:
            print(f"[{cname}] skip (no xlsx)")
            STATS.append((cname, 0, 0, 0, None))
            continue
        print(f"[{cname}]", end="", flush=True)
        df = pd.read_excel(xlsx)
        if df.empty:
            print(" -> skip (empty)")
            STATS.append((cname, 0, 0, 0, None))
            continue
        n = len(df)
        df["mins"] = df["时长"].apply(parse_minutes)
        ok = df[df["mins"] >= 30]
        removed = n - len(ok)
        bv_list = ok["BV号"].dropna().tolist()

        # 导出清洗后的 xlsx
        if not ok.empty:
            out_path = save_cleaned_xlsx(ok, cname, sd)
        else:
            out_path = None
        STATS.append((cname, n, len(bv_list), removed, out_path))
        print(f" {n}->{len(bv_list)} ({removed} filtered)")

        if not bv_list:
            continue
        idx = None
        for i, l in enumerate(new_lines):
            if l.strip() == cname:
                idx = i; break
        if idx is None:
            continue

        end = idx + 1
        while end < len(new_lines):
            l = new_lines[end].strip()
            if l and not l.startswith("BV"):
                break
            end += 1

        up = new_lines[:idx+1] + bv_list + new_lines[end:]
        new_lines = up
        updated += 1

    if updated > 0:
        with open(txt, "w", encoding="utf-8") as f:
            f.write(NL.join(new_lines) + NL)
        print(NL + "[+] bvid_courses.txt updated (" + str(updated) + " courses)")
    else:
        print(NL + "[-] bvid_courses.txt unchanged")

    # 输出汇总
    print(NL + "=" * 60)
    print("清洗结果汇总：")
    print("=" * 60)
    header = f"{'课程':<12} {'原始':>5} {'保留':>5} {'过滤':>5}"
    print(header)
    print("-" * 40)
    total_ori, total_clean = 0, 0
    for cname, n, keep, removed, out_path in STATS:
        total_ori += n
        total_clean += keep
        flag = "  *" if out_path else ""
        print(f"{cname:<12} {n:>5} {keep:>5} {removed:>5}{flag}")
    print("-" * 40)
    print(f"{'合计':<12} {total_ori:>5} {total_clean:>5} {total_ori-total_clean:>5}")
    clean_dir = os.path.abspath(os.path.join(sd, "..", "清洗后的课程"))
    print(NL + f"清洗后 xlsx 保存目录：{clean_dir}")
