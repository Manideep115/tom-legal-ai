import json

def report_empty_sections(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # strict=False helps if there are still messy control characters
            data = json.load(f, strict=False)
            
        empty_list = []
        
        for index, section in enumerate(data):
            content = section.get('content', '')
            
            # Check if content is empty or just whitespace
            if not content or str(content).strip() == "":
                # Capture the number and title for the report
                sec_num = section.get('number', f"Unknown (Index {index})")
                sec_title = section.get('title', 'No Title Found')
                empty_list.append(f"Section {sec_num}: {sec_title}")

        # Print the Results
        print("\n" + "="*50)
        print(f"RESULTS FOR: {file_path}")
        print("="*50)
        
        if not empty_list:
            print("🎉 Success! No empty sections found.")
        else:
            print(f"Found {len(empty_list)} empty sections:\n")
            for item in empty_list:
                print(f"  [ ] {item}")
        
        print("="*50)
        print(f"Total Sections Checked: {len(data)}")
        print(f"Total Empty:            {len(empty_list)}")
        print("="*50)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError as e:
        print(f"Error: JSON file is corrupted or contains invalid characters: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    target_file = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\data\bns_complete.json"
    report_empty_sections(target_file)