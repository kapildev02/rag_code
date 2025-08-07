import os
import fitz
from pathlib import Path

def split_pdf(input_pdf, output_folder="split_pages"):
    """Split a multi-page PDF into single-page PDFs, save them in a named folder, and return their paths."""

    # Extract PDF file name without extension
    pdf_name = Path(input_pdf).stem  # e.g., "DataTables" from "DataTables.pdf"
    
    # Create a subfolder inside split_pages using the file name
    pdf_folder = Path(output_folder) / pdf_name
    pdf_folder.mkdir(parents=True, exist_ok=True)

    pdf_doc = fitz.open(input_pdf)
    output_paths = []

    for page_num in range(len(pdf_doc)):
        output_path = pdf_folder / f"page_{page_num + 1}.pdf"
        new_pdf = fitz.open()  # Create a new PDF
        new_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
        new_pdf.save(output_path)
        new_pdf.close()
        output_paths.append(str(output_path))

    return output_paths

# Example usage
pdf_file = "data/pdf/offer.pdf"  # Path to your input PDF
split_pages = split_pdf(pdf_file)

# List all generated split files
print("Generated Files:")
for pdf in split_pages:
    print(pdf)