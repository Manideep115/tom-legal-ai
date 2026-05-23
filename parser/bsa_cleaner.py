import json
import re
import os

def sanitize_bsa_content():
    input_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_populated_final.json"
    output_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_populated.json"

    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        sections = json.load(f)

    print("🧹 Starting Content Sanitization...")

    # Regex to match "CHAPTER" followed by Roman Numerals (e.g., CHAPTER X, CHAPTER IV)
    # This also looks for optional Part headings like "PART III"
    noise_pattern = re.compile(r'\s+(CHAPTER|PART)\s+[IVXLCDM]+\b.*', re.IGNORECASE)

    cleaned_count = 0

    for section in sections:
        content = section.get("content", "")
        
        if content:
            # Search for the noise pattern
            match = noise_pattern.search(content)
            
            if match:
                # Truncate the content at the start of the noise
                new_content = content[:match.start()].strip()
                section["content"] = new_content
                cleaned_count += 1
                print(f"✂️ Cleaned Section {section['section_number']}: Removed Chapter/Part noise.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Sanitization Complete!")
    print(f"📊 Total sections cleaned: {cleaned_count}")
    print(f"💾 Saved to: {output_file}")

if __name__ == "__main__":
    sanitize_bsa_content()