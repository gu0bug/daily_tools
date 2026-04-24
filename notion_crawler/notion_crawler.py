import time
import re
import os
from playwright.sync_api import sync_playwright
import html2text

# ----------------- Configuration Parameters -----------------
# Replace with your actual Notion database URL and workspace domain
TARGET_URL = "https://your-workspace.notion.site/your-database-id?v=your-view-id"
DOMAIN_PREFIX = "https://your-workspace.notion.site"
OUTPUT_DIR = "./notebooklm_sources"
# ------------------------------------------------------------

def clean_filename(title):
    # Remove invalid characters for OS filenames
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()

def run_scraper():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.body_width = 0 
    h2t.bypass_tables = False

    # Extract the 32-character ID of the main page to exclude it from child page processing
    main_page_id_match = re.search(r'[a-f0-9]{32}', TARGET_URL.replace("-", ""), re.IGNORECASE)
    main_page_id = main_page_id_match.group(0) if main_page_id_match else ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print("[1/4] Accessing target Database page...")
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("div[data-block-id]", timeout=60000)
        time.sleep(3)

        print("[2/4] Executing physical mouse wheel scroll to force lazy loading...")
        # Move virtual mouse to the center of the screen
        page.mouse.move(960, 540)
        
        last_item_count = 0
        idle_count = 0
        
        # Assume bottom reached when no new data nodes are added
        while idle_count < 6:
            # Simulate high-frequency mouse scrolling downwards
            page.mouse.wheel(0, 4000)
            time.sleep(2) 
            
            # Count all 'a' tags with 'href' attributes as the judgment basis
            current_count = len(page.locator("a[href]").all())
            if current_count == last_item_count:
                idle_count += 1
            else:
                idle_count = 0
                last_item_count = current_count

        print("[3/4] Extracting child page IDs and reconstructing URLs...")
        all_hrefs = page.evaluate("Array.from(document.querySelectorAll('a')).map(a => a.getAttribute('href'))")
        target_urls = set()
        
        # Core characteristic of Notion page ID: 32-character hexadecimal string
        id_pattern = re.compile(r'[a-f0-9]{32}', re.IGNORECASE)
        
        for href in all_hrefs:
            if href and type(href) == str:
                # Remove hyphens to uniformly match the 32-character ID
                clean_href = href.replace("-", "")
                match = id_pattern.search(clean_href)
                
                if match:
                    found_id = match.group(0)
                    # Filter out the main page itself; process all other captured 32-character IDs as independent child pages
                    if found_id != main_page_id:
                        # Forcibly drop all parameters after '?'; assemble the cleanest direct full-screen route
                        target_urls.add(f"{DOMAIN_PREFIX}/{found_id}")

        print(f"Target queue built, accurately captured {len(target_urls)} child page nodes.")

        if len(target_urls) == 0:
            print("Failed to capture any child page links.")
            browser.close()
            return

        print("[4/4] Starting deep traversal scraping and Markdown conversion...")
        success_count = 0
        for index, url in enumerate(target_urls, 1):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for the child page body container to render
                page.wait_for_selector(".notion-page-content", timeout=15000)
                time.sleep(1) # Buffer for internal asynchronous text components
                
                raw_title = page.title()
                clean_title = clean_filename(raw_title.replace("- Notion", "").strip())
                
                content_html = page.locator(".notion-page-content").inner_html()
                markdown_content = h2t.handle(content_html)
                
                file_path = os.path.join(OUTPUT_DIR, f"{clean_title}.md")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# {clean_title}\n\n**Source URL**: {url}\n\n---\n\n{markdown_content}")
                
                success_count += 1
                print(f"[{index}/{len(target_urls)}] Successfully fetched: {clean_title}.md")
                
                time.sleep(1.5) 
                
            except Exception as e:
                print(f"[{index}/{len(target_urls)}] Exception fetching node {url} | Thrown: {str(e)}")

        browser.close()
        print(f"Task completed. Successfully exported {success_count} documents.")

if __name__ == "__main__":
    run_scraper()