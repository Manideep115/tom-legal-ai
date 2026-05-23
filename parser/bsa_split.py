import json
import re
import os

def clean_bsa_text(text):
    # Specialized junk filter for the BSA PDF
    junk_patterns = [
        r'Bill No\..*?LOK SABHA', 
        r'Page \d+', 
        r'SECTIONS', 
        r'—+', 
        r'THE BHARATIYA SAKSHYA ADHINIYAM, 2023',
        r'ARRANGEMENT OF SECTIONS'
    ]
    for pattern in junk_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Fix hyphenated words at line breaks
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()

def ingest_bsa_with_dash():
    skeleton_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_index.json"
    raw_text_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_raw_text.txt"
    output_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_populated_final.json"

    with open(skeleton_path, 'r', encoding='utf-8') as f:
        skeleton = json.load(f)
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    print(f"🚀 Ingesting 170 BSA Sections using Dash-Anchor logic...")

    positions = []

    for i, entry in enumerate(skeleton):
        sec_num = str(entry["section_number"])
        title = entry.get("title").strip()
        
        # PATTERN: Newline + Optional Spaces + Number + Dot + Title + Dash
        # Example: "\n1. Short title, application and commencement.—"
        anchor_pattern = rf"\n\s*{sec_num}\.\s+{re.escape(title)}\s*—"
        
        match = re.search(anchor_pattern, full_text)
        
        if match:
            positions.append({
                "skeleton_index": i,
                "sec_num": sec_num,
                "title": title,
                "content_start": match.end() # Start right AFTER the dash
            })
        else:
            # Fallback: Try without the dash just in case one section is missing it
            fallback = rf"\n\s*{sec_num}\.\s+{re.escape(title)}"
            match = re.search(fallback, full_text)
            if match:
                 positions.append({
                    "skeleton_index": i,
                    "sec_num": sec_num,
                    "title": title,
                    "content_start": match.end()
                })
            else:
                print(f"⚠️ Header not found for Section {sec_num}")

    # Slicing the content between anchors
    for k in range(len(positions)):
        curr = positions[k]
        
        if k + 1 < len(positions):
            next_p = positions[k+1]
            # The next section's header is where we stop
            next_anchor = rf"\n\s*{next_p['sec_num']}\.\s+{re.escape(next_p['title'])}"
            
            boundary_match = re.search(next_anchor, full_text[curr["content_start"]:])
            if boundary_match:
                end_index = curr["content_start"] + boundary_match.start()
            else:
                end_index = len(full_text)
        else:
            end_index = len(full_text)

        raw_content = full_text[curr["content_start"]:end_index]
        skeleton[curr["skeleton_index"]]["content"] = clean_bsa_text(raw_content)
        print(f"✅ Section {curr['sec_num']} Ingested.")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(skeleton, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Done! Matched {len(positions)} out of {len(skeleton)} sections.")

if __name__ == "__main__":
    ingest_bsa_with_dash()