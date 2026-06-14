import requests
import time
from datetime import datetime
import pandas as pd
import os

def trans_date(v_timestamp):
    """10位时间戳转换为时间字符串"""
    v_timestamp = float(v_timestamp)
    timeArray = time.localtime(v_timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime

def fecth_everything(comment):
    """解析单条评论的所有要素"""
    # ✨ 【新增提取】用户唯一数字 ID (mid)
    user_id = comment["member"]["mid"]
    # 用户名
    username = comment["member"]["uname"]
    # 性别
    gender = comment["member"]["sex"]
    # 评论的时间
    time_un = comment["ctime"]
    publish_time = trans_date(time_un)
    
    # 评论的IP属地（安全容错判断）
    if "location" in comment.get("reply_control", {}):
        IP = comment["reply_control"]["location"].replace("IP属地：", "")
    else:
        IP = "未知"
        
    # 评论的内容（顺便清理掉内容里的换行，方便表格单行展示）
    content = comment["content"]["message"].strip().replace('\n', ' ')
    # 评论的点赞数
    num = comment["like"]

    return user_id, username, gender, publish_time, IP, content, num

def fetch_comments(video_bv, headers, max_pages):
    # 用一个列表来装所有抓取到的字典数据，后续一键转为表格
    all_comments_list = []

    for page in range(1, max_pages + 1):
        # 保持你测试成功的原装老接口路径不变
        url = f'https://api.bilibili.com/x/v2/reply/main?next={page}&type=1&oid={video_bv}&mode=3'
        print(f"📡 正在抓取: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 第 {page} 页已获取完毕！")
                
                # 检查数据包是否为空
                if data.get('data') is None or data['data'].get('replies') is None:
                    print("🏁 已经到达评论区末尾，没有更多数据。")
                    break
                    
                for comment in data['data']['replies']:
                    # 1. 抓取主评论并追加
                    user_id, username, gender, publish_time, IP, content, num = fecth_everything(comment)
                    all_comments_list.append({
                        "User_ID": user_id, "User_Name": username, "Gender": gender,
                        "Publish_Time": publish_time, "IP_Location": IP, "Content": content, "Likes": num
                    })

                    # 2. 抓取楼中楼（子评论）并追加
                    if comment.get("replies"):
                        for child in comment["replies"]:
                            c_user_id, c_username, c_gender, c_publish_time, c_IP, c_content, c_num = fecth_everything(child)
                            all_comments_list.append({
                                "User_ID": c_user_id, "User_Name": c_username, "Gender": c_gender,
                                "Publish_Time": c_publish_time, "IP_Location": c_IP, "Content": c_content, "Likes": c_num
                            })
            else:
                print(f"❌ 网页状态码异常: {response.status_code}")
                break
                
        except requests.RequestException as e:
            print(f"请求出错: {e}")
            break
            
        # 控制请求频率
        time.sleep(2)
        
    return all_comments_list

# ==================== 运行控制台 ====================
if __name__ == "__main__":
    video_bv = input("请输入Bvid号/或者Oid号：").strip()
    user_agent = input("请输入 User-Agent：").strip()
    cookie = input("请输入 Cookie：").strip()
    
    headers = {
        'User-Agent': user_agent,
        'Cookie': cookie
    }
    
    # 执行抓取
    max_pages_to_crawl = 40
    parsed_data = fetch_comments(video_bv=video_bv, headers=headers, max_pages=max_pages_to_crawl)
    
    # ======= ✨ 【核心变化】在这里统一生成 Excel 表格 =======
    if parsed_data:
        # 创建一个单独的数据存放文件夹
        os.makedirs('./crawledData', exist_ok=True)
        excel_filename = './crawledData/bilibili_comments.xlsx'
        
        # 使用 Pandas 把提取的列表洗成 DataFrame 结构
        df = pd.DataFrame(parsed_data)
        
        # 统一和规范一下列的左右摆放顺序
        columns_order = ["User_ID", "User_Name", "Gender", "Publish_Time", "IP_Location", "Content", "Likes"]
        df = df[columns_order]
        
        # 导出为 Excel 电子表格，并且不保留行索引
        df.to_excel(excel_filename, index=False)
        print(f"\n🎉 [大功告成] 数据已完美保存！共采集 {len(parsed_data)} 条评论（含子评论），表格已生成至: {excel_filename}")
    else:
        print("\n😭 本次未采集到任何有效数据。")