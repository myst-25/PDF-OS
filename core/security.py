"""
core/security.py
Encryption, decryption, passwords, permissions.
"""
from pypdf import PdfReader, PdfWriter


def encrypt_pdf(input_path: str, output_path: str, user_password: str, owner_password: str = None,
                allow_printing: bool = True, allow_copying: bool = False, cancel_event=None):
    """Encrypt a PDF with user and owner passwords."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")
        writer.add_page(page)

    # Copy metadata
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    permissions = 0
    if allow_printing:
        permissions |= 0b000000000100  # print permission
    if allow_copying:
        permissions |= 0b000000010000  # copy permission

    writer.encrypt(
        user_password=user_password,
        owner_password=owner_password or user_password,
        permissions_flag=permissions
    )
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def decrypt_pdf(input_path: str, output_path: str, password: str, cancel_event=None):
    """Remove password protection from a PDF."""
    reader = PdfReader(input_path)
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PdfWriter()
    for page in reader.pages:
        if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")
        writer.add_page(page)
    if reader.metadata:
        writer.add_metadata(reader.metadata)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def is_encrypted(input_path: str) -> bool:
    """Check if a PDF is encrypted."""
    reader = PdfReader(input_path)
    return reader.is_encrypted


def set_permissions(input_path: str, output_path: str, owner_password: str,
                    allow_print: bool = True, allow_copy: bool = True,
                    allow_modify: bool = False, allow_annotate: bool = True, cancel_event=None):
    """Set specific permissions on a PDF."""
    reader = PdfReader(input_path)
    if reader.is_encrypted:
        reader.decrypt(owner_password)
    writer = PdfWriter()
    for page in reader.pages:
        if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")
        writer.add_page(page)

    perms = 0
    if allow_print:
        perms |= 0b000000000100
    if allow_copy:
        perms |= 0b000000010000
    if allow_modify:
        perms |= 0b000000001000
    if allow_annotate:
        perms |= 0b000000100000

    writer.encrypt(
        user_password="",
        owner_password=owner_password,
        permissions_flag=perms
    )
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path
