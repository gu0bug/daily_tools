import os
import re

# --- Configuration Parameters ---
SOURCE_DIR = "./notebooklm_sources"  # Directory containing exported markdown files
OUTPUT_DIR = "./notebooklm_merged"   # Directory for merged output
MAX_WORDS_PER_FILE = 400000          # Max words per merged file (400k recommended for buffer)
# --------------------------------

def clean_markdown(content):
    """Remove redundant blank lines and potential invalid characters."""
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()

def merge_markdown_files():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.md')]
    files.sort() # Sort by filename to maintain logical sequence

    current_file_index = 1
    current_word_count = 0
    merged_content = []

    def save_chunk(index, content_list):
        output_path = os.path.join(OUTPUT_DIR, f"merged_source_part_{index}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(content_list))
        print(f"Generated merged file: {output_path}")

    for filename in files:
        file_path = os.path.join(SOURCE_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Inject metadata anchors to help identify context source
        title = filename.replace(".md", "")
        formatted_section = f"# Source Document: {title}\n\n{clean_markdown(content)}\n\n---\n"
        
        # Estimate word count (spaces for English, characters for Chinese)
        word_count = len(formatted_section.split()) + len(re.findall(r'[\u4e00-\u9fa5]', formatted_section))
        
        if current_word_count + word_count > MAX_WORDS_PER_FILE:
            save_chunk(current_file_index, merged_content)
            current_file_index += 1
            merged_content = []
            current_word_count = 0
            
        merged_content.append(formatted_section)
        current_word_count += word_count

    if merged_content:
        save_chunk(current_file_index, merged_content)

if __name__ == "__main__":
    merge_markdown_files()