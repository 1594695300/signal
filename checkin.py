import os
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
        browser = p.webkit.launch(headless=True)

        ctx = browser.new_context(
            user_agent=IPHONE_UA,
            viewport={"width": 390, "height": 844},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # 补 iOS Safari 专有特征，防止被环境检测拦
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'platform', {
                get: () => 'iPhone'
            });
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Apple Computer, Inc.'
            });
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 5
            });
            window.webkit = window.webkit || {};
            window.webkit.messageHandlers = window.webkit.messageHandlers || {};
        """)

        page = ctx.new_page()

        # 记录 API 请求
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
        page.goto(
            "https://www.iios.me/#/login",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(3000)
        page.screenshot(path="02_login.png")

        print("→ 填写账号密码")
        page.fill("input[type=email]", USERNAME)
        page.fill("input[type=password]", PASSWORD)
        page.wait_for_timeout(500)
        page.screenshot(path="03_filled.png")

        print("→ 点击登录按钮")
        try:
            page.get_by_role("button", name="提交登录").click(timeout=5000)
            print("   已点击「提交登录」")
        except Exception as e:
            print("   按文字没点到，改用选择器:", e)
            page.click("button[type=submit]")

        page.wait_for_timeout(5000)
        page.screenshot(path="04_after_login.png")
        print("   登录后 URL:", page.url)

        print("\n=== API 请求日志 ===")
        for line in api_logs:
            print(line)

        ctx.storage_state(path="state.json")
        print("\n已保存 state.json")

        browser.close()


if __name__ == "__main__":
    run()
