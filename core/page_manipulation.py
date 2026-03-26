"""
core/page_manipulation.py
Merge, split, reorder, delete, extract, rotate, crop, insert, duplicate, reverse pages.
"""
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
import os


def merge_pdfs(pdf_paths: list, output_path: str, cancel_event=None):
    """Merge multiple PDF files into one."""
    writer = PdfWriter()
    for path in pdf_paths:
        if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def split_pdf(input_path: str, output_dir: str, ranges: list = None, cancel_event=None):
    """Split a PDF into multiple files. ranges is a list of (start, end) tuples (1-indexed)."""
    reader = PdfReader(input_path)
    total = len(reader.pages)
    results = []

    if ranges is None:
        # Split into individual pages
        for i in range(total):
            if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            out = os.path.join(output_dir, f"page_{i + 1}.pdf")
            with open(out, "wb") as f:
                writer.write(f)
            results.append(out)
    else:
        for idx, (start, end) in enumerate(ranges):
            if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")
            writer = PdfWriter()
            for i in range(max(0, start - 1), min(end, total)):
                writer.add_page(reader.pages[i])
            out = os.path.join(output_dir, f"split_{idx + 1}_pages_{start}-{end}.pdf")
            with open(out, "wb") as f:
                writer.write(f)
            results.append(out)
    return results


def reorder_pages(input_path: str, output_path: str, new_order: list, cancel_event=None):
    """Reorder pages. new_order is list of 0-indexed page numbers."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for i in new_order:
        writer.add_page(reader.pages[i])
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def delete_pages(input_path: str, output_path: str, pages_to_delete: list, cancel_event=None):
    """Delete specific pages (1-indexed)."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    delete_set = set(p - 1 for p in pages_to_delete)
    for i, page in enumerate(reader.pages):
        if i not in delete_set:
            writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def extract_pages(input_path: str, output_path: str, page_numbers: list, cancel_event=None):
    """Extract specific pages (1-indexed) into a new PDF."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for p in page_numbers:
        writer.add_page(reader.pages[p - 1])
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def rotate_pages(input_path: str, output_path: str, pages: list, angle: int, cancel_event=None):
    """Rotate specific pages (1-indexed) by angle (90, 180, 270)."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    rotate_set = set(p - 1 for p in pages) if pages else set(range(len(reader.pages)))
    for i, page in enumerate(reader.pages):
        if i in rotate_set:
            page.rotate(angle)
        writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def crop_pages(input_path: str, output_path: str, left: float, top: float, right: float, bottom: float, pages: list = None, cancel_event=None):
    """Crop pages by setting media box. Values are in points from edges."""
    doc = fitz.open(input_path)
    page_set = set(p - 1 for p in pages) if pages else set(range(len(doc)))
    for i in page_set:
        page = doc[i]
        rect = page.rect
        new_rect = fitz.Rect(rect.x0 + left, rect.y0 + top, rect.x1 - right, rect.y1 - bottom)
        page.set_cropbox(new_rect)
    doc.save(output_path)
    doc.close()
    return output_path


def insert_blank_page(input_path: str, output_path: str, position: int, width: float = 612, height: float = 792):
    """Insert a blank page at position (0-indexed)."""
    doc = fitz.open(input_path)
    doc.new_page(pno=position, width=width, height=height)
    doc.save(output_path)
    doc.close()
    return output_path


def insert_pdf_pages(input_path: str, insert_path: str, output_path: str, position: int):
    """Insert all pages from insert_path into input_path at position."""
    doc = fitz.open(input_path)
    insert_doc = fitz.open(insert_path)
    doc.insert_pdf(insert_doc, start_at=position)
    doc.save(output_path)
    doc.close()
    insert_doc.close()
    return output_path


def duplicate_page(input_path: str, output_path: str, page_num: int):
    """Duplicate a specific page (1-indexed) right after its current position."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        if i == page_num - 1:
            writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def reverse_pages(input_path: str, output_path: str, cancel_event=None):
    """Reverse the order of all pages."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reversed(reader.pages):
        writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def get_page_count(input_path: str) -> int:
    """Get total number of pages."""
    reader = PdfReader(input_path)
    return len(reader.pages)


def get_page_dimensions(input_path: str, page_num: int = 1):
    """Get width and height of a page (1-indexed) in points."""
    doc = fitz.open(input_path)
    page = doc[page_num - 1]
    rect = page.rect
    doc.close()
    return rect.width, rect.height
