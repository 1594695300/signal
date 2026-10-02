import os, time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

USERNAME = os.environ["IIOS_USERNAME"]
PASSWORD = os.environ["IIOS_PASSWORD"]

IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=IPHONE_UA,
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = ctx.new_page()

        print("→ 打开首页")
        page.goto("https://www.iios.me/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path="01_home.png")
        print("标题:", page.title())
        print("URL:", page.url)

        # 检测是否被 Cloudflare 拦
        html = page.content()
        if "cf-challenge" in html or "Just a moment" in html or "Checking your browser" in html:
            print("❌ 被 Cloudflare 拦截")
            page.screenshot(path="cf_block.png")
            browser.close()
            return

        print("→ 打开登录页")
        page.goto("https://www.iios.me/#/login", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path="02_login.png")

        # 打印页面里所有输入框，方便定位
        inputs = page.query_selector_all("input")
        print(f"找到 {len(inputs)} 个输入框:")
        for i, el in enumerate(inputs):
            print(f"  [{i}] type={el.get_attribute('type')!r} "
                  f"name={el.get_attribute('name')!r} "
                  f"placeholder={el.get_attribute('placeholder')!r}")

        print("✅ 到这里说明能打开登录页，下一步根据输入框信息填账号密码")
        browser.close()

if __name__ == "__main__":
    run()
