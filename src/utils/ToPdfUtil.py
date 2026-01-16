import logging
import os
import tempfile
import time
from fpdf import FPDF
from PIL import Image
import pdfkit
import subprocess


def convert_file_to_pdf(input_file, output_file):
    ext = os.path.splitext(input_file)[-1].lower()
    output_path = None

    if ext == ".txt":
        output_path = txt_to_pdf(input_file, output_file)
    elif ext == ".docx":
        output_path = docx_to_pdf(input_file, output_file)
    elif ext == ".xlsx":
        output_path = xlsx_to_pdf(input_file, output_file)
    elif ext in [".jpg", ".jpeg", ".png"]:
        output_path = image_to_pdf(input_file, output_file)
    elif ext == ".html":
        output_path = html_to_pdf(input_file, output_file)
    else:
        output_path = convert_to_pdf(input_file, os.path.dirname(output_file))

    return os.path.exists(output_path)


def txt_to_pdf(txt_file, pdf_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with open(txt_file, 'r', encoding='utf-8') as file:
        for line in file:
            pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=True)

    pdf.output(pdf_file)
    return pdf_file


def docx_to_pdf(docx_file, pdf_file):
    return convert_with_libreoffice(docx_file, pdf_file)


def xlsx_to_pdf(xlsx_file, pdf_file):
    return convert_with_libreoffice(xlsx_file, pdf_file)


def image_to_pdf(image_file, pdf_file):
    image = Image.open(image_file)
    image.save(pdf_file, "PDF", resolution=100.0)
    return pdf_file


def html_to_pdf(html_file, pdf_file):
    try:
        pdfkit.from_file(html_file, pdf_file)
        return pdf_file
    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        return f"转PDF失败: {str(e)}"

def convert_to_pdf(input_file, output_dir):
    return convert_with_libreoffice(input_file, os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[
        0] + ".pdf"))


def convert_with_libreoffice(input_file, pdf_file):
    output_dir = os.path.dirname(pdf_file)
    subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', input_file, '--outdir', output_dir])
    return pdf_file
