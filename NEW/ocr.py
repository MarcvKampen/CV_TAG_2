"""
OCR Processing Module for CV Documents.

Uses the Mistral OCR API to extract text from PDF files.
"""

import random
import time
from pathlib import Path

import httpx
from mistralai import Mistral, OCRResponse

from config import DOWNLOADED_CVS_DIR, OCR_MODEL, OCR_TEXTS_DIR

# Mistral Client Configuration


def retry_with_backoff(func, max_retries=5, initial_backoff=1, backoff_factor=2, jitter=0.1):
    """Decorator to retry a function with exponential backoff on network errors."""

    def wrapper(*args, **kwargs):
        retries = 0
        backoff = initial_backoff
        while True:
            try:
                return func(*args, **kwargs)
            except (
                httpx.ReadTimeout,
                httpx.ConnectTimeout,
                httpx.ConnectError,
                httpx.NetworkError,
            ) as e:
                if retries >= max_retries:
                    print(f"  - ERROR: Request failed after {max_retries} retries. Last error: {e}")
                    raise
                sleep_time = backoff + random.uniform(0, jitter)
                print(f"  - WARNING: Network error: {e}. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                retries += 1
                backoff *= backoff_factor

    return wrapper


@retry_with_backoff
def upload_file(client: Mistral, file_name: str, file_content: bytes):
    """Upload a file to Mistral for OCR processing."""
    print(f"  - Uploading {file_name}...")
    return client.files.upload(
        file={"file_name": file_name, "content": file_content},
        purpose="ocr",
    )


@retry_with_backoff
def get_signed_url(client: Mistral, file_id: str):
    """Get a signed URL for the uploaded file."""
    return client.files.get_signed_url(file_id=file_id, expiry=5)


@retry_with_backoff
def process_ocr(client: Mistral, signed_url: str) -> OCRResponse:
    """Send the file to the OCR model for processing."""
    print("  - Sending file to OCR model...")
    return client.ocr.process(
        document={"type": "document_url", "document_url": signed_url},
        model=OCR_MODEL,
        include_image_base64=True,
        table_format="html",
    )


def get_combined_markdown(ocr_response: OCRResponse) -> str:
    """Combine OCR text from all pages into a single markdown document."""
    pages = []
    for i, page in enumerate(ocr_response.pages):
        page_markdown = page.markdown

        # Remove image placeholders (we only need the text)
        for img in page.images:
            placeholder = f"![{img.id}]({img.id})"
            page_markdown = page_markdown.replace(placeholder, "")
            base64_placeholder = f"![{img.id}]({img.image_base64})"
            page_markdown = page_markdown.replace(base64_placeholder, "")

        pages.append(page_markdown)

    return "\n\n---\n\n".join(pages)


def process_single_pdf(pdf_path: Path, api_key: str) -> str | None:
    """
    Process a single PDF file with OCR and return the extracted markdown text.

    Args:
        pdf_path: Path to the PDF file
        api_key: Mistral API key

    Returns:
        Extracted markdown text, or None if already cached
    """
    print(f"\n{'=' * 20}\nProcessing: {pdf_path.name}\n{'=' * 20}")

    output_md_path = OCR_TEXTS_DIR / f"{pdf_path.stem}.md"

    # Check cache
    if output_md_path.exists():
        print("  - Result already exists. Skipping OCR.")
        return output_md_path.read_text(encoding="utf-8")

    # Initialize client and process
    client = Mistral(api_key=api_key)

    uploaded_file = upload_file(client, pdf_path.name, pdf_path.read_bytes())
    signed_url_response = get_signed_url(client, uploaded_file.id)
    ocr_response = process_ocr(client, signed_url_response.url)

    print("  - Combining extracted text...")
    combined_markdown = get_combined_markdown(ocr_response)

    # Save to cache
    output_md_path.write_text(combined_markdown, encoding="utf-8")
    print(f"  - SUCCESS: Saved to {output_md_path}")

    return combined_markdown
