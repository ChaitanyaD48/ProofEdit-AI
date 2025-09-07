from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.text import WD_LINE_SPACING
import io

from models import ProofreadRequest

def extract_text_from_docx(docx_file_stream: io.BytesIO) -> str:
    """
    Reads a .docx file stream and returns its raw text content.
    """
    try:
        document = Document(docx_file_stream)
        full_text = [para.text for para in document.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        # Ideally, log this error
        print(f"Error reading docx file: {e}")
        raise ValueError("Could not process the uploaded .docx file.")


def create_formatted_docx(text_content: str, params: ProofreadRequest) -> io.BytesIO:
    """
    Creates a new .docx file in memory with specified formatting and text.
    """
    document = Document()
    
    # --- Apply Margins ---
    sections = document.sections
    for section in sections:
        section.top_margin = Inches(params.margin_top)
        section.bottom_margin = Inches(params.margin_bottom)
        section.left_margin = Inches(params.margin_left)
        section.right_margin = Inches(params.margin_right)

    # --- Set Font and Line Spacing for the 'Normal' style ---
    style = document.styles['Normal']
    font = style.font
    font.name = params.font_family
    font.size = Pt(params.font_size)
    
    paragraph_format = style.paragraph_format
    if params.line_spacing == 1.0:
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    elif params.line_spacing == 1.5:
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    elif params.line_spacing == 2.0:
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    else:
        paragraph_format.line_spacing = Pt(params.font_size * params.line_spacing)

    # --- Add AI-processed text ---
    # Split the content by newlines and add as separate paragraphs
    # This preserves the paragraph structure from the AI output
    for para_text in text_content.split('\n'):
        if para_text.strip(): # Avoid adding empty paragraphs
            document.add_paragraph(para_text)

    # --- Save to a memory buffer ---
    file_stream = io.BytesIO()
    document.save(file_stream)
    file_stream.seek(0) # Rewind the buffer to the beginning
    
    return file_stream
