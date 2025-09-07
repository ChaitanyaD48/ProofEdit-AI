from pydantic import BaseModel, Field

class ProofreadRequest(BaseModel):
    """
    Defines the structure of the data expected for the main proofreading task.
    """
    author_persona: str = Field(..., example="An 85-year-old retired professor of philosophy...")
    book_summary: str = Field(..., example="A reflective memoir on the changing world.")
    font_family: str = Field(default="Times New Roman", example="Arial")
    font_size: int = Field(default=12, example=12)
    line_spacing: float = Field(default=1.5, example=1.5)
    margin_top: float = Field(default=1.0, example=1.0)
    margin_bottom: float = Field(default=1.0, example=1.0)
    margin_left: float = Field(default=1.0, example=1.0)
    margin_right: float = Field(default=1.0, example=1.0)
    language_rules: str = Field(default="Italicize all Sanskrit words.", example="Place Hindi dialogue in quotes.")
    # We will add other fields like consistency checks later as features expand.

class InteractiveEditRequest(BaseModel):
    """
    Defines the structure for interactive, on-the-fly editing of a text snippet.
    """
    text_snippet: str = Field(..., example="the boy ran fastly to the store")
    command: str = Field(..., example="Rephrase this more formally.")
