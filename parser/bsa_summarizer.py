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

def generate_summary_smart(title, content):
    """Routes the summary request based on content length."""
    if not content or not content.strip():
        return "No content available."

    # Routing logic for BSA
    content_length = len(content)
    if content_length < 3000:
        model_to_use = "llama-3.1-8b-instant"
    else:
        model_to_use = "llama-3.3-70b-versatile"
        print(f"    -> Using Heavy Model for Section: {title[:20]}... ({content_length} chars)")

    prompt = f"""You are an expert Indian legal advisor. 
I will provide you with a section from the Bharatiya Sakshya Adhiniyam (BSA), 2023, the new evidence law of India.
Please explain this section in simple, human-friendly words so that a common person can understand what counts as evidence and how it is proved in court.

Section Title: {title}
Legal Text: {content}

Provide ONLY the explanation/summary. Do not include 'Here is a summary' or 'This section means'. Just provide the clear, simplified legal explanation."""

    try:
        completion = client.chat.completions.create(
            model=model_to_use, 
            messages=[
                {"role": "system", "content": "You are a helpful legal expert who explains evidence law simply."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
            max_tokens=800,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def process_bsa_summaries():
    # Update paths for your cleaned BSA data
    input_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_populated.json"
    output_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bsa_summarized.json"

    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        return

    sections = load_json_safely(input_file)
    print(f"Loaded {len(sections)} BSA sections. Starting Smart Summarization...")

    for i, section in enumerate(sections):
        # Resume logic
        if 'summary' in section and section['summary'] and section['summary'] != "Error generating summary.":
            continue

        sec_num = section.get('section_number', 'N/A')
        title = section.get('title', 'Unknown Title')
        content = section.get('content', '')

        if not content.strip():
            continue

        print(f"[{i+1}/{len(sections)}] Summarizing BSA Section {sec_num}: {title[:30]}...")
        
        summary = generate_summary_smart(title, content)
        
        if summary:
            section['summary'] = summary
        else:
            time.sleep(3) # Retry delay
            summary = generate_summary_smart(title, content)
            section['summary'] = summary if summary else "Error generating summary."

        # Incremental save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
            
        time.sleep(1.2) # Rate limit protection

    print("\n✅ BSA Summarization Complete!")

if __name__ == "__main__":
    process_bsa_summaries()