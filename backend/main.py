from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io

from models import AnalysisResponse, FinalizeRequest, FinalDocumentData
from doc_handler import extract_text_from_docx, create_final_docx
from ai_processor import detect_languages_in_text, finalize_manuscript

# --- App Initialization ---
app = FastAPI(title="AI Editor & Publisher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-document/", response_model=AnalysisResponse)
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    Step 1: Analyzes the uploaded document to extract raw text and detect languages.
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Please upload a .docx file.")

    try:
        file_content_stream = io.BytesIO(await file.read())
        raw_text = extract_text_from_docx(file_content_stream)
        detected_languages = await detect_languages_in_text(raw_text)

        return AnalysisResponse(raw_text=raw_text, detected_languages=detected_languages)

    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"An unexpected error occurred during analysis: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.post("/finalize-document/")
async def finalize_document_endpoint(request: FinalizeRequest):
    """
    Step 2: Takes the raw text and detailed formatting options, performs the final
    AI edit and analysis, and returns the result for frontend preview.
    """
    try:
        processed_data = await finalize_manuscript(
            raw_text=request.raw_text,
            tone=request.tone,
            options=request.formatting_options,
            generate_glossary=request.generate_glossary
        )
        return JSONResponse(content=processed_data)
    except Exception as e:
        print(f"An unexpected error occurred during finalization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download-document/")
async def download_document_endpoint(request: FinalDocumentData):
    """
    Step 3: Takes the final, user-approved text and glossary data,
    and generates the final formatted .docx file for download.
    """
    try:
        output_stream = create_final_docx(request)
        
        return StreamingResponse(
            output_stream,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition': 'attachment; filename="Formatted_Manuscript.docx"'}
        )
    except Exception as e:
        print(f"Error creating final docx: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate the final document.")

