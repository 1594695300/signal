import os, time
from playwright.sync_api import sync_playwright

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

        # 记录所有 API 请求，方便看登录发了什么
        api_logs = []
        def on_request(req):
            if "/api/" in req.url:
                api_logs.append(f"→ {req.method} {req.url}")
        def on_response(resp):
            if "/api/" in resp.url:
                api_logs.append(f"← {resp.status} {resp.url}")
        page.on("request", on_request)
        page.on("response", on_response)

        print("→ 打开登录页")
        page.goto("https://www.iios.me/#/login", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path="02_login.png")

        print("→ 填写账号密码")
        page.fill("input[type=email]", USERNAME)
        page.fill("input[type=password]", PASSWORD)
        page.wait_for_timeout(500)
        page.screenshot(path="03_filled.png")

        print("→ 点击登录按钮")
        # 先尝试常见选择器，找不到就打印所有 button 文字
        btn = None
        for sel in [
            "button[type=submit]",
            "button:has-text('登录')",
            "button:has-text('登 录')",
            ".login-btn",
        ]:
            try:
                el = page.query_selector(sel)
                if el:
                    btn = el
                    print(f"   命中按钮选择器: {sel}")
                    break
            except Exception:
                pass

        if not btn:
            print("   ⚠️ 没找到登录按钮，页面上的 button 有：")
            for b in page.query_selector_all("button"):
                print("   -", repr(b.inner_text()))
            browser.close()
            return

        btn.click()
        page.wait_for_timeout(5000)
        page.screenshot(path="04_after_login.png")
        print("   登录后 URL:", page.url)

        print("\n=== API 请求日志 ===")
        for line in api_logs:
            print(line)

        # 保存登录态
        ctx.storage_state(path="state.json")
        print("\n已保存 state.json")

        browser.close()

if __name__ == "__main__":
    run()
