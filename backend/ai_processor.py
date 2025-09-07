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
    """Uses the AI to detect the primary languages present in a text."""
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
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        detected_languages = json.loads(json_text)
        return detected_languages
    except Exception as e:
        print(f"Error during language detection: {e}")
        return ["English"]


def generate_final_editor_prompt(raw_text: str, tone: str, options: FormattingOptions) -> str:
    """
    Generates the master prompt for the final editorial pass with strict rules
    to preserve the original content.
    """
    sanskrit_rules = ""
    if options.sanskrit_shlokas:
        opts = options.sanskrit_shlokas
        sanskrit_rules += "\n    **Sanskrit Shloka Formatting Rules:**\n"
        sanskrit_rules += "    - Preserve the original Devanagari script perfectly.\n"
        sanskrit_rules += "    - Maintain correct Sandhi and Samas (do not break joined words inappropriately).\n"
        if opts.line_breaks:
            sanskrit_rules += "    - Inside the [SHLOKA]...[/SHLOKA] tags, insert a newline character '\\n' to separate each half-verse (pāda).\n"
        if opts.add_numbering:
            sanskrit_rules += "    - If you can identify the source (e.g., Bhagavad Gita), add a citation marker like [CITE: Bhagavad Gita 2.47] immediately after the shloka.\n"
        if opts.translation_style != "No translation":
             sanskrit_rules += f"    - After the shloka, add the English translation. The style should be: '{opts.translation_style}'. Prefix the translation with the label 'Translation: '. Embed this entire block (label and text) inside a [TRANSLATION]...[/TRANSLATION] tag.\n"
    
    return f"""
    You are a technical typesetter and proofreader with deep expertise in English, Hindi, and Sanskrit.

    **PRIMARY RULE: DO NOT CHANGE THE AUTHOR'S ORIGINAL WORDS OR SENTENCE STRUCTURE.**
    - Your only job is to fix surface-level errors and apply the formatting markers specified below.
    - **DO NOT** rewrite, rephrase, or restructure any sentences.
    - **DO NOT** add any content, ideas, or explanations. The original text must be preserved exactly as written by the author.
    - The tone '{tone}' is for context only; do not change words to match it.

    **PROOFREADER'S CHECKLIST (Surface-level fixes ONLY):**
    1.  **Correct Errors:** Fix obvious spelling mistakes, grammatical errors (like subject-verb agreement), punctuation, and typos.
    2.  **Transliterate Correctly:** Convert any Hindi/Sanskrit words typed in English (e.g., "anushasan") to Devanagari script (e.g., अनुशासन). This is a correction, not a content change.
    3.  **Capitalization:** Ensure proper capitalization at the start of sentences and for proper nouns.

    **SPECIFIC FORMATTING RULES:**
    {sanskrit_rules if sanskrit_rules else "    - No special language formatting requested."}

    **OUTPUT MARKER INSTRUCTIONS (MANDATORY):**
    You MUST use the following markers to structure your output. Do not use any markdown.
    - `[H1]Your Heading[/H1]` for main headings.
    - `[H2]Your Subheading[/H2]` for subheadings.
    - `[SHLOKA]...[/SHLOKA]` to enclose a Sanskrit shloka.
    - `[TRANSLATION]...[/TRANSLATION]` to enclose the English translation of a shloka.

    **MANUSCRIPT TO PROCESS:**
    ---
    {raw_text}
    ---

    Return only the corrected and formatted manuscript text, adhering strictly to all rules.
    """

def generate_glossary_prompt(edited_text: str) -> str:
    """Generates a prompt to extract a glossary."""
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
    """Orchestrates the two-stage AI processing pipeline for the final edit."""
    editor_prompt = generate_final_editor_prompt(raw_text, tone, options)
    try:
        edited_response = await model.generate_content_async(editor_prompt)
        edited_manuscript = edited_response.text
    except Exception as e:
        print(f"Error during Stage 1 (Editor Pass): {e}")
        raise RuntimeError("AI failed during the main editing phase.")

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

