import os
from pathlib import Path
from docling.document_converter import DocumentConverter

source_root = "./split_pages/"  # Root folder containing subfolders with PDFs
output_root = "./output/"       # Root folder to store Markdown files

# Ensure the output folder exists
os.makedirs(output_root, exist_ok=True)

converter = DocumentConverter()
supported_extensions = (".pdf", ".docx", ".txt", ".pptx", ".html")

print()
# Iterate over each subfolder inside split_pages
for subfolder in os.listdir(source_root):
    subfolder_path = Path(source_root) / subfolder

    # Ensure it's a directory (not a file)
    if subfolder_path.is_dir():
        output_subfolder = Path(output_root) / subfolder  # Create corresponding output subfolder
        output_subfolder.mkdir(parents=True, exist_ok=True)

        # Process each PDF file inside the subfolder
        for filename in os.listdir(subfolder_path):
            if filename.lower().endswith(supported_extensions):  # Ensure it's a pdf file
                source_path = subfolder_path / filename
                # output_filename = filename.replace(".pdf", ".md")  # Change extension to .md
                output_filename = Path(filename).stem + ".md"
                output_path = output_subfolder / output_filename

                # Convert the PDF to Markdown
                result = converter.convert(str(source_path))
                if result and result.document:
                    result.document.save_as_markdown(str(output_path))  # Save Markdown file
                    print(f"Saved: {output_path}")
                else:
                    print(f"Conversion failed for: {source_path}")