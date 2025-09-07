from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io

# Import helper functions and models
from models import ProofreadRequest, InteractiveEditRequest
from doc_handler import extract_text_from_docx, create_formatted_docx
from ai_processor import process_text_with_gemini, perform_interactive_edit, generate_glossary_and_consistency_report

# --- App Initialization ---
app = FastAPI(
    title="AI Publishing Assistant API",
    description="An API to proofread and format voice-typed book drafts.",
    version="1.0.0"
)

# --- CORS Middleware ---
# This allows your frontend (running on a different address) to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/process-document/", response_class=StreamingResponse)
async def process_document(
    # We use Form fields because we are also uploading a file
    author_persona: str = Form(...),
    book_summary: str = Form(...),
    font_family: str = Form("Times New Roman"),
    font_size: int = Form(12),
    line_spacing: float = Form(1.5),
    margin_top: float = Form(1.0),
    margin_bottom: float = Form(1.0),
    margin_left: float = Form(1.0),
    margin_right: float = Form(1.0),
    language_rules: str = Form(""),
    file: UploadFile = File(...)
):
    """
    Main endpoint to upload, process, and download a formatted document.
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file.")

    try:
        # Create a Pydantic model instance from the form data for validation and easier use
        params = ProofreadRequest(
            author_persona=author_persona,
            book_summary=book_summary,
            font_family=font_family,
            font_size=font_size,
            line_spacing=line_spacing,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            language_rules=language_rules
        )

        # Read the content of the uploaded file into a BytesIO stream
        file_content_stream = io.BytesIO(await file.read())

        # Step 1: Extract text from the document
        raw_text = extract_text_from_docx(file_content_stream)

        # Step 2: Process text with the AI
        edited_text = process_text_with_gemini(raw_text, params)

        # Step 3: Create the newly formatted .docx file in memory
        output_stream = create_formatted_docx(edited_text, params)

        # Step 4: Stream the document back to the user for download
        return StreamingResponse(
            output_stream,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition': f'attachment; filename="edited_{file.filename}"'}
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        # A generic catch-all for unexpected errors
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.post("/interactive-edit/")
async def interactive_edit_endpoint(request: InteractiveEditRequest):
    """
    Endpoint for performing quick, targeted edits on a piece of text.
    """
    try:
        edited_snippet = perform_interactive_edit(request)
        return {"edited_snippet": edited_snippet}
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))


@app.post("/analyze-document/")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to generate a glossary and consistency report without editing.
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file.")
        
    try:
        file_content_stream = io.BytesIO(await file.read())
        raw_text = extract_text_from_docx(file_content_stream)
        report = await generate_glossary_and_consistency_report(raw_text)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze document: {e}")


# To run the app: `uvicorn main:app --reload` in your terminal
