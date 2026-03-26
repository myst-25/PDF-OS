"""
core/extraction.py
Extract text, images, tables, metadata, fonts, links, bookmarks, attachments from PDFs.
"""
import fitz  # PyMuPDF
import os
import json


def extract_text(input_path: str, page_numbers: list = None, cancel_event=None) -> str:
    """Extract text from all or specific pages."""
    doc = fitz.open(input_path)
    text = ""
    pages = page_numbers or range(1, len(doc) + 1)
    for p in pages:
        if cancel_event:
            if cancel_event.is_set(): raise Exception("Cancelled by user")
            import time; time.sleep(0.005)
        text += doc[p - 1].get_text() + "\n"
    doc.close()
    return text


def extract_images(input_path: str, output_dir: str, cancel_event=None):
    """Extract all embedded images from a PDF."""
    doc = fitz.open(input_path)
    results = []
    img_count = 0
    for page_num in range(len(doc)):
        if cancel_event:
            if cancel_event.is_set(): raise Exception("Cancelled by user")
            import time; time.sleep(0.005)
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_idx, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            img_count += 1
            out_path = os.path.join(output_dir, f"image_{img_count}.{ext}")
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            results.append(out_path)
    doc.close()
    return results


def extract_tables(input_path: str, output_dir: str = None, cancel_event=None):
    """Extract tables from PDF using pdfplumber."""
    import pdfplumber

    all_tables = []
    with pdfplumber.open(input_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            if cancel_event:
                if cancel_event.is_set(): raise Exception("Cancelled by user")
                import time; time.sleep(0.005)
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                all_tables.append({
                    "page": page_num + 1,
                    "table_index": t_idx,
                    "data": table
                })

    if output_dir:
        import csv
        for t in all_tables:
            out = os.path.join(output_dir, f"table_p{t['page']}_{t['table_index']}.csv")
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for row in t["data"]:
                    writer.writerow([cell if cell else "" for cell in row])
    return all_tables


def extract_metadata(input_path: str) -> dict:
    """Get PDF metadata."""
    doc = fitz.open(input_path)
    meta = doc.metadata
    meta["page_count"] = len(doc)
    meta["file_size"] = os.path.getsize(input_path)
    doc.close()
    return meta


def set_metadata(input_path: str, output_path: str, metadata: dict):
    """Set PDF metadata (title, author, subject, keywords, creator, producer)."""
    doc = fitz.open(input_path)
    doc.set_metadata(metadata)
    doc.save(output_path)
    doc.close()
    return output_path


def extract_hyperlinks(input_path: str, cancel_event=None) -> list:
    """Extract all hyperlinks from a PDF."""
    doc = fitz.open(input_path)
    links = []
    for page_num in range(len(doc)):
        if cancel_event:
            if cancel_event.is_set(): raise Exception("Cancelled by user")
            import time; time.sleep(0.005)
        page = doc[page_num]
        for link in page.get_links():
            if link.get("uri"):
                links.append({
                    "page": page_num + 1,
                    "uri": link["uri"],
                    "rect": list(link["from"])
                })
    doc.close()
    return links


def extract_bookmarks(input_path: str) -> list:
    """Extract bookmarks/outline from PDF."""
    doc = fitz.open(input_path)
    toc = doc.get_toc()
    doc.close()
    return [{"level": item[0], "title": item[1], "page": item[2]} for item in toc]


def extract_fonts(input_path: str, cancel_event=None) -> list:
    """List all fonts used in the PDF."""
    doc = fitz.open(input_path)
    fonts = set()
    for page in doc:
        if cancel_event:
            if cancel_event.is_set(): raise Exception("Cancelled by user")
            import time; time.sleep(0.005)
        for font in page.get_fonts():
            fonts.add((font[3], font[4]))  # name, encoding
    doc.close()
    return [{"name": f[0], "encoding": f[1]} for f in fonts]


def extract_attachments(input_path: str, output_dir: str) -> list:
    """Extract embedded file attachments from PDF."""
    doc = fitz.open(input_path)
    results = []
    count = doc.embfile_count()
    for i in range(count):
        info = doc.embfile_info(i)
        data = doc.embfile_get(i)
        name = info.get("filename", f"attachment_{i}")
        out = os.path.join(output_dir, name)
        with open(out, "wb") as f:
            f.write(data)
        results.append(out)
    doc.close()
    return results


def full_text_search(input_path: str, query: str, cancel_event=None) -> list:
    """Search for text in all pages and return positions."""
    doc = fitz.open(input_path)
    results = []
    for page_num in range(len(doc)):
        if cancel_event:
            if cancel_event.is_set(): raise Exception("Cancelled by user")
            import time; time.sleep(0.005)
        page = doc[page_num]
        instances = page.search_for(query)
        for rect in instances:
            results.append({
                "page": page_num + 1,
                "rect": [rect.x0, rect.y0, rect.x1, rect.y1]
            })
    doc.close()
    return results
