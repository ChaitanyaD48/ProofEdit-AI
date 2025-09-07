import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any

from models import FormattingOptions

load_dotenv()

# --- Gemini API Configuration ---
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API: {e}")


async def detect_languages_in_text(raw_text: str) -> list[str]:
    """
    Uses the AI to detect the primary languages present in a text.
    """
    # Use a small portion of text for efficiency
    sample_text = (raw_text[:2000] + '...') if len(raw_text) > 2000 else raw_text
    
    prompt = f"""
    Analyze the following text and identify all significant languages present.
    Your response must be a valid JSON array of strings.
    For example: ["English", "Hindi", "Sanskrit"]

    Text to analyze:
    ---
    {sample_text}
    ---

    JSON Array:
    """
    try:
        response = await model.generate_content_async(prompt)
        # Clean up and parse the JSON response
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        detected_languages = json.loads(json_text)
        return detected_languages
    except Exception as e:
        print(f"Error during language detection: {e}")
        # Default fallback
        return ["English"]


def generate_final_editor_prompt(raw_text: str, tone: str, options: FormattingOptions) -> str:
    """
    Generates the master prompt for the final, detailed editorial pass.
    This prompt is now dynamically constructed based on user formatting choices.
    """
    
    # --- Dynamically build language-specific instructions ---
    sanskrit_rules = ""
    if options.sanskrit_shlokas:
        opts = options.sanskrit_shlokas
        sanskrit_rules += "\n    **Sanskrit Shloka Formatting Rules:**\n"
        sanskrit_rules += "    - Preserve the original Devanagari script perfectly. Do not translate unless it's part of the original text.\n"
        sanskrit_rules += "    - Maintain correct Sandhi and Samas (do not break joined words inappropriately).\n"
        if opts.line_breaks:
            sanskrit_rules += "    - Inside the [SHLOKA]...[/SHLOKA] tags, insert a newline character '\\n' to separate each half-verse (pāda).\n"
        if opts.add_numbering:
            sanskrit_rules += "    - If you can identify the source (e.g., Bhagavad Gita), add a citation marker like [CITE: Bhagavad Gita 2.47] immediately after the shloka.\n"
        sanskrit_rules += f"    - After the shloka, add the English translation. The style should be: '{opts.translation_style}'. Embed this translation inside a [TRANSLATION]...[/TRANSLATION] tag.\n"
    
    return f"""
    You are a world-class book editor and typographer with deep expertise in English, Hindi, and Sanskrit.
    Your task is to transform a raw manuscript into a polished, publication-ready draft, following user-specified formatting rules precisely.

    **CONTEXT:**
    - **Desired Tone:** {tone}. You must rewrite and adjust sentences to match this tone consistently.
    
    **SPECIFIC FORMATTING RULES:**
    {sanskrit_rules if sanskrit_rules else "    - No special language formatting requested."}

    **GENERAL PROOFREADER'S & EDITOR'S CHECKLIST:**
    1.  **Correct All Errors:** Fix spelling, grammar, punctuation, and typos.
    2.  **Restructure Sentences:** Rephrase awkward sentences for clarity and flow, adhering to the '{tone}' tone.
    3.  **Transliterate Correctly:** Convert any Hindi/Sanskrit words typed in English (e.g., "anushasan") to Devanagari script (e.g., अनुशासन).

    **OUTPUT MARKER INSTRUCTIONS (MANDATORY):**
    You MUST use the following markers to structure your output.
    - `[H1]Your Heading[/H1]` for main headings.
    - `[H2]Your Subheading[/H2]` for subheadings.
    - `[ITALIC]Your Text[/ITALIC]` for emphasis.
    - `[SHLOKA]...[/SHLOKA]` to enclose a Sanskrit shloka.
    - `[TRANSLATION]...[/TRANSLATION]` to enclose the English translation of a shloka.

    **MANUSCRIPT TO EDIT:**
    ---
    {raw_text}
    ---

    Return only the fully edited and formatted manuscript text, adhering to all rules.
    """

def generate_glossary_prompt(edited_text: str) -> str:
    """Generates a prompt to extract a glossary. (This function remains the same)"""
    # ... (code from previous version is unchanged) ...
    return f"""
    You are a linguistic analyst. Analyze the following manuscript to produce a glossary of all non-English terms.
    Your output MUST be a valid JSON array of objects. Each object must have four keys: "term", "transliteration", "translation", and "context".

    **Instructions:**
    1.  Identify every significant Hindi and Sanskrit term in the text (e.g., अनुशासन, धर्म, श्लोक).
    2.  For each term, provide the following:
        - `term`: The word in its original Devanagari script.
        - `transliteration`: The Roman script (English) transliteration.
        - `translation`: The concise English meaning.
        - `context`: If the term is part of a cited source (marked with [CITE: ...]), provide that citation. Otherwise, provide a brief note on its usage in the text or leave it as null.
    3.  Ensure the final output is ONLY the JSON array, with no other text before or after it.

    **EDITED MANUSCRIPT:**
    ---
    {edited_text}
    ---

    JSON Output:
    """

async def finalize_manuscript(raw_text: str, tone: str, options: FormattingOptions, generate_glossary: bool) -> Dict[str, Any]:
    """
    Orchestrates the two-stage AI processing pipeline for the final edit.
    """
    # STAGE 1: The Editor Pass with detailed formatting
    editor_prompt = generate_final_editor_prompt(raw_text, tone, options)
    try:
        edited_response = await model.generate_content_async(editor_prompt)
        edited_manuscript = edited_response.text
    except Exception as e:
        print(f"Error during Stage 1 (Editor Pass): {e}")
        raise RuntimeError("AI failed during the main editing phase.")

    # STAGE 2: The Analyst Pass (Glossary & Citations)
    # ... (code from previous version is unchanged) ...
    glossary_data = []
    if generate_glossary:
        glossary_prompt = generate_glossary_prompt(edited_manuscript)
        try:
            glossary_response = await model.generate_content_async(glossary_prompt)
            json_text = glossary_response.text.strip().replace("```json", "").replace("```", "")
            glossary_data = json.loads(json_text)
        except Exception as e:
            print(f"Error during Stage 2 (Glossary Pass): {e}")
            glossary_data = [{"term": "Error", "transliteration": "Processing Failed", "translation": f"Could not generate glossary: {e}", "context": ""}]

    return {
        "edited_manuscript": edited_manuscript,
        "glossary": glossary_data
    }

