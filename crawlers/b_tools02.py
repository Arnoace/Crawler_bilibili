import requests
from datetime import datetime
import pandas as pd
import time
import json

data = []

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    "cookie": "buvid_fp=e97de9811f1af09c7385f099a4f3104d; enable_web_push=DISABLE; buvid4=458F7D22-E431-A882-2612-538973FAF25601829-025030412-W9jtpoE8eYZuJ0gXrQAgyA%3D%3D; DedeUserID=3546760217626711; DedeUserID__ckMd5=276af90c606e39e1; rpdid=|(um~u)YJuJm0J'u~RmRYR)Yk; theme-tip-show=SHOWED; CURRENT_QUALITY=0; theme-avatar-tip-show=SHOWED; home_feed_column=4; buvid3=653F1B83-23B6-666F-FB23-E263B93FD2E278491infoc; b_nut=1781091878; _uuid=BB7AFCD7-61010D-3155-10478-9454982D9F5781237infoc; browser_resolution=1232-596; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODEzNTEwODUsImlhdCI6MTc4MTA5MTgyNSwicGx0IjotMX0.2f5SwdQ2flJCOGiJSawlMvFkzTVkHfcGbkkyBMXtFDc; bili_ticket_expires=1781351025; SESSDATA=70bf8bef%2C1796643891%2C5e70b%2A61CjA4LqBzKVvgWf0HfVOamQcKlqhurPcZH2BpUUSCw3V5L4XoGx1tMPTG1aabJ3oMCaESVkZDdi1vTG9hX19CYkk1a2xDSXN3ZWpIMEZHODBrYVczejFWRkhLZGNJZ3hRV3QtNFIwTFZKdmhheklJMmpIalFqU3JLdUFMaWYzQXRaT1pFb096ekJBIIEC; bili_jct=80e7648602802d376d00d12e89cd5d7f; sid=4hf1i8jl; bp_t_offset_3546760217626711=1212496278710124544; bsource=search_bing; CURRENT_FNVAL=4048; b_lsid=3A2E34C0_19EB530F16C"
}

# 初始请求参数
params = {
    'oid': '48624233',
    'type': 1,
    'mode': 3,
    'pagination_str': '{"offset":""}',  # 💡 初始第一页
    'plat': 1,
    'seek_rpid': '',
    'web_location': 1315875,
    'w_rid': '451d947362289317b1ff8299902c790c',
    'wts': '1781156345',
}

url = 'https://api.bilibili.com/x/v2/reply/wbi/main'

# ⚙️ 设置你想爬取的总页数
max_pages = 5  

for page_num in range(1, max_pages + 1):
    print(f"\n🚀 [正在爬取] 第 {page_num} 页...")
    
    try:
        response = requests.get(url=url, headers=headers, params=params).json()
        
        # 1. 检查接口返回状态
        if response.get('code') != 0:
            print(f"⚠️ 第 {page_num} 页请求受阻。原因: {response.get('message')} (可能是固定 w_rid 触发了多页风控)")
            break
            
        data_node = response.get('data', {})
        items = data_node.get('replies', [])
        
        # 如果某一页没有评论数据了，说明已经到底了，提前结束
        if not items:
            print("🏁 已经没有更多评论，爬取结束。")
            break
            
        # 2. 解析当前页面的评论
        for index in items:
            ctime = index['ctime']
            date = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
            
            reply_control = index.get('reply_control', {})
            location = reply_control.get('location', '未知')
            location = location.replace('IP属地：', '')
            
            dit = {
                '名字': index['member']['uname'],
                '性别': index['member']['sex'],
                '评论': index['content']['message'].strip(),
                '获赞': index['like'],
                '属地': location,
                '日期': date,
            }
            data.append(dit)
            print(f"  [第 {page_num} 页] 名字: {dit['名字']} | 属地: {dit['属地']}")
            
        # 3. 🔥 【核心多页逻辑】提取下一页所需的判定游标
        cursor_node = data_node.get('cursor', {})
        is_end = cursor_node.get('is_end', False)
        next_pagination = cursor_node.get('pagination_str')
        
        if is_end or not next_pagination:
            print("🏁 触发结束标记(is_end为True)，所有评论已全部加载完毕。")
            break
            
        # 4. 🔥 动态更新参数，把下一页的钥匙传给 params
        params['pagination_str'] = next_pagination
        
        # 5. 歇一口气，防止频率过快被封 IP
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ 解析第 {page_num} 页时发生非预期崩溃: {e}")
        break

# ======= 保存结果 =======
if data:
    df = pd.DataFrame(data)
    df.to_excel('bili_comments_multipage.xlsx', index=False)
    print(f"\n🎉 [大功告成] 共成功抓取并保存了 {len(data)} 条评论到 'bili_comments_multipage.xlsx'！")
else:
    print("\n😭 未能保存任何有效数据，请检查第一页是否就被拦截了。")