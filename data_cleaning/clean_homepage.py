# -*- coding: utf-8 -*-
import os, sys, re, copy
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

    print(f"[*] {len(courses)} courses..." + NL)
    new_lines = list(lines)
    updated = 0

    for cname in courses:
        xlsx = os.path.abspath(os.path.join(sd, "..", "crawledData", cname + "课程.xlsx"))
        print(f"[{cname}]", end=" ", flush=True)
        if not os.path.isfile(xlsx):
            print("skip (no xlsx)"); continue
        df = pd.read_excel(xlsx)
        if df.empty:
            print("skip (empty)"); continue
        n = len(df)
        df["mins"] = df["时长"].apply(parse_minutes)
        ok = df[df["mins"] >= 30]
        bv_list = ok["BV号"].dropna().tolist()
        print(f"{n} -> {len(bv_list)}")

        if not bv_list: continue
        idx = None
        for i, l in enumerate(new_lines):
            if l.strip() == cname:
                idx = i; break
        if idx is None: continue

        end = idx + 1
        while end < len(new_lines):
            l = new_lines[end].strip()
            if l and not l.startswith("BV"): break
            end += 1

        up = new_lines[:idx+1] + bv_list + new_lines[end:]
        new_lines = up
        updated += 1

    if updated > 0:
        with open(txt, "w", encoding="utf-8") as f:
            f.write(NL.join(new_lines) + NL)
        print(NL + "[+] Done! Updated", updated, "courses")
    else:
        print(NL + "[-] Nothing to update")
