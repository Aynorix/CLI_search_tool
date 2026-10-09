"""Find the PDF pages most relevant to a natural-language query."""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

from pypdf import PdfReader


DEFAULT_PDF = Path(__file__).parent / "data" / "assignment1-pdf.pdf"
WORD_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def extract_pages(pdf_path: Path) -> tuple[int, list[tuple[int, str]]]:
    """Return (1-based page number, selectable text) for non-empty pages."""
    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                pages.append((page_number, text))
        return len(reader.pages), pages
    except Exception as exc:
        raise RuntimeError(f"Could not read '{pdf_path}': {exc}") from exc


def make_snippet(text: str, query: str, limit: int = 320) -> str:
    """Choose the sentence with the strongest query-term overlap."""
    query_terms = {word.lower() for word in WORD_RE.findall(query)}
    sentences = [part.strip() for part in SENTENCE_RE.split(text) if part.strip()]
    if not sentences:
        sentences = [text]

    def overlap(sentence: str) -> tuple[int, int]:
        terms = {word.lower() for word in WORD_RE.findall(sentence)}
        return len(query_terms & terms), -len(sentence)

    best = max(sentences, key=overlap)
    if len(best) > limit:
        best = best[: limit - 3].rsplit(" ", 1)[0] + "..."
    return best


def search(
    pdf_path: Path, query: str, top_k: int
) -> tuple[int, int, list[tuple[int, float, str]]]:
    total_page_count, pages = extract_pages(pdf_path)
    if not pages:
        raise ValueError(
            "No selectable text was found in this PDF. Choose a text-based PDF "
            "or OCR the scanned document first."
        )

    def terms(text: str) -> list[str]:
        words = [word.lower() for word in WORD_RE.findall(text)]
        return words + [f"{left} {right}" for left, right in zip(words, words[1:])]

    page_terms = [terms(text) for _, text in pages]
    document_frequency = Counter(term for doc in page_terms for term in set(doc))
    document_count = len(page_terms)
    idf = {
        term: math.log((1 + document_count) / (1 + frequency)) + 1
        for term, frequency in document_frequency.items()
    }

    def normalized_vector(document_terms: list[str]) -> dict[str, float]:
        frequencies = Counter(document_terms)
        weights = {
            term: (1 + math.log(count)) * idf[term]
            for term, count in frequencies.items()
            if term in idf
        }
        magnitude = math.sqrt(sum(weight * weight for weight in weights.values()))
        return {term: weight / magnitude for term, weight in weights.items()} if magnitude else {}

    query_vector = normalized_vector(terms(query))
    ranked = []
    for (page_number, text), document in zip(pages, page_terms):
        page_vector = normalized_vector(document)
        score = sum(query_weight * page_vector.get(term, 0.0) for term, query_weight in query_vector.items())
        ranked.append((page_number, score, text))
    ranked.sort(key=lambda result: (-result[1], result[0]))
    results = [
        (page_num, score, make_snippet(text, query))
        for page_num, score, text in ranked[: min(top_k, len(ranked))]
        if score > 0
    ]
    return total_page_count, len(pages), results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find the pages in a selectable-text PDF that best match a query."
    )
    parser.add_argument(
        "query", nargs="*", help="words or a question to search for (omit for interactive prompts)"
    )
    parser.add_argument(
        "--top-k", type=int, default=None, help="maximum number of matching pages (default: 5)"
    )
    return parser.parse_args()


def ask_for_query() -> str:
    return input("What should I search for? ").strip()


def ask_for_top_k(default: int = 5) -> int:
    while True:
        value = input(f"How many matching pages should I show? [{default}]: ").strip()
        if not value:
            return default
        try:
            top_k = int(value)
        except ValueError:
            print("Enter a whole number, such as 5.")
            continue
        if top_k > 0:
            return top_k
        print("Enter a number greater than zero.")


def main() -> int:
    args = parse_args()
    interactive = not args.query
    pdf_path = DEFAULT_PDF
    try:
        query = " ".join(args.query).strip() if args.query else ask_for_query()
        top_k = args.top_k if args.top_k is not None else (ask_for_top_k() if interactive else 5)
    except EOFError:
        print("\nInput ended before the search could start.", file=sys.stderr)
        return 2

    if not query:
        print("Error: enter a non-empty search query.", file=sys.stderr)
        return 2
    if top_k < 1:
        print("Error: --top-k must be at least 1.", file=sys.stderr)
        return 2
    if not pdf_path.is_file():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    try:
        total_page_count, searchable_page_count, results = search(pdf_path, query, top_k)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"PDF: {pdf_path}")
    print(f"Indexed {searchable_page_count} of {total_page_count} pages with selectable text.")
    print(f"Query: {query}")
    if not results:
        print("No matching page text was found. Try different or more specific terms.")
        return 0

    print(f"\nTop {len(results)} matching page(s):")
    for rank, (page_number, score, snippet) in enumerate(results, start=1):
        print(f"\n{rank}. Page {page_number}  (similarity: {score:.3f})")
        print(f"   {snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
