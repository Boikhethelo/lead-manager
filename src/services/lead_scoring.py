import json
import os

import google.generativeai as genai
from datetime import date
from dotenv import load_dotenv

class LeadScoringError(Exception):
    """Raised when lead scoring fails due to API errors or response parsing issues."""
    pass


class LeadScoringService:
    """A service that leverages Google's Gemini LLM to analyze and score B2B sales leads.

    This service evaluates lead profiles against standardized sales criteria (Hot, Warm, Cold)
    and extracts structured insights including the assigned score, brief reasoning, and
    confidence metrics.

    Attributes:
        CRITERIA (str): The baseline guidelines used by the LLM to classify lead quality.
        _REQUIRED_KEYS (set): The structural JSON fields expected from the model's response.
    """

    CRITERIA = """
    Hot:  decision-maker contact present, potential value > 50000,
          interaction notes suggest positive engagement, contacted within 7 days.
    Warm: has a contact but no recent interaction, or value is moderate.
    Cold: no decision-maker, no recent contact, or disengaged notes.
    """

    _REQUIRED_KEYS = {"score", "reasoning", "confidence"}

    def __init__(self, api_key: str | None):
        """Initializes the service with the given Gemini API key and configures the LLM.

        Args:
            api_key (str | None): The Gemini API key used to authenticate requests.

        Raises:
            ValueError: If the `api_key` is falsy or missing.
        """

        if not api_key:
            raise ValueError(
                "A valid Gemini API key is required. "
                "Set GEMINI_API_KEY in your .env file."
            )


        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    @classmethod
    def from_env(cls) -> "LeadScoringService":
        """Factory method to initialize the service using environment variables.

        Loads environment variables from a local `.env` file and retrieves the
        Gemini API key.

        Returns:
            LeadScoringService: A configured instance of the scoring service.

        Raises:
            ValueError: If the `GEMINI_API_KEY` cannot be found in the environment.
        """

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Add it to your .env file:\n  GEMINI_API_KEY=your_key_here"
            )

        return cls(api_key)

    def _build_prompt(self, lead_data: dict) -> str:
        """Constructs the system prompt instructing the LLM how to score the lead data.

        Args:
            lead_data (dict): The dictionary containing comprehensive profile info for a lead.

        Returns:
            str: The fully structured prompt string containing evaluation instructions,
                criteria, source data, and formatting rules.
        """

        prompt = f"""
        You are a B2B sales analyst. Score this lead as Cold, Warm, or Hot. Scoring criteria: {self.CRITERIA} 
        Lead profile: {json.dumps(lead_data, indent=2)} Respond ONLY with valid JSON, 
        no markdown: {{"score": "Hot|Warm|Cold", "reasoning": "one sentence", "confidence": 0.85}}
                """

        return prompt

    def _parse_response(self, raw_text: str) -> dict:
        """Cleans and validates the raw text returned by the Gemini API.

        Removes any accidental markdown code block wrappers, parses the text
        as JSON, and ensures all required dictionary keys are present.

        Args:
            raw_text (str): The raw string output received from the LLM.

        Returns:
            dict: The validated, parsed dictionary containing the structured scoring elements.

        Raises:
            LeadScoringError: If the response is not valid JSON or if required
                schema keys are missing.
        """

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
        """Scores a specific lead profile by querying the Gemini LLM.

        This orchestrates prompt building, network execution, response parsing,
        and output validation, returning a unified dictionary containing the
        final score metadata.

        Args:
            lead_id (str): The unique identifier for the lead being evaluated.
            lead_data (dict): The target metadata profile of the lead to analyze.

        Returns:
            dict: A formatted dictionary tracking the lead's ID, assigned Score,
                Reasoning text, clamped Confidence float, and the evaluation Date.

        Raises:
            LeadScoringError: If the Gemini API call fails or if the response
                validation fails.
        """
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