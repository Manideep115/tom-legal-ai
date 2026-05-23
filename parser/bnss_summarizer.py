import json
import time
import os
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key
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

    # --- ROUTING LOGIC ---
    content_length = len(content)
    if content_length < 3000:
        model_to_use = "llama-3.1-8b-instant"
    else:
        model_to_use = "llama-3.3-70b-versatile"
        print(f"    -> Using Heavy Model for Section: {title[:20]}... ({content_length} chars)")

    prompt = f"""You are an expert Indian legal advisor. 
I will provide you with a section from the Bharatiya Nagarik Suraksha Sanhita (BNSS), the new procedural law of India.
Please explain this section in simple, human-friendly words so that a common person can understand the procedure easily.

Section Title: {title}
Legal Text: {content}

Provide ONLY the explanation/summary. Do not include 'Here is a summary' or 'This section means'. Just provide the clear, simplified legal explanation."""

    try:
        completion = client.chat.completions.create(
            model=model_to_use, 
            messages=[
                {"role": "system", "content": "You are a helpful legal expert who explains complex procedures simply."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
            max_tokens=800, # Increased for longer sections
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def process_summaries():
    # Update these to your actual file names
    input_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_populated_final.json"
    output_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bnss_summarized.json"

    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        return

    sections = load_json_safely(input_file)
    print(f"Loaded {len(sections)} sections. Starting Smart Summarization...")

    for i, section in enumerate(sections):
        # Resume where it left off
        if 'summary' in section and section['summary'] and section['summary'] != "Error generating summary.":
            continue

        sec_num = section.get('section_number', 'N/A')
        title = section.get('title', 'Unknown Title')
        content = section.get('content', '')

        if not content.strip():
            continue

        print(f"[{i+1}/{len(sections)}] Summarizing Section {sec_num}...")
        
        summary = generate_summary_smart(title, content)
        
        if summary:
            section['summary'] = summary
        else:
            # Simple retry logic
            time.sleep(3)
            summary = generate_summary_smart(title, content)
            section['summary'] = summary if summary else "Error generating summary."

        # Save incrementally
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
            
        time.sleep(1.2) # Delay for rate limits

    print("\n✅ BNSS Summarization Complete!")

if __name__ == "__main__":
    process_summaries()