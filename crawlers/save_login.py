import asyncio
from playwright.async_api import async_playwright

async def save_bilibili_cookie():
    async with async_playwright() as p:
        # 必须开启 headless=False，否则你看不到二维码
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 1. 直接前往B站登录页面
        print("🌐 正在打开 B 站登录页面...")
        await page.goto("https://passport.bilibili.com/login")
        
        print("📸 请在弹出的浏览器中，使用手机B站App扫描屏幕上的二维码进行登录！")
        print("⏳ 爬虫正在等待你登录成功...（限时 60 秒）")
        
        # 2. 监控页面，直到右上角出现用户头像（说明登录成功了）
        # B站右上角头像的类名通常包含 header-entry-mini 或者 .header-avatar-wrap
        try:
            # 动态等待头像加载，超时时间设为 60 秒
            await page.wait_for_selector(".header-avatar-wrap", timeout=60000)
            print("🎉 检测到用户头像，登录成功！")
            
            # 3. 核心：把当前浏览器的所有 Cookies 保存到本地文件
            cookies = await context.cookies()
            import json
            with open("cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=4)
            print("💾 成功将登录凭证保存至本地 `cookies.json` 文件！")
            
        except Exception as e:
            print("❌ 登录超时或失败，未检测到成功登录状态。")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_bilibili_cookie())