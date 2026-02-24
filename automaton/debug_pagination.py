import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    async with async_playwright() as pw:
        # We can run headless for a quick debug
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://id.jobstreet.com/id/job-search/guru-jobs/in-jakarta/?where=Jakarta", wait_until="domcontentloaded")
        await page.wait_for_selector('article[data-automation="normalJob"]', timeout=10000)
        
        # Test get_by_role
        nxt = page.get_by_role("link", name=re.compile(r"(Selanjutnya|Next)", re.IGNORECASE))
        print(f"Role Link count: {await nxt.count()}")
        
        if await nxt.count() > 0:
            print("Next button found with get_by_role!")
            print("HTML:", await nxt.first.evaluate("el => el.outerHTML"))
            await nxt.first.click()
            print("Clicked Next")
            try:
                # wait for page 2
                await page.wait_for_url(re.compile(r"page=2"), timeout=5000)
                print(f"Navigated to {page.url}")
            except Exception as e:
                print(f"Timeout waiting for URL change: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
