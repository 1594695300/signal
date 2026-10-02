import os
from playwright.sync_api import sync_playwright

USERNAME = os.environ["IIOS_USERNAME"]
PASSWORD = os.environ["IIOS_PASSWORD"]

UA_WIN_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        ctx = browser.new_context(
            user_agent=UA_WIN_CHROME,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # 反检测：抹掉 Playwright / 自动化痕迹
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5].map(i => ({ name: 'Plugin ' + i }))
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });

            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );
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
