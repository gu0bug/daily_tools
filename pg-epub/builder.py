import os
import re
import json
import html
import uuid
import zipfile
import urllib.request
from datetime import datetime

# Configurations
URL = "https://pg.imwsl.com/"
LOCAL_FALLBACK_HTML = r"C:\Users\小喵喵\.gemini\antigravity\brain\65da631a-cb6e-40ad-a0ea-1e2bfc04a905\.system_generated\steps\3\content.md"
COVER_IMAGE_SRC = "cover.png"
OUTPUT_EPUB = "paul_graham_essays_bilingual.epub"

def fetch_data():
    """Fetch website HTML and parse the script block containing all articles."""
    html_content = ""
    print(f"Fetching from {URL}...")
    try:
        req = urllib.request.Request(
            URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html_content = response.read().decode('utf-8')
        print("Successfully fetched live site.")
    except Exception as e:
        print(f"Failed to fetch live site: {e}")
        if os.path.exists(LOCAL_FALLBACK_HTML):
            print(f"Falling back to local cache file: {LOCAL_FALLBACK_HTML}")
            with open(LOCAL_FALLBACK_HTML, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            raise Exception("No data source available.")

    # Match JSON script block
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html_content, re.DOTALL)
    if not match:
        raise Exception("Could not locate the JSON data block in the HTML content.")
    
    data = json.loads(match.group(1))
    print(f"Parsed {len(data)} essays successfully.")
    return data

def clean_text(text):
    """Remove HTML comments and trim whitespaces."""
    if not text:
        return ""
    # Strip HTML comments (including unclosed comments)
    text = re.sub(r'<!--.*?(?:-->|$)', '', text, flags=re.DOTALL)
    return text.strip()

def process_paragraph(p_dict):
    """Formats a paragraph pair into XHTML compatible markup."""
    en_text = clean_text(p_dict.get("en", ""))
    zh_text = clean_text(p_dict.get("zh", ""))
    
    if not en_text and not zh_text:
        return ""
    
    # Split by double newlines or more (for paragraphs embedded in single paragraph entries)
    en_chunks = [c.strip() for c in re.split(r'\n{2,}', en_text) if c.strip()]
    zh_chunks = [c.strip() for c in re.split(r'\n{2,}', zh_text) if c.strip()]
    
    processed_en = []
    for chunk in en_chunks:
        # replace single newlines with space
        chunk_clean = re.sub(r'\s*\n\s*', ' ', chunk)
        processed_en.append(chunk_clean)
        
    processed_zh = []
    for chunk in zh_chunks:
        # For Chinese newlines: if between CJK characters, merge without space, otherwise with space
        chunk_clean = re.sub(r'([\u4e00-\u9fff])\s*\n\s*([\u4e00-\u9fff])', r'\1\2', chunk)
        chunk_clean = re.sub(r'\s*\n\s*', ' ', chunk_clean)
        processed_zh.append(chunk_clean)
        
    html_out = []
    max_len = max(len(processed_en), len(processed_zh))
    for i in range(max_len):
        html_out.append('      <div class="para-pair">')
        if i < len(processed_en):
            html_out.append(f'        <p class="en">{html.escape(processed_en[i])}</p>')
        if i < len(processed_zh):
            html_out.append(f'        <p class="zh">{html.escape(processed_zh[i])}</p>')
        html_out.append('      </div>')
        
    return "\n".join(html_out)

def build_epub():
    essays = fetch_data()
    
    # Reverse essays order to chronological (oldest first)
    essays.reverse()
    print("Reversed essays to chronological order (oldest first).")

    # Generate Book UUID
    book_uuid = str(uuid.uuid4())
    current_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    # Start writing EPUB ZIP
    with zipfile.ZipFile(OUTPUT_EPUB, 'w', zipfile.ZIP_DEFLATED) as epub:
        # 1. mimetype (must be first, uncompressed)
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        container_xml = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        epub.writestr('META-INF/container.xml', container_xml)

        # 3. OEBPS/styles.css
        styles_css = '''body {
  font-family: Georgia, serif;
  margin: 1em 1.5em;
  line-height: 1.5;
  color: #111111;
}

h1.book-title {
  text-align: center;
  font-size: 2em;
  margin-top: 2em;
  margin-bottom: 0.5em;
  color: #8a3324;
}

p.book-author {
  text-align: center;
  font-size: 1.2em;
  color: #555555;
  margin-bottom: 3em;
}

h1.chapter-title {
  font-size: 1.5em;
  line-height: 1.3;
  margin-top: 1.5em;
  margin-bottom: 0.3em;
  color: #8a3324;
  border-bottom: 1px solid #e6e3dc;
  padding-bottom: 0.3em;
}

.original-link {
  font-size: 0.85em;
  margin-bottom: 2em;
  color: #777777;
  font-family: -apple-system, sans-serif;
}

.original-link a {
  color: #8a3324;
  text-decoration: none;
}

.para-pair {
  margin-bottom: 1.5em;
}

.en {
  margin: 0 0 0.3em 0;
  color: #1a1a1a;
  font-size: 1.05em;
  line-height: 1.5;
}

.zh {
  margin: 0;
  color: #444444;
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  font-size: 0.95em;
  line-height: 1.6;
  opacity: 0.85;
}

nav ol {
  list-style-type: none;
  padding-left: 0;
}

nav li {
  margin-bottom: 0.5em;
  line-height: 1.4;
}

nav a {
  text-decoration: none;
  color: #8a3324;
}
'''
        epub.writestr('OEBPS/styles.css', styles_css)

        # 4. OEBPS/cover.png
        if os.path.exists(COVER_IMAGE_SRC):
            print(f"Packaging cover image from {COVER_IMAGE_SRC}...")
            epub.write(COVER_IMAGE_SRC, 'OEBPS/cover.png')
        else:
            print("Warning: Cover image not found, skipping image package.")

        # 5. OEBPS/cover.xhtml
        cover_xhtml = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head>
  <title>Cover</title>
  <style type="text/css">
    body { margin: 0; padding: 0; text-align: center; background-color: #ffffff; }
    img { max-width: 100%; height: auto; }
  </style>
</head>
<body>
  <div style="text-align: center; padding: 0; margin: 0;">
    <img src="cover.png" alt="Book Cover" />
  </div>
</body>
</html>'''
        epub.writestr('OEBPS/cover.xhtml', cover_xhtml)

        # Build Chapters and Manifest
        manifest_items = []
        spine_items = []
        ncx_points = []
        nav_links = []

        # Add Cover and Navigation files to OPF and NCX listings
        manifest_items.append('<item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image" />')
        manifest_items.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml" />')
        manifest_items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />')
        manifest_items.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />')
        manifest_items.append('<item id="styles" href="styles.css" media-type="text/css" />')

        spine_items.append('<itemref idref="cover" linear="yes" />')
        spine_items.append('<itemref idref="nav" linear="yes" />')

        ncx_points.append('''    <navPoint id="navpoint-cover" playOrder="1">
      <navLabel><text>Cover</text></navLabel>
      <content src="cover.xhtml"/>
    </navPoint>''')
        ncx_points.append('''    <navPoint id="navpoint-nav" playOrder="2">
      <navLabel><text>Table of Contents</text></navLabel>
      <content src="nav.xhtml"/>
    </navPoint>''')

        nav_links.append('      <li><a href="cover.xhtml">Cover</a></li>')
        nav_links.append('      <li><a href="nav.xhtml">Table of Contents / 目录</a></li>')

        # Format and write chapters
        for idx, essay in enumerate(essays, 1):
            ch_id = f"ch_{idx:03d}"
            ch_filename = f"chapters/chapter_{idx:03d}.xhtml"
            
            title = essay.get("title", f"Essay {idx}")
            orig_url = essay.get("url", "https://www.paulgraham.com/")
            paras = essay.get("paras", [])

            # Compile chapter HTML
            paras_xhtml = []
            for p in paras:
                p_markup = process_paragraph(p)
                if p_markup:
                    paras_xhtml.append(p_markup)
            
            paras_xhtml_str = "\n".join(paras_xhtml)
            chapter_content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN" lang="zh-CN">
<head>
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="../styles.css" type="text/css" />
</head>
<body>
  <section class="chapter" epub:type="chapter">
    <h1 class="chapter-title">{html.escape(title)}</h1>
    <div class="original-link"><a href="{html.escape(orig_url)}">Original Essay: {html.escape(orig_url)}</a></div>
    <div class="content">
{paras_xhtml_str}
    </div>
  </section>
</body>
</html>'''
            epub.writestr(f"OEBPS/{ch_filename}", chapter_content)
            print(f"Wrote OEBPS/{ch_filename}: {title}")

            # Manifest & Spine lists
            manifest_items.append(f'<item id="{ch_id}" href="{ch_filename}" media-type="application/xhtml+xml" />')
            spine_items.append(f'<itemref idref="{ch_id}" linear="yes" />')

            # NCX & Nav lists
            play_order = idx + 2
            ncx_points.append(f'''    <navPoint id="navpoint-{idx}" playOrder="{play_order}">
      <navLabel><text>{html.escape(title)}</text></navLabel>
      <content src="{ch_filename}"/>
    </navPoint>''')
            nav_links.append(f'      <li><a href="{ch_filename}">{html.escape(title)}</a></li>')

        # 6. OEBPS/toc.ncx
        ncx_points_str = "\n".join(ncx_points)
        ncx_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{book_uuid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>Paul Graham Essays (Bilingual Edition) / 保罗·格雷厄姆文集 (中英对照)</text>
  </docTitle>
  <navMap>
{ncx_points_str}
  </navMap>
</ncx>'''
        epub.writestr('OEBPS/toc.ncx', ncx_xml)

        # 7. OEBPS/nav.xhtml
        nav_links_str = "\n".join(nav_links)
        nav_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN" lang="zh-CN">
<head>
  <title>目录 / Table of Contents</title>
  <link rel="stylesheet" href="styles.css" type="text/css" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1 class="chapter-title">目录 / Table of Contents</h1>
    <ol>
{nav_links_str}
    </ol>
  </nav>
</body>
</html>'''
        epub.writestr('OEBPS/nav.xhtml', nav_xhtml)

        # 8. OEBPS/content.opf
        manifest_items_str = "\n".join("    " + item for item in manifest_items)
        spine_items_str = "\n".join("    " + item for item in spine_items)
        opf_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0" prefix="rendition: http://www.idpf.org/2007/opf/features/rendition/">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Paul Graham Essays (Bilingual Edition) / 保罗·格雷厄姆文集 (中英对照)</dc:title>
    <dc:creator id="creator">Paul Graham</dc:creator>
    <dc:language>en</dc:language>
    <dc:language>zh-CN</dc:language>
    <dc:identifier id="bookid">urn:uuid:{book_uuid}</dc:identifier>
    <dc:publisher>pg.imwsl.com / Antigravity EPUB Builder</dc:publisher>
    <dc:date>{current_date}</dc:date>
    <meta property="dcterms:modified">{current_date}</meta>
    <meta name="cover" content="cover-image" />
  </metadata>
  <manifest>
{manifest_items_str}
  </manifest>
  <spine toc="ncx">
{spine_items_str}
  </spine>
</package>'''
        epub.writestr('OEBPS/content.opf', opf_xml)

    print(f"\nEPUB Generation Complete: {OUTPUT_EPUB}")

if __name__ == '__main__':
    build_epub()
