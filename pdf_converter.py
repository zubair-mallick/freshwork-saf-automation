"""Convert Aadhar.pdf pages to individual PNG images."""

import os
import fitz  # PyMuPDF


def convert_pdf_to_images(pdf_path, names, output_dir, dpi=200):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    if len(names) != len(doc):
        print(f"    ⚠ Name count ({len(names)}) != PDF page count ({len(doc)})")

    image_paths = []
    for i, page in enumerate(doc):
        if i >= len(names):
            break
        safe_name = names[i].strip().replace(" ", "_")
        out_path = os.path.join(output_dir, f"{safe_name}.png")
        pix = page.get_pixmap(dpi=dpi)
        pix.save(out_path)
        size_kb = os.path.getsize(out_path) / 1024
        print(f"    > Page {i+1} -> {safe_name}.png ({size_kb:.0f} KB)")
        image_paths.append(out_path)

    doc.close()
    return image_paths
