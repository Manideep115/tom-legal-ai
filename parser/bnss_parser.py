import json
import re
import os

def clean_legal_text(text):
    # Strip PDF artifacts: Headers, Footers, and Page Numbers
    text = re.sub(r'Bill No\..*?LOK SABHA|Page \d+|CLAUSES|—+|BHARATIYA NAGARIK SURAKSHA SANHITA', '', text, flags=re.IGNORECASE)
    # Fix words split by newlines (e.g., "punish- ment")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()

def ingest_bnss_by_pattern():
    skeleton_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_flat.json"
    raw_text_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_raw_text.txt"
    output_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_populated_final.json"

    with open(skeleton_path, 'r', encoding='utf-8') as f:
        skeleton = json.load(f)
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    print("🚀 Starting Guarded Pattern-Based Ingestion...")

    # First, let's find the start position of every section in the text
    # We store them in a list of dicts: {'sec_num': '1', 'start': 500, 'end': 1200}
    positions = []

    for i, entry in enumerate(skeleton):
        sec_num = str(entry["section_number"])
        title = entry.get("title")
        
        if not title:
            print(f"⚠️ Skipping Section {sec_num} - Title is missing in JSON!")
            continue

        # Pattern: Newline, Space, Number, Dot, Space, Title
        clean_title = title.strip()
        pattern = rf"\n\s*{sec_num}\.\s+{re.escape(clean_title)}"
        
        match = re.search(pattern, full_text)
        if match:
            positions.append({
                "skeleton_index": i,
                "sec_num": sec_num,
                "content_start": match.end()
            })

    # Now, slice the text between these positions
    for k in range(len(positions)):
        curr = positions[k]
        
        # The end of this section is the start of the NEXT matched section's header
        if k + 1 < len(positions):
            next_pos = positions[k+1]
            # We need to find the beginning of the next header again
            # to make sure we don't include the header in the previous section's content
            next_title = skeleton[next_pos["skeleton_index"]]["title"].strip()
            next_pattern = rf"\n\s*{next_pos['sec_num']}\.\s+{re.escape(next_title)}"
            
            boundary_match = re.search(next_pattern, full_text[curr["content_start"]:])
            if boundary_match:
                end_index = curr["content_start"] + boundary_match.start()
            else:
                end_index = len(full_text)
        else:
            end_index = len(full_text)

        raw_content = full_text[curr["content_start"]:end_index]
        skeleton[curr["skeleton_index"]]["content"] = clean_legal_text(raw_content)
        print(f"✅ Section {curr['sec_num']} Ingested.")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(skeleton, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Done! Results saved to: {output_path}")

if __name__ == "__main__":
    ingest_bnss_by_pattern()