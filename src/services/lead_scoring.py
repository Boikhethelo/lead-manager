
import json
import os

import google.generativeai as genai
from datetime import date
from dotenv import load_dotenv

class LeadScoringError(Exception):
    """Raised when scoring fails due to API or parsing issues."""
    pass


class LeadScoringService:

    CRITERIA = """
    Hot:  decision-maker contact present, potential value > 50000,
          interaction notes suggest positive engagement, contacted within 7 days.
    Warm: has a contact but no recent interaction, or value is moderate.
    Cold: no decision-maker, no recent contact, or disengaged notes.
    """

    _REQUIRED_KEYS = {"score", "reasoning", "confidence"}

    def __init__(self, api_key: str | None):

        if not api_key:
            raise ValueError(
                "A valid Gemini API key is required. "
                "Set GEMINI_API_KEY in your .env file."
            )


        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    @classmethod
    def from_env(cls) -> "LeadScoringService":

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Add it to your .env file:\n  GEMINI_API_KEY=your_key_here"
            )

        return cls(api_key)

    def _build_prompt(self, lead_data: dict) -> str:

        prompt = f"""
        You are a B2B sales analyst. Score this lead as Cold, Warm, or Hot. Scoring criteria: {self.CRITERIA} 
        Lead profile: {json.dumps(lead_data, indent=2)} Respond ONLY with valid JSON, 
        no markdown: {{"score": "Hot|Warm|Cold", "reasoning": "one sentence", "confidence": 0.85}}
                """

        return prompt

    def _parse_response(self, raw_text: str) -> dict:

        cleaned = (
            raw_text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LeadScoringError(
                f"Gemini returned non-JSON response: {raw_text!r}"
            ) from exc

        missing = self._REQUIRED_KEYS - parsed.keys()
        if missing:
            raise LeadScoringError(
                f"Gemini response missing required keys: {missing}. Got: {parsed}"
            )

        return parsed

    def score_lead(self,  lead_id: str , lead_data: dict) -> dict:
        score_date = date.today()
        date_string = score_date.strftime("%Y-%m-%d")


        prompt = self._build_prompt(lead_data)

        try:
            response = self.model.generate_content(prompt)

        except Exception as exc:
            raise LeadScoringError(
                f"Gemini API call failed for lead {lead_id}: {exc}"
            ) from exc

        parsed = self._parse_response(response.text)
        confidence = max(0.0, min(1.0, float(parsed["confidence"])))
        result = {"ID" : lead_id , "Score" : parsed["score"] , "Reasoning" : parsed["reasoning"] , "Confidence" : confidence , "Date Scored" : date_string}
        return result

