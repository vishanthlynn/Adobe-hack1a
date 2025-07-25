# PDF Title and Heading Extractor

This project processes PDF files to extract document titles and headings, saving the results as structured JSON files.

## Requirements
- Python 3.7+
- [pdfminer.six](https://github.com/pdfminer/pdfminer.six) (see `requirements.txt`)

## Setup
1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Prepare your PDFs:**
   - Place all PDF files you want to process in the `input` directory.

## Usage
From the project root directory, run:
```sh
python process_pdf_1a.py
```

- The script will process all `.pdf` files in the `input` folder.
- For each PDF, a corresponding `.json` file will be created in the `output` folder.
- Each JSON file contains the extracted title and a list of detected headings (with their levels and positions).

## Input/Output Structure
- `input/` — Place your PDF files here.
- `output/` — Processed JSON files will be saved here, one per PDF.

## Example
Suppose you have `input/8._paragraph_writing.pdf` and `input/13. 이 몸이 죽어가서 autor Seong Sam Mun.pdf`.
After running the script, you will find:
- `output/8._paragraph_writing.json`
- `output/13. 이 몸이 죽어가서 autor Seong Sam Mun.json`

Each JSON file will look like:
```json
{
    "title": "Extracted Title",
    "outline": [
        {"text": "Heading 1", "level": "H1", "page": 1, "y_pos": 700},
        {"text": "Subheading", "level": "H2", "page": 2, "y_pos": 600}
    ]
}
```

## Notes
- The script uses heuristics to detect titles and headings, so results may vary depending on PDF formatting.
- If you add or remove PDFs from the `input` folder, re-run the script to process the new files.
