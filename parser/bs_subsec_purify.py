import json
import os

def purify_subsections():
    # Update this to your local path
    file_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_summarized.json"
    
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned_total = 0

    for section in data:
        if "subsections" in section and isinstance(section["subsections"], list):
            # Keep only subsections that have actual content and aren't error flags
            original_count = len(section["subsections"])
            
            section["subsections"] = [
                sub for sub in section["subsections"]
                if sub.get("text") and 
                sub["text"].strip() not in ["", "null", "Parsing failed.", "None"]
            ]
            
            cleaned_total += (original_count - len(section["subsections"]))

    # Save the cleaned data back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✨ Purification Complete!")
    print(f"🗑️ Removed {cleaned_total} empty or corrupted subsections.")

if __name__ == "__main__":
    purify_subsections()