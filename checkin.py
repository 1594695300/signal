import os, json, time
from playwright.sync_api import sync_playwright

STORAGE = json.loads(os.environ["STORAGE_STATE"])

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        storage_state=STORAGE,
        viewport={"width": 390, "height": 844},
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"),
    )
    page = ctx.new_page()
    page.goto("https://www.iios.me/", wait_until="networkidle")
    page.screenshot(path="home.png")

    # 待定：找签到按钮 / 入口
    print("标题:", page.title())
    print(page.content()[:1000])

    browser.close()
