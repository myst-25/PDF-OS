"""
core/editing.py
Watermarks, text insertion, headers/footers, redaction.
"""
import fitz  # PyMuPDF
import os


def add_text_watermark(input_path: str, output_path: str, text: str = "CONFIDENTIAL",
                       fontsize: int = 60, color: tuple = (0.8, 0.8, 0.8),
                       rotation: float = -45, opacity: float = 0.3, pages: list = None):
    """Add a text watermark across pages."""
    doc = fitz.open(input_path)
    page_set = set(p - 1 for p in pages) if pages else set(range(len(doc)))

    for i in page_set:
        page = doc[i]
        rect = page.rect
        # Center the watermark text
        center_x = rect.width / 2
        center_y = rect.height / 2
        text_point = fitz.Point(center_x - fontsize * len(text) * 0.15, center_y)
        page.insert_text(
            text_point, text,
            fontsize=fontsize,
            color=color,
            rotate=int(rotation),
            overlay=True,
        )

    doc.save(output_path)
    doc.close()
    return output_path


def add_image_watermark(input_path: str, output_path: str, image_path: str,
                        opacity: float = 0.3, scale: float = 0.5, pages: list = None):
    """Add an image watermark across pages."""
    doc = fitz.open(input_path)
    page_set = set(p - 1 for p in pages) if pages else set(range(len(doc)))

    for i in page_set:
        page = doc[i]
        rect = page.rect
        img_w = rect.width * scale
        img_h = rect.height * scale
        x = (rect.width - img_w) / 2
        y = (rect.height - img_h) / 2
        img_rect = fitz.Rect(x, y, x + img_w, y + img_h)
        page.insert_image(img_rect, filename=image_path, overlay=True)

    doc.save(output_path)
    doc.close()
    return output_path


def add_header(input_path: str, output_path: str, text: str,
               fontsize: int = 10, color: tuple = (0, 0, 0), pages: list = None):
    """Add header text to pages."""
    doc = fitz.open(input_path)
    page_set = set(p - 1 for p in pages) if pages else set(range(len(doc)))

    for i in page_set:
        page = doc[i]
        rect = page.rect
        header_point = fitz.Point(rect.width / 2 - fontsize * len(text) * 0.15, 25)
        page.insert_text(header_point, text, fontsize=fontsize, color=color, overlay=True)

    doc.save(output_path)
    doc.close()
    return output_path


def add_footer(input_path: str, output_path: str, text: str,
               fontsize: int = 10, color: tuple = (0, 0, 0),
               include_page_numbers: bool = True, pages: list = None):
    """Add footer text to pages, optionally with page numbers."""
    doc = fitz.open(input_path)
    page_set = set(p - 1 for p in pages) if pages else set(range(len(doc)))

    for i in page_set:
        page = doc[i]
        rect = page.rect
        footer_text = text
        if include_page_numbers:
            footer_text = f"{text}  —  Page {i + 1} of {len(doc)}"
        x = rect.width / 2 - fontsize * len(footer_text) * 0.15
        footer_point = fitz.Point(x, rect.height - 15)
        page.insert_text(footer_point, footer_text, fontsize=fontsize, color=color, overlay=True)

    doc.save(output_path)
    doc.close()
    return output_path


def add_page_numbers(input_path: str, output_path: str, position: str = "bottom-center",
                     fontsize: int = 10, start_num: int = 1):
    """Add page numbers to every page."""
    doc = fitz.open(input_path)

    for i, page in enumerate(doc):
        rect = page.rect
        num_text = str(start_num + i)

        if position == "bottom-center":
            point = fitz.Point(rect.width / 2 - 5, rect.height - 20)
        elif position == "bottom-right":
            point = fitz.Point(rect.width - 40, rect.height - 20)
        elif position == "bottom-left":
            point = fitz.Point(30, rect.height - 20)
        elif position == "top-center":
            point = fitz.Point(rect.width / 2 - 5, 25)
        else:
            point = fitz.Point(rect.width / 2 - 5, rect.height - 20)

        page.insert_text(point, num_text, fontsize=fontsize, color=(0.3, 0.3, 0.3), overlay=True)

    doc.save(output_path)
    doc.close()
    return output_path


def insert_text(input_path: str, output_path: str, page_num: int, x: float, y: float,
                text: str, fontsize: int = 12, color: tuple = (0, 0, 0)):
    """Insert text at a specific position on a page (1-indexed)."""
    doc = fitz.open(input_path)
    page = doc[page_num - 1]
    page.insert_text(fitz.Point(x, y), text, fontsize=fontsize, color=color, overlay=True)
    doc.save(output_path)
    doc.close()
    return output_path


def redact_text(input_path: str, output_path: str, search_text: str,
                fill_color: tuple = (0, 0, 0), pages: list = None):
    """Find and redact (black out) all instances of search_text."""
    doc = fitz.open(input_path)
    page_set = set(p - 1 for p in pages) if pages else set(range(len(doc)))
    redact_count = 0

    for i in page_set:
        page = doc[i]
        instances = page.search_for(search_text)
        for rect in instances:
            page.add_redact_annot(rect, fill=fill_color)
            redact_count += 1
        page.apply_redactions()

    doc.save(output_path)
    doc.close()
    return {"output": output_path, "redactions": redact_count}


def insert_image_on_page(input_path: str, output_path: str, image_path: str,
                         page_num: int, x: float, y: float, width: float, height: float):
    """Insert an image onto a specific page at given coordinates."""
    doc = fitz.open(input_path)
    page = doc[page_num - 1]
    img_rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_image(img_rect, filename=image_path)
    doc.save(output_path)
    doc.close()
    return output_path
