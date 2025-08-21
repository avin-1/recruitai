import os
import json
import fitz
import re
import time
from pathlib import Path
from collections import defaultdict
from statistics import median, mode, StatisticsError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import sys

# --- Start of provided parsing code ---
CONFIG = {
    "header_threshold": 0.15,
    "footer_threshold": 0.85,
    "min_heading_score": 3.0,
    "font_size_ratio": 1.0,
    "min_body_text_words": 6,
    "title_page_limit": 2,
    "schema_path": "output_schema.json"
}


def get_document_structure(doc):
    """
    Extracts the structure of an already-opened PDF document.
    """
    doc_structure = []
    for page_num, page in enumerate(doc):
        page_data = {
            "page_num": page_num + 1,
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "blocks": []
        }
        blocks = page.get_text(
            "dict",
            flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES
        ).get("blocks", [])

        for b in blocks:
            if b.get("type") == 0:
                block_data = {"bbox": b['bbox'], "lines": []}
                for line in b.get("lines", []):
                    spans = line.get("spans")
                    if spans:
                        line_text = " ".join(
                            s.get("text", "") for s in spans
                        ).strip()
                        if line_text:
                            clean_line = {
                                "text": line_text,
                                "bbox": line.get("bbox", []),
                                "spans": spans,
                            }
                            block_data["lines"].append(clean_line)
                if block_data["lines"]:
                    page_data["blocks"].append(block_data)

        doc_structure.append(page_data)

    return doc_structure


def identify_and_filter_content(doc_structure, config):
    ignored_line_ids = set()
    potential_hf_lines = defaultdict(list)

    for page in doc_structure[1:]:
        for block in page['blocks']:
            is_header = block['bbox'][3] < page['page_height'] * config['header_threshold']
            is_footer = block['bbox'][1] > page['page_height'] * config['footer_threshold']

            if is_header or is_footer:
                for line in block['lines']:
                    normalized_text = re.sub(r'\d+', '#', line['text'])
                    if len(normalized_text.split()) < 8:
                        potential_hf_lines[normalized_text].append(page['page_num'])

    num_pages = len(doc_structure)
    for text, pages in potential_hf_lines.items():
        if len(set(pages)) > 2 or (num_pages > 5 and len(set(pages)) > num_pages * 0.5):
            for page in doc_structure:
                if page['page_num'] in pages:
                    for block in page['blocks']:
                        for line in block['lines']:
                            if re.sub(r'\d+', '#', line['text']) == text:
                                ignored_line_ids.add(
                                    (line['text'], tuple(map(round, line['bbox'])))
                                )

    return ignored_line_ids


def find_title_by_layout(doc_structure, ignored_line_ids, config):
    candidates = []

    for page in doc_structure[:config['title_page_limit']]:
        for block in page['blocks']:
            if any(
                (line['text'], tuple(map(round, line['bbox']))) in ignored_line_ids
                for line in block['lines']
            ):
                continue

            if not (1 <= len(block['lines']) <= 4) or block['bbox'][1] > page['page_height'] * 0.4:
                continue

            block_text = " ".join(line['text'] for line in block['lines'])
            if not block_text:
                continue

            avg_size = median(
                [s['size'] for line in block['lines'] for s in line['spans']]
            ) if any(line['spans'] for line in block['lines']) else 0

            block_center_x = (block['bbox'][0] + block['bbox'][2]) / 2
            page_center_x = page['page_width'] / 2

            centering_score = (
                (1 - abs(block_center_x - page_center_x) / page_center_x) * 15
                if page_center_x > 0 else 0
            )
            position_score = (1 - block['bbox'][1] / (page['page_height'] * 0.4)) * 5
            score = avg_size + centering_score + position_score

            candidates.append({
                "text": block_text,
                "score": score,
                "lines": block['lines']
            })

    if not candidates:
        return "Untitled Document", set()

    best_candidate = max(candidates, key=lambda x: x["score"])
    return best_candidate['text'], {
        (line['text'], tuple(map(round, line['bbox'])))
        for line in best_candidate['lines']
    }


