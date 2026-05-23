import json
import time
import os
from groq import Groq

# Initialize Groq client
# Replace with your actual API key or use os.environ.get("GROQ_API_KEY")
GROQ_API_KEY = "YOUR_API_KEY_HERE" 
client = Groq(api_key=GROQ_API_KEY)

def load_json_safely(file_path):
    """Safely loads JSON, falling back to UTF-16 if Windows changed the encoding."""
    try:
        # utf-8-sig handles standard UTF-8 and UTF-8 with BOM
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f, strict=False)
    except UnicodeDecodeError:
        print("Detected UTF-16 encoding (Windows Notepad). Adapting...")
        with open(file_path, 'r', encoding='utf-16') as f:
            return json.load(f, strict=False)

def generate_summary_groq(title, content):
    """Calls Llama 3.1 via Groq to summarize the legal text."""
    
    if not content or not content.strip():
        return "No content available to summarize."

    prompt = f"""You are an expert Indian legal advisor. 
I will provide you with a section from the Bharatiya Nyaya Sanhita (BNS).
Please explain this section in simple, human-friendly words so that a common person can understand it easily.

Section Title: {title}
Legal Text: {content}

Provide ONLY the explanation/summary. Do not include introductory phrases like 'Here is a summary' or 'This section means'. Just provide the clear explanation."""

    try:
        completion = client.chat.completions.create(
            # Using the new, supported model
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": "You are a helpful legal expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, 
            max_tokens=500,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def process_bns_summaries():
    input_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bns_complete.json"
    output_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bns_summarized.json"

    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        return

    # Load the data using our safe loader
    sections = load_json_safely(input_file)
    print(f"Loaded {len(sections)} sections. Starting summarization via Groq API...")

    for i, section in enumerate(sections):
        # Skip if we already summarized it (Resumes where it left off)
        if 'summary' in section and section['summary']:
            continue

        sec_num = section.get('number', section.get('section_number', 'N/A'))
        title = section.get('title', 'Unknown Title')
        
        # Skip empty entries that might have sneaked into the JSON
        if not section.get('content', '').strip():
            continue

        print(f"[{i+1}/{len(sections)}] Summarizing Section {sec_num}: {title[:30]}...")
        
        # Get the summary from Groq
        summary = generate_summary_groq(title, section.get('content', ''))
        
        if summary:
            section['summary'] = summary
            
            # Remove the old 'text' field as requested
            if 'text' in section:
                del section['text']
        else:
            print("  -> API failed (Rate limit or network). Retrying in 5 seconds...")
            time.sleep(5)
            summary = generate_summary_groq(title, section.get('content', ''))
            if summary:
                section['summary'] = summary
                if 'text' in section:
                    del section['text']
            else:
                section['summary'] = "Error generating summary."

        # Save incrementally after every section in clean UTF-8
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
            
        # 1-second delay to avoid hitting Groq's Requests Per Minute (RPM) limits
        time.sleep(1) 

    print("\n✅ All summaries generated successfully! Saved to bns_summarized.json")

if __name__ == "__main__":
    process_bns_summaries()