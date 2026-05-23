import json
import re
import os

def clean_legal_text(text):
    # Specialized junk filter for BSA
    junk_patterns = [
        r'Bill No\..*?LOK SABHA', 
        r'Page \d+', 
        r'SECTIONS', 
        r'—+', 
        r'THE BHARATIYA SAKSHYA ADHINIYAM, 2023'
    ]
    for pattern in junk_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Fix words split by newlines (e.g., "admissi- bility")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()

def ingest_bsa_guarded():
    # Update these paths to match your BSA files
    skeleton_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_index.json"
    raw_text_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_raw_text.txt"
    output_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_populated_final.json"

    if not os.path.exists(raw_text_path):
        print(f"❌ Error: {raw_text_path} not found.")
        return

    with open(skeleton_path, 'r', encoding='utf-8') as f:
        skeleton = json.load(f)
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    print(f"🚀 Starting BSA Ingestion (170 Sections)...")

    positions = []

    for i, entry in enumerate(skeleton):
        sec_num = str(entry["section_number"])
        title = entry.get("title")
        
        if not title:
            continue

        # Using the First 25 characters for a robust anchor
        clean_title_anchor = title.strip()[:25]
        pattern = rf"\n\s*{sec_num}\.\s+{re.escape(clean_title_anchor)}"
        
        match = re.search(pattern, full_text)
        if match:
            positions.append({
                "skeleton_index": i,
                "sec_num": sec_num,
                "content_start": match.end()
            })
        else:
            print(f"⚠️ Header not found for Section {sec_num}")

    # Slicing the content
    for k in range(len(positions)):
        curr = positions[k]
        skeleton_idx = curr["skeleton_index"]
        
        if k + 1 < len(positions):
            next_p = positions[k+1]
            next_title_anchor = skeleton[next_p["skeleton_index"]]["title"].strip()[:25]
            next_pattern = rf"\n\s*{next_p['sec_num']}\.\s+{re.escape(next_title_anchor)}"
            
            boundary_match = re.search(next_pattern, full_text[curr["content_start"]:])
            if boundary_match:
                end_index = curr["content_start"] + boundary_match.start()
            else:
                end_index = len(full_text)
        else:
            end_index = len(full_text)

        raw_content = full_text[curr["content_start"]:end_index]
        skeleton[skeleton_idx]["content"] = clean_legal_text(raw_content)
        print(f"✅ Section {curr['sec_num']} Ingested.")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(skeleton, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Done! Matched {len(positions)} out of {len(skeleton)} sections.")

if __name__ == "__main__":
    ingest_bsa_guarded()