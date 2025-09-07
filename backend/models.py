from pydantic import BaseModel, Field
from typing import List, Optional

# --- New Model for Heading Styles ---
class HeadingStyle(BaseModel):
    font_size: int = 24
    bold: bool = True

# --- Stage 1: Analysis ---
class AnalysisResponse(BaseModel):
    """
    Response from the initial document analysis.
    """
    raw_text: str
    detected_languages: List[str]

# --- Stage 2: Finalization ---
class SanskritShlokaOptions(BaseModel):
    """
    Detailed formatting options specifically for Sanskrit shlokas.
    """
    center_align: bool = True
    line_breaks: bool = True
    add_numbering: bool = False
    translation_style: str = "Below the shloka in plain text"

class FormattingOptions(BaseModel):
    """
    A comprehensive model for all user-selected formatting.
    """
    margins: float = 1.0
    line_spacing: float = 1.5
    font_family: str = "Times New Roman"
    font_size: int = 12
    heading1: HeadingStyle = Field(default_factory=HeadingStyle)
    heading2: HeadingStyle = Field(default_factory=lambda: HeadingStyle(font_size=18, bold=True))
    sanskrit_shlokas: Optional[SanskritShlokaOptions] = None

class FinalizeRequest(BaseModel):
    """
    Payload for the main AI editing and processing endpoint.
    """
    raw_text: str
    tone: str # Although we won't rewrite for tone, it can provide context for ambiguity.
    generate_glossary: bool = True
    formatting_options: FormattingOptions

# --- Stage 3: Download ---
class GlossaryItem(BaseModel):
    term: str
    transliteration: str
    translation: str
    context: Optional[str] = None

class FinalDocumentData(BaseModel):
    """
    Data required to generate the final .docx file.
    This is sent from the frontend for the download step.
    """
    edited_manuscript: str
    glossary: List[GlossaryItem]
    # Global formatting
    font_family: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 1.5
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    # Heading formatting
    heading1: HeadingStyle = Field(default_factory=HeadingStyle)
    heading2: HeadingStyle = Field(default_factory=lambda: HeadingStyle(font_size=18, bold=True))

