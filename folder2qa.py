import os
import re
import json

def find_md_files(folder_path):
    """Finds all .md files in the given folder and its subfolders."""
    md_files = []
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith('.md'):
                md_files.append(os.path.join(root, file_name))
    return md_files

def read_markdown(file_path):
    """Reads the markdown file and returns its content as a string."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_markdown_headings(text, file_name):
    """
    Parses the markdown text and extracts prompt-completion pairs based on headings.

    For each heading, the prompt is the file name plus the full path of headings
    (e.g., FILENAME - TITLELEVEL1 - TITLELEVEL2...),
    and the completion is the text under that heading until the next heading of the same or higher level.
    """
    lines = text.split('\n')
    qa_pairs = []

    # List to store headings with their level and line numbers
    headings = []

    # Regex pattern to match markdown headings
    heading_pattern = re.compile(r'^(#{1,6})\s*(.*)')

    for idx, line in enumerate(lines):
        heading_match = heading_pattern.match(line)
        if heading_match:
            hashes, title = heading_match.groups()
            level = len(hashes)
            title = title.strip()
            # Record the heading with its level and line number
            headings.append({'level': level, 'title': title, 'line_number': idx})

    # Add an artificial end to simplify processing
    headings.append({'level': 0, 'title': 'END_OF_DOCUMENT', 'line_number': len(lines)})

    # Now, for each heading, get the content until the next heading of same or higher level
    for i in range(len(headings) - 1):
        current_heading = headings[i]
        current_level = current_heading['level']
        start_line = current_heading['line_number'] + 1

        # Find the next heading of the same or higher level
        for j in range(i + 1, len(headings)):
            if headings[j]['level'] <= current_level:
                end_line = headings[j]['line_number']
                break

        # Build the prompt by combining filename and headings from root to current
        prompt_headings = [h['title'] for h in headings[:i + 1]]
        prompt = f"{file_name} - " + ' - '.join(prompt_headings)

        # Get the content between current heading and the next heading of same or higher level
        completion_lines = lines[start_line:end_line]
        completion = '\n'.join(completion_lines).strip()

        # Skip if completion is empty
        if completion:
            qa_pairs.append({
                'prompt': prompt,
                'completion': completion
            })

    return qa_pairs

def process_md_file(file_path):
    """Processes an md file and returns a list of prompt-completion pairs."""
    # Get the filename without the extension
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    markdown_text = read_markdown(file_path)
    qa_pairs = []

    # First, create a prompt-completion pair where the prompt is the filename and the completion is the whole file content
    qa_pairs.append({
        'prompt': file_name,
        'completion': markdown_text.strip()
    })

    # Then, process the file level by level
    qa_pairs.extend(parse_markdown_headings(markdown_text, file_name))

    return qa_pairs

def save_qa_pairs(qa_pairs, output_file):
    """Saves the prompt-completion pairs to a JSONL file in the correct format for fine-tuning GPT-4."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for pair in qa_pairs:
            if pair['completion']:  # Ensure the completion is not empty
                data = {
                    'messages': [
                        {'role': 'user', 'content': pair['prompt']},
                        {'role': 'assistant', 'content': pair['completion']}
                    ]
                }
                json_line = json.dumps(data, ensure_ascii=False)
                f.write(json_line + '\n')

def main(folder_path, output_file):
    all_qa_pairs = []
    md_files = find_md_files(folder_path)
    for md_file in md_files:
        qa_pairs = process_md_file(md_file)
        all_qa_pairs.extend(qa_pairs)

    save_qa_pairs(all_qa_pairs, output_file)
    print(f"Processed {len(md_files)} markdown files.")
    print(f"Generated {len(all_qa_pairs)} prompt-completion pairs.")

# Usage
if __name__ == '__main__':
    folder_path = r'C:\Users\bunny\Desktop\FSLogix'  # Replace with your folder path
    output_file = 'folder_fine_tuning_dataset.jsonl'  # Output file for fine-tuning
    main(folder_path, output_file)
