# Notion-to-NotebookLM Data Pipeline

## 1. Overview
This project provides a two-step automated system to extract high-fidelity content from Notion databases (specifically when native export permissions are disabled) and aggregate the scattered data into chunked Markdown files optimized for Google's NotebookLM.

### 1.1 System Architecture
The system consists of two core modules that communicate via the local file system.

| Module | Tech Stack | Core Function |
| :--- | :--- | :--- |
| **Extraction (`notion_crawler.py`)** | Playwright (Chromium), `html2text` | Bypasses dynamic rendering, simulates physical scrolling, extracts UUIDs, and converts DOM content to pure Markdown. |
| **Aggregation (`merge_files.py`)** | Python File I/O, Regex | Merges fragmented files based on a word-count threshold and injects metadata anchors for better RAG performance. |

## 2. Prerequisites & Installation
* **Python Requirement:** Python 3.10 or higher.

Open your terminal and install the required dependencies:

```bash
# Install core Python libraries
pip install playwright html2text

# Install the Playwright Chromium browser binary
playwright install chromium
```

## 3. Usage Guide

### Step 1: Data Extraction
The scraper simulates human browsing behavior to bypass Notion's anti-scraping mechanisms and lazy-loading logic.

1. Open `notion_crawler.py` and configure your target variables:
   * `TARGET_URL`: The full URL of your Notion Database view.
   * `DOMAIN_PREFIX`: Your Notion workspace domain (e.g., `https://your-workspace.notion.site`).
2. Run the crawler:
   ```bash
   python notion_crawler.py
   ```
3. A browser window will open automatically. Do not close it. The script will scroll the page, extract all child pages, and save them as individual `.md` files in the `./notebooklm_sources` directory.

### Step 2: Data Aggregation
NotebookLM has a strict limit of 50 Sources per notebook. This module merges the hundreds of individual files into a few optimized chunks.

1. Ensure the `./notebooklm_sources` directory contains the scraped `.md` files.
2. Run the merger:
   ```bash
   python merge_files.py
   ```
3. The script will generate chunked files (e.g., `merged_source_part_1.md`) in the `./notebooklm_merged` directory. 
4. **Upload to NotebookLM:** Drag and drop the merged `.md` files directly into your NotebookLM project.

## 4. Key Features
* **Physical Scroll Simulation:** Uses `mouse.wheel` instead of standard JavaScript scrolling to effectively trigger Notion's strict lazy-loading containers.
* **UUID Extraction:** Scans the DOM for Notion's 32-character hexadecimal identifiers, ensuring 100% accurate child-page routing regardless of URL parameters.
* **Metadata Injection:** Automatically injects `# Source Document: [Title]` at the top of every merged section. This helps NotebookLM's AI explicitly cite the original Notion page when answering your queries.

## 5. Limitations & Troubleshooting
* **Rate Limiting:** Notion may temporarily block IP addresses that make requests too quickly. The script includes built-in `time.sleep()` delays to prevent this. Do not drastically reduce these sleep times.
* **Authentication:** This script relies on the data being publicly accessible or readable within the current browser context. It cannot scrape private databases without prior cookie injection or manual login during the browser's startup phase.
* **Word Count Limits:** NotebookLM supports a maximum of 500,000 words per source. `merge_files.py` defaults to a safe buffer of 400,000 words. Adjust the `MAX_WORDS_PER_FILE` variable if you encounter upload errors.