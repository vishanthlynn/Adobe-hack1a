import os
import json
import statistics
import unicodedata
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar

INPUT_DIR = "input"
OUTPUT_DIR = "output"


class PDFProcessor:
    def process_pdf_outline(self, filename: str) -> dict:
        pdf_path = os.path.join(INPUT_DIR, filename)
        title = self._extract_title(pdf_path)
        headings = self._detect_headings(pdf_path)
        return {"title": title, "outline": headings}

    def _extract_title(self, pdf_path: str) -> str:
        title_candidate = {"text": os.path.basename(pdf_path), "score": 0}
        for page in extract_pages(pdf_path, maxpages=1):
            page_height = page.bbox[3] if page.bbox else 1000
            for element in self._merge_adjacent_textboxes(
                [el for el in page if isinstance(el, LTTextBox)]
            ):
                text = element.get_text().strip()
                if 3 < len(text.split()) < 15 and text:
                    avg_size, is_bold = self._get_text_features(element)
                    centered = abs((element.x0 + element.x1) / 2 - 300) < 100
                    top_third = element.y1 > (2 * page_height / 3)
                    score = avg_size + (5 if is_bold else 0)
                    if centered:
                        score += 3
                    if top_third:
                        score += 2
                    if score > title_candidate["score"]:
                        title_candidate["score"] = score
                        title_candidate["text"] = text
        return title_candidate["text"]

    def _detect_headings(self, pdf_path: str):
        candidates = []
        for page_num, page in enumerate(extract_pages(pdf_path), 1):
            page_height = page.bbox[3] if page.bbox else 1000
            merged_elements = self._merge_adjacent_textboxes(
                [el for el in page if isinstance(el, LTTextBox)]
            )
            for element in merged_elements:
                text = element.get_text().strip()
                if self._is_likely_heading(text):
                    avg_size, is_bold = self._get_text_features(element)
                    if avg_size > 11:
                        center_aligned = abs((element.x0 + element.x1) / 2 - 300) < 100
                        top_third = element.y1 > (2 * page_height / 3)
                        candidates.append({
                            "text": text, "size": avg_size, "bold": is_bold,
                            "page": page_num, "y_pos": element.y1,
                            "centered": center_aligned, "top_third": top_third
                        })
        return self._classify_headings_by_font(candidates)

    def _is_cased_language(self, text: str) -> bool:
        return any(unicodedata.category(c) in ('Lu', 'Ll') for c in text)

    def _is_likely_heading(self, text: str) -> bool:
        if not text or len(text.split()) > 20 or len(text) > 150:
            return False
        if text.endswith('.') or text.endswith(','):
            return False
        if text.isdigit():
            return False
        if any('\u4e00' <= c <= '\u9fff' for c in text):  # CJK
            return True
        if self._is_cased_language(text):
            if text.istitle() or text.isupper():
                return True
        if any(char.isdigit() for char in text[:3]):
            return True
        return False

    def _get_text_features(self, element: LTTextBox):
        sizes, names = [], []
        for text_line in element:
            if isinstance(text_line, LTTextLine):
                for char in text_line:
                    if isinstance(char, LTChar) and char.get_text().strip():
                        sizes.append(char.size)
                        names.append(char.fontname)
        return (statistics.mean(sizes) if sizes else 0, any('bold' in n.lower() for n in names))

    def _classify_headings_by_font(self, candidates):
        if not candidates:
            return []
        sizes = [c['size'] for c in candidates]
        try:
            h1_threshold = statistics.quantiles(sizes, n=10)[-1]
            h2_threshold = statistics.quantiles(sizes, n=4)[-1]
        except statistics.StatisticsError:
            h1_threshold = h2_threshold = max(sizes)
        for c in candidates:
            if c['size'] >= h1_threshold * 0.99 or (c['centered'] and c['top_third']):
                c['level'] = 'H1'
            elif c['size'] >= h2_threshold:
                c['level'] = 'H2'
            else:
                c['level'] = 'H3'
        return [{"text": c['text'], "level": c['level'], "page": c['page'], "y_pos": c['y_pos']} for c in candidates]

    def _merge_adjacent_textboxes(self, textboxes):
        if not textboxes:
            return []

        textboxes = sorted(textboxes, key=lambda b: -b.y1)
        merged_boxes = []
        buffer = []

        def combine_boxes(buffer):
            text = " ".join(b.get_text().strip() for b in buffer if isinstance(b, LTTextBox))
            x0 = min(b.x0 for b in buffer)
            x1 = max(b.x1 for b in buffer)
            y0 = min(b.y0 for b in buffer)
            y1 = max(b.y1 for b in buffer)

            # Return mock LTTextBox-like object
            return type('MergedBox', (), {
                'get_text': lambda self: text,
                'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1,
                '_class_': LTTextBox,
                '__iter__': lambda self: (ch for b in buffer for ch in b)
            })()

        for box in textboxes:
            if not buffer:
                buffer.append(box)
                continue
            last = buffer[-1]
            vertical_close = abs(last.y0 - box.y1) < 5
            horizontal_align = abs((last.x0 + last.x1) / 2 - (box.x0 + box.x1) / 2) < 10
            if vertical_close and horizontal_align:
                buffer.append(box)
            else:
                merged_boxes.append(combine_boxes(buffer))
                buffer = [box]

        if buffer:
            merged_boxes.append(combine_boxes(buffer))

        return merged_boxes


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    processor = PDFProcessor()
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file}...")
        result = processor.process_pdf_outline(pdf_file)
        output_filename = pdf_file.replace('.pdf', '.json')
        with open(os.path.join(OUTPUT_DIR, output_filename), 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()