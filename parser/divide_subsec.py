import json
import time
import os
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = "YOUR_API_KEY_HERE"
client = Groq(api_key=GROQ_API_KEY)

def load_json_safely(file_path):
    """Safely loads JSON, falling back to UTF-16 if Windows changed the encoding."""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f, strict=False)
    except UnicodeDecodeError:
        print("Detected UTF-16 encoding. Adapting...")
        with open(file_path, 'r', encoding='utf-16') as f:
            return json.load(f, strict=False)

def extract_subsections(content):
    """Routes the content to the right model based on length and extracts JSON."""
    
    if not content or not content.strip():
        return []

    # --- THE ROUTING LOGIC ---
    content_length = len(content)
    if content_length < 3000:
        model_to_use = "llama-3.1-8b-instant"
        print(f"    -> Short content ({content_length} chars). Using fast model: {model_to_use}")
    else:
        model_to_use = "llama-3.3-70b-versatile"
        print(f"    -> Long content ({content_length} chars). Using heavy-duty model: {model_to_use}")

    prompt = f"""You are a precise legal data extraction bot.
Analyze the following legal text from the Bharatiya Nyaya Sanhita (BNS). 
Break it down into its distinct structural parts: the main introductory text, numbered subsections (1, 2), lettered clauses (a, b), Explanations, Exceptions, and Illustrations.

Return the result STRICTLY as a JSON array of objects. Each object must have exactly two keys:
1. "id": The identifier (e.g., "(1)", "(5)(a)", "Explanation 1", "Illustration (a)"). Use "main" for introductory text that has no specific number/letter.
2. "text": The exact original text of that specific part. Do NOT summarize or change the text.

Do NOT include any markdown formatting like ```json. Output ONLY the raw JSON array.

Legal Text:
{content}
"""

    try:
        completion = client.chat.completions.create(
            model=model_to_use, 
            messages=[
                {"role": "system", "content": "You output only raw, valid JSON arrays. No pleasantries, no markdown tags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Extremely low temp for precise extraction
        )
        
        raw_output = completion.choices[0].message.content.strip()
        
        # Strip out markdown formatting if the LLM disobeys the prompt
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3]
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:-3]
            
        return json.loads(raw_output.strip())
        
    except json.JSONDecodeError:
        print("    -> LLM did not return valid JSON. Catching error...")
        return None
    except Exception as e:
        print(f"    -> API Error: {e}")
        return None

def process_subsections():
    file_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bns_summarized.json"

    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return

    sections = load_json_safely(file_path)
    print(f"Loaded {len(sections)} sections. Starting smart extraction via Groq...")

    for i, section in enumerate(sections):
        # Resume feature: Skip if we already successfully extracted it
        if 'subsections' in section and section['subsections'] and section['subsections'][0].get('id') != 'error':
            continue

        sec_num = section.get('section_number', section.get('number', 'N/A'))
        title = section.get('title', 'Unknown Title')
        content = section.get('content', '')
        
        # Skip empty entries
        if not content.strip():
            continue

        print(f"\n[{i+1}/{len(sections)}] Section {sec_num}: {title[:30]}...")
        
        extracted_data = extract_subsections(content)
        
        if extracted_data is not None:
            section['subsections'] = extracted_data
        else:
            print("    -> Retrying in 5 seconds...")
            time.sleep(5)
            # Second attempt
            extracted_data = extract_subsections(content)
            if extracted_data is not None:
                section['subsections'] = extracted_data
            else:
                print("    -> Failed twice. Marking with error.")
                section['subsections'] = [{"id": "error", "text": "Failed to extract subsections due to parsing limits."}]

        # Save incrementally to protect your progress
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
            
        time.sleep(1) # Gentle delay to respect Groq rate limits

    print("\n✅ All subsections extracted successfully! Check your bns_summarized.json file.")

if __name__ == "__main__":
    process_subsections()