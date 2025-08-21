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

# --- Start of your provided parsing code ---
CONFIG = {
    "header_threshold": 0.15,
    "footer_threshold": 0.85,
    "min_heading_score": 3.0,
    "font_size_ratio": 1.0,
    "min_body_text_words": 6,
    "title_page_limit": 2,
    "schema_path": "output_schema.json"
}

def get_document_structure(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return None
    doc_structure = []
    for page_num, page in enumerate(doc):
        page_data = {
            "page_num": page_num + 1,
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "blocks": []
        }
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES).get("blocks", [])
        for b in blocks:
            if b.get("type") == 0:
                block_data = {"bbox": b['bbox'], "lines": []}
                for line in b.get("lines", []):
                    spans = line.get("spans")
                    if spans:
                        line_text = " ".join(s.get("text", "") for s in spans).strip()
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
    doc.close()
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
                                ignored_line_ids.add((line['text'], tuple(map(round, line['bbox']))))
    return ignored_line_ids

def find_title_by_layout(doc_structure, ignored_line_ids, config):
    candidates = []
    for page in doc_structure[:config['title_page_limit']]:
        for block in page['blocks']:
            if any((line['text'], tuple(map(round, line['bbox']))) in ignored_line_ids for line in block['lines']):
                continue
            if not (1 <= len(block['lines']) <= 4) or block['bbox'][1] > page['page_height'] * 0.4:
                continue
            block_text = " ".join(line['text'] for line in block['lines'])
            if not block_text: continue
            avg_size = median([s['size'] for line in block['lines'] for s in line['spans']]) if any(line['spans'] for line in block['lines']) else 0
            block_center_x = (block['bbox'][0] + block['bbox'][2]) / 2
            page_center_x = page['page_width'] / 2
            centering_score = (1 - abs(block_center_x - page_center_x) / page_center_x) * 15 if page_center_x > 0 else 0
            position_score = (1 - block['bbox'][1] / (page['page_height'] * 0.4)) * 5
            score = avg_size + centering_score + position_score
            candidates.append({"text": block_text, "score": score, "lines": block['lines']})
    if not candidates:
        return "Untitled Document", set()
    best_candidate = max(candidates, key=lambda x: x["score"])
    return best_candidate['text'], {(line['text'], tuple(map(round, line['bbox']))) for line in best_candidate['lines']}

def get_heading_score(line, block, body_text_size, config):
    text = line['text']
    spans = line['spans']
    if re.search(r'(https?://\S+|www\.\S+|\S+\.(com|org|git|pdf))$', text) or \
       len(text.split()) > 15 or \
       text.endswith(('.', ',')):
        return -10
    try:
        font_sizes = {round(s['size']) for s in spans}
        if len(font_sizes) > 1: return -10
        line_size = font_sizes.pop()
    except (KeyError, IndexError):
        return -10
    score = 0.0
    is_bold = any('bold' in s['font'].lower() for s in spans)
    if line_size > body_text_size * config["font_size_ratio"]: score += (line_size - body_text_size) * 3
    elif line_size < body_text_size: score -= (body_text_size - line_size)
    if is_bold: score += 2.5
    if re.match(r"^\d+\.\s", text): score += 2.0
    if text.istitle(): score += 1.5
    if text.isupper(): score += 2.0
    if len(text.split()) < 10: score += 1.0
    if text.endswith(':'): score += 2.0
    if len(block['lines']) == 1: score += 3.0
    if line_size < body_text_size and not is_bold: score -= 3.0
    return score

def extract_pdf_outline(pdf_path, config=CONFIG):
    doc_structure = get_document_structure(pdf_path)
    if doc_structure is None:
        return {"title": os.path.basename(pdf_path), "outline": [], "error": "Could not open or read PDF file."}
    if not any(block['lines'] for page in doc_structure for block in page['blocks']):
        return {"title": "No Text Found", "outline": [], "error": "No text extracted from the document."}
    font_sizes = [
        round(s['size']) for page in doc_structure for b in page['blocks'] 
        for line in b['lines'] for s in line['spans']
        if len(line['text'].split()) > config['min_body_text_words'] and not any('bold' in sp['font'].lower() for sp in line['spans'])
    ]
    body_text_size = median(font_sizes) if font_sizes else 10
    ignored_line_ids = identify_and_filter_content(doc_structure, config)
    title_text, title_line_ids = find_title_by_layout(doc_structure, ignored_line_ids, config)
    ignored_line_ids.update(title_line_ids)
    heading_candidates = []
    for page in doc_structure:
        for block in page['blocks']:
            for line in block['lines']:
                if (line['text'], tuple(map(round, line['bbox']))) in ignored_line_ids: continue
                score = get_heading_score(line, block, body_text_size, config)
                if score >= config['min_heading_score']:
                    line['page'] = page['page_num']
                    heading_candidates.append(line)
    if not heading_candidates:
        return {"title": title_text, "outline": []}
    style_properties = defaultdict(list)
    for h in heading_candidates:
        try:
            style_key = (mode([round(s['size']) for s in h['spans']]), any('bold' in s['font'].lower() for s in h['spans']))
        except StatisticsError: continue
        style_properties[style_key].append(h['bbox'][0])
    ranked_styles = [{"size": s[0], "bold": s[1], "x0": median(x0s), "style_key": s} for s, x0s in style_properties.items()]
    ranked_styles.sort(key=lambda x: (-x["size"], x["x0"]))
    style_to_level = {s["style_key"]: f"H{min(i+1, 3)}" for i, s in enumerate(ranked_styles[:3])}
    outline = []
    for line in heading_candidates:
        try:
            style_key = (mode([round(s['size']) for s in line['spans']]), any('bold' in s['font'].lower() for s in line['spans']))
        except StatisticsError: style_key = None
        level = style_to_level.get(style_key, "H3")
        outline.append({"level": level, "text": line["text"], "page": line["page"]})
    return {"title": title_text, "outline": outline, "doc_structure": doc_structure}

