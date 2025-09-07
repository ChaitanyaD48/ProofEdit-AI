import os
import google.generativeai as genai
from models import ProofreadRequest, InteractiveEditRequest

# --- Gemini API Configuration ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash') # Using a powerful model
except KeyError:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set. Please set it before running the application.")
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API: {e}")


def generate_master_prompt(raw_text: str, params: ProofreadRequest) -> str:
    """
    Constructs the main, detailed prompt for the AI based on user inputs.
    """
    return f"""
    You are an expert multilingual book editor and proofreader with mastery in English, Hindi, and Sanskrit.
    Your task is to meticulously edit and format a raw, voice-typed manuscript draft. Adhere STRICTLY to the following instructions.

    **Primary Goal:** Preserve the author's original voice and intent while elevating the text to a professional, publication-ready standard.

    ---
    **CONTEXTUAL & STYLISTIC PARAMETERS:**

    1.  **Author's Persona:** {params.author_persona}
    2.  **Book's Core Message:** {params.book_summary}
    3.  **Language-Specific Rules:** {params.language_rules}

    ---
    **CORE EDITORIAL TASKS:**

    1.  **Proofread for Errors:**
        - Correct all spelling, grammar, and syntax errors.
        - Pay extreme attention to common voice-to-text mistakes like homophones (e.g., "their/there/they're", "right/write/rite"). Use context to determine the correct word.
        - Fix incorrect capitalization. Capitalize the start of sentences and all proper nouns.

    2.  **Punctuation and Structure:**
        - Insert correct punctuation (periods, commas, question marks, etc.).
        - Break down long, run-on sentences into clear, concise ones.
        - Structure the text into logical paragraphs. Add paragraph breaks where a new idea or topic is introduced. The output should be a clean flow of paragraphs.

    3.  **Consistency Check:**
        - Scan the entire text for inconsistencies in names, places, and key terms. If you find a variation (e.g., "Suresh" and "Suraesh"), standardize it to the first usage.

    ---
    **OUTPUT FORMATTING:**

    -   Your final output MUST be plain text only.
    -   Do NOT include any markdown (like ##, **, _, etc.), HTML tags, or any other special formatting.
    -   The output should be the complete, edited manuscript, ready to be placed directly into a document.

    ---
    **MANUSCRIPT TO PROCESS:**

    {raw_text}
    """


def process_text_with_gemini(raw_text: str, params: ProofreadRequest) -> str:
    """
    Sends the text and parameters to the Gemini API for proofreading.
    """
    master_prompt = generate_master_prompt(raw_text, params)
    try:
        response = model.generate_content(master_prompt)
        return response.text
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        # In a real app, you might want a more sophisticated retry mechanism
        raise RuntimeError("Failed to get a response from the AI model.")


def perform_interactive_edit(request: InteractiveEditRequest) -> str:
    """
    Performs a specific, targeted edit on a snippet of text.
    """
    prompt = f"""
    You are an expert editor. A user has provided a snippet of text and a command.
    Execute the command precisely. Return ONLY the modified text snippet.

    **Command:** "{request.command}"

    **Text to modify:** "{request.text_snippet}"
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error during interactive edit API call: {e}")
        raise RuntimeError("Failed to get a response from the AI model for interactive edit.")


async def generate_glossary_and_consistency_report(full_text: str) -> dict:
    """
    Uses AI to generate a glossary of key terms and a consistency report.
    This is a separate, more advanced function.
    """
    prompt = f"""
    You are a linguistic analyst. Analyze the following manuscript to produce two things: a glossary and a consistency report.
    Return the output as a single JSON object with two keys: "glossary" and "consistency_report".

    1.  **Glossary:** Identify key terms (especially non-English words, philosophical concepts, or recurring proper nouns). For each term, provide a brief, context-based definition. The glossary should be an array of objects, each with "term" and "definition" keys.
    2.  **Consistency Report:** Identify potential inconsistencies in names, dates, or facts. The report should be an array of strings, where each string describes a potential issue.

    **Manuscript:**
    ---
    {full_text}
    ---
    """
    try:
        response = model.generate_content(prompt)
        # Basic cleanup to extract JSON from the response
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        import json
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error generating glossary/report: {e}")
        return {"glossary": [], "consistency_report": ["Failed to generate report."]}
