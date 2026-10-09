# Assignment 1: PDF Page Similarity Search

## Example output

```text
PS C:\Users\Aynorix\OneDrive\Desktop\AI_labwork> .\.venv\Scripts\python.exe search_pdf.py
What should I search for? cloud computing technology
How many matching pages should I show? [5]: 5
PDF: C:\Users\Aynorix\OneDrive\Desktop\AI_labwork\data\assignment1-pdf.pdf
Indexed 100 of 100 pages with selectable text.
Query: cloud computing technology

Top 5 matching page(s):

1. Page 2  (similarity: 1.000)
   Cloud Computing Technology

2. Page 3  (similarity: 0.383)
   Cloud Computing Technology

3. Page 1  (similarity: 0.208)
   CLOUD COMPUTING TECHNOLOGY Huawei Technologies Co., Ltd.

4. Page 70  (similarity: 0.111)
   ______technology is the basic support of cloud computing.

5. Page 5  (similarity: 0.107)
   It is still difficult for beginners to have a more complete understanding of cloud computing technology.
```

This command-line program searches a PDF for the pages most similar to a
question or phrase. It reports page numbers, similarity scores, and relevant
text excerpts.

The program automatically searches the uploaded 100-page
`data/assignment1-pdf.pdf`.
You do not need to paste or upload a PDF path in the terminal.

## Requirements

- Python 3.10 or newer
- A PDF with selectable text

## Setup

Open PowerShell in this folder and install the packages:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Interactive use

Start the program without arguments:

```powershell
.\.venv\Scripts\python.exe search_pdf.py
```

The terminal asks you to:

1. Enter the query or question you want to search for.
2. Choose how many matching pages to display. Press Enter for the default of 5.

Example session:

```text
What should I search for? how does self attention work
How many matching pages should I show? [5]: 3
```

## Command-line use

You can also give the query and options directly:

```powershell
.\.venv\Scripts\python.exe search_pdf.py "cloud computing technology"
.\.venv\Scripts\python.exe search_pdf.py --top-k 3 "cloud computing technology"
```

When a query is given as an argument, the program uses the same included PDF
and shows 5 results by default.

## How it works

The program extracts text page by page with `pypdf`, then represents each page
and the query as TF-IDF vectors. It includes single words and two-word phrases
and ranks pages by cosine similarity. The displayed excerpt comes from the
sentence with the most query-term overlap. PDF page numbers are 1-based.

This is lexical similarity, so wording that appears in the PDF ranks best. It
does not recognize every synonym. Scanned PDFs without selectable text need
OCR before they can be searched. Pages without extractable text are skipped,
and the program reports how many pages were indexed.
