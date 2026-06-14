import os
import time
import pandas as pd
import requests
import re
import json

# 全局变量
com = []
pdData = pd.DataFrame()
max_page = 10  # 默认爬取页数上限，一页20条数据

def require(url, current_headers):
    try:
        r = requests.get(url, headers=current_headers, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"❌ 接口请求失败: {e}")
        return None


def Html(html):
    try:
        s = json.loads(html)
        
        # 检查 B 站返回的状态码
        if s.get('code') != 0:
            print(f" ⚠️ B站接口返回异常! 错误码: {s.get('code')}, 原因: {s.get('message')}")
            return False
            
        data = s.get('data', {})
        replies = data.get('replies')
        
        # 如果当前页完全没有评论数据了，说明真的到底了
        if not replies or len(replies) == 0:
            return False
            
        for comment in replies:
            floor = comment['member']['mid']
            username = comment['member']['uname']
            ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(comment['ctime']))
            content = comment['content']['message']
            
            # 清洗一下评论里的换行，方便 Excel 排版
            content = content.replace('\n', ' ').strip()
            
            item = [floor, username, content, ctime]
            print(f"  [已抓取] 用户: {username} -> {content[:15]}...")
            com.append(item)
        return True
    except Exception as e:
        print(f"❌ 解析 JSON 数据包时出错: {e}")
        return False


def save_afile(alls, filename):
    global pdData
    columns = ['Comment_ID', 'Comment_Name', 'Comment_Content', 'Comment_Time']
    df = pd.DataFrame(alls, columns=columns)
    
    output_dir = r'./crawledData'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    excel_path = os.path.join(output_dir, f"{filename}.xlsx")
    try:
        df.to_excel(excel_path, index=False)
        print(f"\n🎉 采集结束！本次共成功抓取 {len(alls)} 条评论。")
        print(f"💾 数据已妥善保存至: {excel_path}")
        pdData = pd.read_excel(excel_path)
    except PermissionError:
        print(f"\n❌ 保存失败！请检查文件 {excel_path} 是否正被 Excel/WPS 打开？请将其关闭后再试。")


def getOidAndBvid(url, current_headers):
    # 提取以 video/ 开头后面跟随的 BV 号
    bv_match = re.search(r'video/(BV[a-zA-Z0-9]+)', url)
    if not bv_match:
        raise ValueError("无法从网址中识别出合法的 BV 号！")
        
    bv = bv_match.group(1)
    print(f"🔍 成功截取视频号 (Bvid): {bv}")
    
    # 用你指定的 Headers 访问视频主页以抓取内部数字 ID (aid/oid)
    resp = requests.get(f"https://www.bilibili.com/video/{bv}", headers=current_headers, timeout=10)
    
    aid_match = re.search(r'"aid":(\d+)', resp.text)
    if aid_match:
        return aid_match.group(1), bv
        
    raise ValueError("未能获取到 Oid(aid)，可能是 Cookie 粘贴不完整或已被拦截。")


def BilibiliCrawler(url, input_cookie):
    global com
    com = []  # 清空缓存
    
    # 动态构建本次运行的绝对真实 Headers (已嵌入你提供的 Edge UA)
    current_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
        'cookie': input_cookie.strip(),
        'Origin': 'https://www.bilibili.com',
        'Referer': url
    }
    
    try:
        oid, bvid = getOidAndBvid(url, current_headers)
    except Exception as e:
        print(f"❌ 初始化视频参数报错: {e}")
        return None
        
    print(f"🚀 关联 Oid 成功: {oid} | 开始跨页拉取...")
    
    # 使用你原本最稳的 reply 接口路径
    Old_url = 'https://api.bilibili.com/x/v2/reply?type=1&sort=1&oid=' + str(oid) + '&pn='
    
    page = 1
    while page <= max_page:
        current_url = Old_url + str(page)
        print(f"\n正在请求第 {page} 页评论...")
        
        html = require(current_url, current_headers)
        if not html:
            break
            
        has_next = Html(html)
        if not has_next:
            print("💡 提示：此页无更多新评论或触发高频风控，已自动终止爬取。")
            break
            
        page += 1
        print("☕ 触发安全缓冲，休息 3 秒...")
        time.sleep(3)  # 原版 3 秒间歇
            
    save_afile(com, bvid)
    return pdData


# ==========================================
# 3. 终端可执行控制台入口
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    print("         Bilibili 评论全自动本地抓取控制台 (UA固定版)")
    print("=" * 60)
    
    # 依次获取你的最新鲜的人工数据
    user_url = input("1. 请输入你想爬取的 B 站视频网址：\n> ").strip()
    user_cookie = input("\n2. 请输入你当前浏览器 F12 复制的 Cookie：\n> ").strip()
    
    if user_url and user_cookie:
        BilibiliCrawler(user_url, user_cookie)
    else:
        print("❌ 错误：网址或 Cookie 不能为空，程序退出。")
        
    print("=" * 60)
    input("执行完毕，按【回车键】即可退出当前控制台...")