def get_heading_score(line, block, body_text_size, config):
    text = line['text']
    spans = line['spans']

    if re.search(r'(https?://\S+|www\.\S+|\S+\.(com|org|git|pdf))$', text) \
       or len(text.split()) > 15 \
       or text.endswith(('.', ',')):
        return -10

    try:
        font_sizes = {round(s['size']) for s in spans}
        if len(font_sizes) > 1:
            return -10
        line_size = font_sizes.pop()
    except (KeyError, IndexError):
        return -10

    score = 0.0
    is_bold = any('bold' in s['font'].lower() for s in spans)

    if line_size > body_text_size * config["font_size_ratio"]:
        score += (line_size - body_text_size) * 3
    elif line_size < body_text_size:
        score -= (body_text_size - line_size)

    if is_bold:
        score += 2.5
    if re.match(r"^\d+\.\s", text):
        score += 2.0
    if text.istitle():
        score += 1.5
    if text.isupper():
        score += 2.0
    if len(text.split()) < 10:
        score += 1.0
    if text.endswith(':'):
        score += 2.0
    if len(block['lines']) == 1:
        score += 3.0
    if line_size < body_text_size and not is_bold:
        score -= 3.0

    return score


def extract_pdf_outline(doc_structure, config=CONFIG):
    if not any(block['lines'] for page in doc_structure for block in page['blocks']):
        return {
            "title": "No Text Found",
            "outline": [],
            "error": "No text extracted from the document."
        }

    font_sizes = [
        round(s['size'])
        for page in doc_structure
        for b in page['blocks']
        for line in b['lines']
        for s in line['spans']
        if len(line['text'].split()) > config['min_body_text_words']
        and not any('bold' in sp['font'].lower() for sp in line['spans'])
    ]

    body_text_size = median(font_sizes) if font_sizes else 10
    ignored_line_ids = identify_and_filter_content(doc_structure, config)
    title_text, title_line_ids = find_title_by_layout(doc_structure, ignored_line_ids, config)
    ignored_line_ids.update(title_line_ids)

    heading_candidates = []
    for page in doc_structure:
        for block in page['blocks']:
            for line in block['lines']:
                if (line['text'], tuple(map(round, line['bbox']))) in ignored_line_ids:
                    continue

                score = get_heading_score(line, block, body_text_size, config)
                if score >= config['min_heading_score']:
                    line['page'] = page['page_num']
                    heading_candidates.append(line)

    if not heading_candidates:
        return {"title": title_text, "outline": []}

    style_properties = defaultdict(list)
    for h in heading_candidates:
        try:
            style_key = (
                mode([round(s['size']) for s in h['spans']]),
                any('bold' in s['font'].lower() for s in h['spans'])
            )
        except StatisticsError:
            continue
        style_properties[style_key].append(h['bbox'][0])

    ranked_styles = [
        {"size": s[0], "bold": s[1], "x0": median(x0s), "style_key": s}
        for s, x0s in style_properties.items()
    ]
    ranked_styles.sort(key=lambda x: (-x["size"], x["x0"]))
    style_to_level = {s["style_key"]: f"H{min(i+1, 3)}" for i, s in enumerate(ranked_styles[:3])}

    outline = []
    for line in heading_candidates:
        try:
            style_key = (
                mode([round(s['size']) for s in line['spans']]),
                any('bold' in s['font'].lower() for s in line['spans'])
            )
        except StatisticsError:
            style_key = None

        level = style_to_level.get(style_key, "H3")
        outline.append({
            "level": level,
            "text": line["text"],
            "page": line["page"],
            "bbox": line["bbox"]
        })

    return {"title": title_text, "outline": outline, "doc_structure": doc_structure}


def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- End of provided parsing code ---

def get_content_between_headings(doc_structure, heading1_page, heading1_bbox, heading2_page, heading2_bbox):
    content_text = []

    for page_data in doc_structure:
        is_first_page = (page_data['page_num'] == heading1_page)
        is_last_page = (page_data['page_num'] == heading2_page)

        if page_data['page_num'] < heading1_page:
            continue
        if page_data['page_num'] > heading2_page:
            break

        for block in page_data['blocks']:
            if is_first_page and block['bbox'][1] < heading1_bbox[3]:
                continue
            if is_last_page and block['bbox'][3] > heading2_bbox[1]:
                break

            block_text = " ".join([line['text'] for line in block['lines']])
            content_text.append(block_text)

    return " ".join(content_text)


