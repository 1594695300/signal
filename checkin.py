import os
import sys
import io
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

        # Anti-detection: hide Playwright / automation traces
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

        # Log API requests
        api_logs = []

        def on_request(req):
            if "/api/" in req.url:
                api_logs.append(f"-> {req.method} {req.url}")

        def on_response(resp):
            if "/api/" in resp.url:
                api_logs.append(f"<- {resp.status} {resp.url}")

        page.on("request", on_request)
        page.on("response", on_response)

        print("Open login page")
        page.goto(
            "https://www.iios.me/#/login",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(3000)
        page.screenshot(path="02_login.png")

        print("Fill email / password")
        page.fill("input[type=email]", USERNAME)
        page.fill("input[type=password]", PASSWORD)
        page.wait_for_timeout(500)
        page.screenshot(path="03_filled.png")

        print("Click login button")
        try:
            page.get_by_role("button", name="\u63d0\u4ea4\u767b\u5f55").click(timeout=5000)
            print("   clicked submit button")
        except Exception as e:
            print("   text locator failed, fallback to selector:", e)
            page.click("button[type=submit]")

        page.wait_for_timeout(5000)
        page.screenshot(path="04_after_login.png")
        print("   URL after login:", page.url)

        print("\n=== API log ===")
        for line in api_logs:
            print(line)

        ctx.storage_state(path="state.json")
        print("\nstate.json saved")

        browser.close()


if __name__ == "__main__":
    run()
