import asyncio
from playwright.async_api import async_playwright

async def get_links():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp('http://localhost:9222')
            context = browser.contexts[0]
            
            # Find the jobstreet page we just opened
            main_page = None
            for ctx in browser.contexts:
                for page in ctx.pages:
                    try:
                        if "jobstreet.com" in page.url and "/apply" not in page.url:
                            main_page = page
                    except:
                        pass
            
            if not main_page:
                print("No main page found")
                return
                
            print('Current page:', main_page.url)
            links = await main_page.locator('a').element_handles()
            print(f"Found {len(links)} a tags")
            
            for l in links[:150]:
                href = await l.get_attribute('href')
                if href and '/job/' in href:
                    title = await l.inner_text()
                    print(f'- {title.strip()} -> {href}')
            await browser.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(get_links())
