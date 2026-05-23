import json
import time
import os
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = "YOUR_API_KEY_HERE"
client = Groq(api_key=GROQ_API_KEY)

def load_json_safely(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f, strict=False)
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='utf-16') as f:
            return json.load(f, strict=False)

def extract_bnss_subsections(content):
    """Routes procedural content to models and extracts structural JSON."""
    if not content or not content.strip():
        return []

    content_length = len(content)
    # BNSS can be very dense, using 3000 chars as the threshold for 70b
    if content_length < 3000:
        model_to_use = "llama-3.1-8b-instant"
    else:
        model_to_use = "llama-3.3-70b-versatile"
        print(f"    -> Large Procedural Block ({content_length} chars). Using {model_to_use}")

    prompt = f"""You are a precise legal data extraction bot specializing in Indian Criminal Procedure.
Analyze the following text from the Bharatiya Nagarik Suraksha Sanhita (BNSS). 
Break it down into its structural parts: introductory text, numbered subsections (1, 2), lettered clauses (a, b), Explanations, and Illustrations.

Return the result STRICTLY as a JSON array of objects. Each object must have exactly two keys:
1. "id": The identifier (e.g., "(1)", "(5)(a)", "Explanation", "Illustration"). Use "main" for text with no specific identifier.
2. "text": The exact original text of that specific part. Do NOT summarize.

Do NOT include any markdown formatting or code blocks. Output ONLY the raw JSON array.

Legal Text:
{content}
"""

    try:
        completion = client.chat.completions.create(
            model=model_to_use, 
            messages=[
                {"role": "system", "content": "You output only raw, valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, 
        )
        
        raw_output = completion.choices[0].message.content.strip()
        
        # Strip potential markdown backticks
        if raw_output.startswith("```"):
            raw_output = re.sub(r'^```json\s*|```$', '', raw_output, flags=re.MULTILINE)
            
        return json.loads(raw_output.strip())
        
    except Exception as e:
        print(f"    -> Extraction Error: {e}")
        return None

def process_bnss_structure():
    # Update these paths for BNSS
    file_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_summarized.json"

    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return

    sections = load_json_safely(file_path)
    print(f"Loaded {len(sections)} BNSS sections. Starting structural extraction...")

    for i, section in enumerate(sections):
        # Skip if already processed or has data
        if 'subsections' in section and section['subsections'] and section['subsections'][0].get('id') != 'error':
            continue

        sec_num = section.get('section_number', 'N/A')
        content = section.get('content', '')
        
        if not content.strip():
            continue

        print(f"[{i+1}/{len(sections)}] Splitting BNSS Section {sec_num}...")
        
        extracted_data = extract_bnss_subsections(content)
        
        if extracted_data:
            section['subsections'] = extracted_data
        else:
            time.sleep(4) # Cooldown on failure
            extracted_data = extract_bnss_subsections(content)
            if extracted_data:
                section['subsections'] = extracted_data
            else:
                section['subsections'] = [{"id": "error", "text": "Parsing failed."}]

        # Incremental save
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
            
        time.sleep(1.2) # Avoid rate limits

    print("\n✅ BNSS structural extraction complete!")

if __name__ == "__main__":
    process_bnss_structure()