import json
import time
import os
import re
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = "YOUR_API_KEY_HERE" 
client = Groq(api_key=GROQ_API_KEY)

def load_json_safely(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f, strict=False)
    except UnicodeDecodeError:
        print("Detected UTF-16 encoding. Adapting...")
        with open(file_path, 'r', encoding='utf-16') as f:
            return json.load(f, strict=False)

def extract_bsa_subsections(content):
    """Extracts structural parts from BSA text using smart routing."""
    if not content or not content.strip():
        return []

    content_length = len(content)
    # BSA sections are usually shorter, but Sec 63 (Electronic Evidence) is huge.
    if content_length < 3000:
        model_to_use = "llama-3.1-8b-instant"
    else:
        model_to_use = "llama-3.3-70b-versatile"
        print(f"    -> Large Evidence Block ({content_length} chars). Using {model_to_use}")

    prompt = f"""You are a precise legal data extraction bot specializing in the Bharatiya Sakshya Adhiniyam (BSA), India's new Evidence Act.
Analyze the following text and break it down into its distinct parts: 
1. introductory text (id: "main")
2. numbered subsections (id: "(1)", "(2)")
3. lettered clauses (id: "(a)", "(b)")
4. Provisos (id: "Proviso 1", "Proviso 2")
5. Explanations (id: "Explanation")
6. Illustrations (id: "Illustration (a)")

Return the result STRICTLY as a JSON array of objects. Each object must have "id" and "text". 
Do NOT change the original wording. Do NOT include markdown blocks.

Legal Text:
{content}
"""

    try:
        completion = client.chat.completions.create(
            model=model_to_use, 
            messages=[
                {"role": "system", "content": "You output only raw, valid JSON arrays. No intro, no backticks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, 
        )
        
        raw_output = completion.choices[0].message.content.strip()
        
        # Clean potential markdown backticks if LLM disobeys
        if raw_output.startswith("```"):
            raw_output = re.sub(r'^```json\s*|```$', '', raw_output, flags=re.MULTILINE)
            
        return json.loads(raw_output.strip())
        
    except Exception as e:
        print(f"    -> Extraction Error: {e}")
        return None

def process_bsa_structure():
    file_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_summarized.json"

    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return

    sections = load_json_safely(file_path)
    print(f"Loaded {len(sections)} BSA sections. Starting structural extraction...")

    for i, section in enumerate(sections):
        # Skip if already processed
        if 'subsections' in section and section['subsections'] and section['subsections'][0].get('id') != 'error':
            continue

        sec_num = section.get('section_number', 'N/A')
        content = section.get('content', '')
        
        if not content.strip():
            continue

        print(f"[{i+1}/{len(sections)}] Splitting BSA Section {sec_num}...")
        
        extracted_data = extract_bsa_subsections(content)
        
        if extracted_data:
            section['subsections'] = extracted_data
        else:
            time.sleep(3) # Short cooldown
            extracted_data = extract_bsa_subsections(content)
            if extracted_data:
                section['subsections'] = extracted_data
            else:
                section['subsections'] = [{"id": "error", "text": "Parsing failed."}]

        # Incremental save
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
            
        time.sleep(1.2) # Rate limit delay

    print("\n✅ BSA structural extraction complete!")

if __name__ == "__main__":
    process_bsa_structure()