import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        locators = await page.locator("p").all()
        print(len(locators))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
