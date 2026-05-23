import json
import os

def generate_skeleton():
    # Paths - Update these to your actual folder locations
    input_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_index.json"
    output_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_flat.json"

    if not os.path.exists(input_path):
        print(f"Error: Could not find {input_path}")
        return

    # Load the hierarchical index
    with open(input_path, 'r', encoding='utf-8') as f:
        hierarchical_data = json.load(f)

    flat_list = []

    # Flatten the structure
    for chapter_data in hierarchical_data:
        chapter_name = chapter_data.get("chapter", "Unknown Chapter")
        act_name = chapter_data.get("act", "BNSS")
        
        for section in chapter_data.get("sections", []):
            skeleton_entry = {
                "act": act_name,
                "chapter": chapter_name,
                "section_number": section.get("section_number"),
                "title": section.get("title"),
                "content": "",        # To be filled by you/parser
                "summary": "",        # To be filled by Groq
                "subsections": []     # To be filled by Groq Sub-extractor
            }
            flat_list.append(skeleton_entry)

    # Save the new flat skeleton
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(flat_list, f, indent=4, ensure_ascii=False)

    print(f"✅ Skeleton created with {len(flat_list)} sections!")
    print(f"📍 Saved to: {output_path}")

if __name__ == "__main__":
    generate_skeleton()