def classify_heading(heading_text):
    text = heading_text.lower()

    education_keywords = ['education', 'academic', 'qualification']
    experience_keywords = ['experience', 'employment', 'professional', 'work history', 'career']
    skills_keywords = ['skills', 'abilities', 'competencies', 'technical skills', 'proficiencies']
    contact_keywords = ['contact', 'personal details', 'email', 'phone', 'address']

    if any(word in text for word in education_keywords):
        return 'education'
    if any(word in text for word in experience_keywords):
        return 'experience'
    if any(word in text for word in skills_keywords):
        return 'skills'
    if any(word in text for word in contact_keywords):
        return 'personal_info'

    return 'other'


def extract_personal_info(text):
    name = text.split('\n')[0].strip()
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\+?\d{1,2}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', text)

    return {
        "name": name,
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "raw_text": text
    }


class ResumeProcessor(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".pdf"):
            print(f"\n--- New resume detected: {event.src_path} ---")
            self.process_resume(event.src_path)

    def process_resume(self, file_path):
        # --- MODIFIED: Retry logic for file access ---
        max_retries = 10
        retry_delay_seconds = 0.5
        doc = None
        for i in range(max_retries):
            try:
                doc = fitz.open(file_path)
                break
            except Exception as e:
                print(f"Attempt {i+1}/{max_retries}: Failed to open file. Retrying in {retry_delay_seconds}s. Error: {e}")
                time.sleep(retry_delay_seconds)

        if doc is None:
            print(f"Skipping file due to persistent parsing error: Could not open or read PDF file after {max_retries} attempts.")
            return
        # --- END OF MODIFIED CODE ---

        try:
            start_time = time.time()
            
            # --- MODIFIED: Passing the document object to the next function ---
            doc_structure = get_document_structure(doc)
            
            if not doc_structure:
                print("No text found in the document.")
                return

            result = extract_pdf_outline(doc_structure, CONFIG)

            if "error" in result:
                print(f"Skipping file due to parsing error: {result['error']}")
                return

            title = result.get("title", "")
            headings = result.get('outline', [])

            candidate_profile = {
                "title": title,
                "personal_info": {},
                "experience": [],
                "education": [],
                "skills": [],
                "other": {}
            }

            if doc_structure:
                first_block_text = " ".join(
                    [line['text'] for line in doc_structure[0]['blocks'][0]['lines']]
                )
                candidate_profile["personal_info"] = extract_personal_info(first_block_text)

            if headings:
                end_of_doc_bbox = (
                    0,
                    doc_structure[-1]['page_height'],
                    doc_structure[-1]['page_width'],
                    doc_structure[-1]['page_height']
                )
                headings.append({
                    "text": "End of Document",
                    "page": len(doc_structure),
                    "bbox": end_of_doc_bbox
                })

                for i in range(len(headings) - 1):
                    h1, h2 = headings[i], headings[i+1]
                    content_text = get_content_between_headings(
                        doc_structure, h1['page'], h1['bbox'], h2['page'], h2['bbox']
                    )
                    heading_category = classify_heading(h1['text'])

                    if heading_category == 'education':
                        candidate_profile['education'].append(content_text.strip())
                    elif heading_category == 'experience':
                        candidate_profile['experience'].append(content_text.strip())
                    elif heading_category == 'skills':
                        candidate_profile['skills'].append(content_text.strip())
                    else:
                        candidate_profile['other'][h1['text']] = content_text.strip()

            elapsed = time.time() - start_time
            print(f"Time taken to parse: {elapsed:.2f} seconds")

            filename = os.path.basename(file_path)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            save_json(candidate_profile, output_path)
            print(f"Candidate profile saved to {output_path}")

            model_script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'model_parsing.py'
            )

            if os.path.exists(model_script_path):
                print(f"Calling model script: {model_script_path}")
                try:
                    # Use the sys.executable path to ensure the correct Python interpreter is used
                    subprocess.run(
                        [sys.executable, model_script_path],
                        check=True,
                        capture_output=True,
                        text=True,
                        env=os.environ.copy()
                    )
                    print("model_parsing.py executed successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Error running model_parsing.py: {e.stderr}")
                except FileNotFoundError:
                    print(f"Python executable not found at '{sys.executable}'.")
            else:
                print(f"model_parsing.py not found at {model_script_path}. Skipping.")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        finally:
            # Ensure the document is always closed
            if doc:
                doc.close()


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_FOLDER = os.path.join(SCRIPT_DIR, "input")
    OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "output")

    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    event_handler = ResumeProcessor()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    observer.start()

    print(f"Monitoring '{INPUT_FOLDER}' for new resumes. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()