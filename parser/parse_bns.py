import fitz  # PyMuPDF
import json
import re
import os

def clean_text(text):
    """
    Handles hyphenation at line ends and normalizes whitespace.
    """
    # 1. Join words split by hyphen at end of line (extra-\nterritorial -> extra-territorial)
    text = re.sub(r'-\s*\n\s*', '-', text)
    
    # 2. Replace all other newlines and tabs with spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def parse_bns_legal_rag():
    # File Paths
    pdf_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\BNS2023.pdf"
    json_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bns_sections.json"
    output_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bns_complete.json"

    if not os.path.exists(pdf_path) or not os.path.exists(json_path):
        print("Error: Ensure PDF and JSON files exist in the specified paths.")
        return

    # 1. Load the JSON structure
    with open(json_path, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)

    # 2. Extract Text from PDF (Page 74 onwards)
    print("Extracting text from PDF...")
    doc = fitz.open(pdf_path)
    full_text_raw = ""
    
    # Page index starts at 0, so page 74 is index 73
    for page_num in range(73, len(doc)):
        full_text_raw += doc[page_num].get_text("text") + " "

    # 3. Clean the PDF text
    print("Normalizing text and repairing hyphens...")
    normalized_corpus = clean_text(full_text_raw)

    # 4. Extract content by finding titles
    # We iterate through the sections and look for the current title and the next title
    print(f"Processing {len(sections_data)} sections...")
    
    for i in range(len(sections_data)):
        current_section = sections_data[i]
        current_title = current_section['title'].strip()
        
        # Prepare search: Normalize the title just like we did the corpus
        search_title = clean_text(current_title)
        
        # Find start position
        # Using case-insensitive search
        start_match = re.search(re.escape(search_title), normalized_corpus, re.IGNORECASE)
        
        if not start_match:
            print(f"Warning: Title not found - '{current_title}'")
            current_section['content'] = ""
            continue
            
        start_index = start_match.end() # Content starts after the title

        # Determine where the content ends (at the start of the next section's title)
        if i + 1 < len(sections_data):
            next_title = clean_text(sections_data[i+1]['title'])
            # Look for the next title starting FROM the current start_index
            end_match = re.search(re.escape(next_title), normalized_corpus[start_index:], re.IGNORECASE)
            
            if end_match:
                end_index = start_index + end_match.start()
            else:
                end_index = len(normalized_corpus)
        else:
            # Last section goes to the end of the doc
            end_index = len(normalized_corpus)

        # Extract and clean content
        content = normalized_corpus[start_index:end_index].strip()
        
        # Remove any leading section numbers if they were missed by title match
        # (e.g., if the JSON title is "Punishment" but PDF has "4. Punishment")
        content = re.sub(r'^\d+\.\s*', '', content)
        
        current_section['content'] = content

    # 5. Save the updated JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sections_data, f, indent=4, ensure_ascii=False)

    print(f"Success! Processed data saved to: {output_path}")

if __name__ == "__main__":
    parse_bns_legal_rag()