import json
import os

def merge_legal_acts():
    # Define paths - Update these to your exact desktop paths
    base_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data"
    files = {
        "BNS": "bns_summarized.json",
        "BNSS": "bnss_summarized.json",
        "BSA": "bsa_summarized.json"
    }
    
    master_data = []
    
    print("🚀 Starting Master Integration...")

    for act_code, file_name in files.items():
        full_path = os.path.join(base_path, file_name)
        
        if not os.path.exists(full_path):
            print(f"⚠️ Warning: {file_name} not found. Skipping...")
            continue
            
        with open(full_path, 'r', encoding='utf-8') as f:
            sections = json.load(f)
            
        for sec in sections:
            # 1. Generate Unique ID
            sec_num = str(sec.get("section_number", "unknown")).strip()
            uid = f"{act_code}_S{sec_num}"
            
            # 2. Build the unified object
            unified_sec = {
                "uid": uid,
                "act": act_code,
                "full_act_name": "Bharatiya Nyaya Sanhita" if act_code == "BNS" else 
                                 "Bharatiya Nagarik Suraksha Sanhita" if act_code == "BNSS" else 
                                 "Bharatiya Sakshya Adhiniyam",
                "chapter": sec.get("chapter", "N/A"),
                "section_number": sec_num,
                "title": sec.get("title", ""),
                "content": sec.get("content", ""),
                "summary": sec.get("summary", ""),
                "subsections": sec.get("subsections", []),
                # This field is optimized for Vector Search
                "search_text": f"Act: {act_code} | Section: {sec_num} | Title: {sec.get('title')} | Summary: {sec.get('summary')}"
            }
            
            master_data.append(unified_sec)
        
        print(f"✅ Integrated {len(sections)} sections from {act_code}")

    # Save the Master File
    output_path = os.path.join(base_path, "master_legal_v1.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Integration Complete! Master file saved at: {output_path}")
    print(f"📊 Total Nodes in Knowledge Base: {len(master_data)}")

if __name__ == "__main__":
    merge_legal_acts()