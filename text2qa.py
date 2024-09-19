import re
import json

def read_markdown(file_path):
    """Reads the markdown file and returns its content as a string."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_markdown_headings(text):
    """
    Parses the markdown text and extracts prompt-completion pairs based on headings.

    For each heading, the prompt is the full path of headings (e.g., HIGHESTTOPIC - LOWERLEVELTOPIC - CURRENTHEADING),
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

        # Build the prompt by combining headings from root to current
        prompt_headings = [h['title'] for h in headings[:i + 1]]
        prompt = ' - '.join(prompt_headings)

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


# Usage
markdown_file = r'C:\Users\yingnanju\OneDrive - Microsoft\Desktop\fslogix_doc.md'  # Replace with your markdown file path
output_file = 'fine_tuning_dataset.jsonl'  # Output file for fine-tuning

markdown_text = read_markdown(markdown_file)
qa_pairs = parse_markdown_headings(markdown_text)
save_qa_pairs(qa_pairs, output_file)

print(f"Generated {len(qa_pairs)} prompt-completion pairs.")
