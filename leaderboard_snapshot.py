import asyncio
from playwright.async_api import async_playwright

async def capture_leaderboard(url, output_path="lb_snapshot.png"):
    """
    Launches a headless browser, navigates to the arena site,
    and takes a high-res crop of the leaderboard component.
    """
    async with async_playwright() as p:
        # 1. Launch Browser (Chromium)
        browser = await p.chromium.launch(headless=True)
        # Set a large enough viewport to capture the full list without scrolling
        page = await browser.new_page(viewport={'width': 1200, 'height': 1600})
        
        try:
            # 2. Go to the URL
            await page.goto(url, wait_until="networkidle")
            
            # 3. Wait for the API data to populate the rows
            # This ensures we don't snap a photo of an empty table
            await page.wait_for_selector(".lb-row", timeout=10000)
            
            # 4. Small buffer for CSS animations (shimmers) to initialize
            await asyncio.sleep(1.5)
            
            # 5. Target the specific leaderboard wrapper
            # This ignores the header/footer of the site for a clean Discord look
            element = await page.query_selector(".lb-wrap")
            
            if element:
                # Take the screenshot with a transparent background
                await element.screenshot(path=output_path, omit_background=True)
            else:
                # Fallback to full page if the selector fails
                await page.screenshot(path=output_path)
                
        except Exception as e:
            print(f"Playwright Error: {e}")
            raise e
        finally:
            await browser.close()
            
        return output_path
      