def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
# --- End of your provided parsing code ---

# Function to get content between two headings
def get_content_between_headings(doc_structure, heading1_page, heading1_bbox, heading2_page, heading2_bbox):
    content_text = []
    
    for page_data in doc_structure:
        if page_data['page_num'] < heading1_page or page_data['page_num'] > heading2_page:
            continue
        
        for block in page_data['blocks']:
            if (page_data['page_num'] == heading1_page and block['bbox'][1] < heading1_bbox[3]):
                continue
            if (page_data['page_num'] == heading2_page and block['bbox'][3] > heading2_bbox[1]):
                continue
            
            block_text = " ".join([line['text'] for line in block['lines']])
            content_text.append(block_text)

    return " ".join(content_text)

def extract_keywords(text):
    action_words = set([
        "developed", "led", "managed", "designed", "implemented", "organized", 
        "conducted", "created", "built", "optimized", "increased", "supported",
        "recruited", "achieved", "published", "ranked"
    ])
    
    sentences = re.split(r'[.!?]', text)
    filtered_sentences = [s.strip() for s in sentences if 3 <= len(s.split()) <= 20 and s.strip()]
    
    found_action_words = [word for word in text.lower().split() if word in action_words]
    
    return {
        "short_sentences": filtered_sentences,
        "action_words": sorted(list(set(found_action_words))),
        "full_text": text
    }

class ResumeProcessor(FileSystemEventHandler):
    """
    Handles file system events in the input directory to process resumes.
    """
    def on_created(self, event):
        """Called when a file or directory is created."""
        if not event.is_directory and event.src_path.endswith(".pdf"):
            print(f"\n--- New resume detected: {event.src_path} ---")
            self.process_resume(event.src_path)

    def process_resume(self, file_path):
        """
        Parses a single resume file using your provided structural parsing logic
        and extracts key information for a candidate profile.
        """
        try:
            start_time = time.time()
            
            # Step 1: Structural Parsing
            result = extract_pdf_outline(file_path, CONFIG)
            
            if "error" in result:
                print(f"Skipping file due to parsing error: {result['error']}")
                return

            doc_structure = result.pop("doc_structure")
            
            # Step 2: Extract content for each heading
            structured_content = {}
            headings = result.get('outline', [])
            
            headings_with_bbox = []
            for h in headings:
                bbox_found = False
                for page_data in doc_structure:
                    if page_data['page_num'] == h['page']:
                        for block in page_data['blocks']:
                            for line in block['lines']:
                                if line['text'] == h['text']:
                                    h['bbox'] = line['bbox']
                                    headings_with_bbox.append(h)
                                    bbox_found = True
                                    break
                            if bbox_found: break
                    if bbox_found: break
            
            # Append the end of the document as a "dummy" heading
            end_of_doc_bbox = (0, doc_structure[-1]['page_height'], doc_structure[-1]['page_width'], doc_structure[-1]['page_height'])
            headings_with_bbox.append({"text": "End of Document", "page": len(doc_structure), "bbox": end_of_doc_bbox})

            for i in range(len(headings_with_bbox) - 1):
                h1 = headings_with_bbox[i]
                h2 = headings_with_bbox[i+1]
                
                content_text = get_content_between_headings(doc_structure, h1['page'], h1['bbox'], h2['page'], h2['bbox'])
                structured_content[h1['text']] = extract_keywords(content_text)
            
            # Create a final candidate profile
            candidate_profile = {
                "title": result.get("title", ""),
                "headings": [h['text'] for h in result.get("outline", [])],
                "content_by_heading": structured_content
            }
            
            elapsed = time.time() - start_time
            print(f"Time taken to parse: {elapsed:.2f} seconds")
            
            # Save the result to a JSON file
            filename = os.path.basename(file_path)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            save_json(candidate_profile, output_path)
            print(f"Candidate profile saved to {output_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # Get the directory where the script is located, regardless of the current working directory
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Define absolute paths for input and output folders
    INPUT_FOLDER = os.path.join(SCRIPT_DIR, "input")
    OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "output")
    
    # Ensure input and output folders exist
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Start the file system observer with absolute paths
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