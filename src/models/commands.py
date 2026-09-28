"""
commands.py

Contains the core business logic layer for the Lead Manager.
This module bridges the CLI controller and the underlying data repository.
"""

from database.repository import LeadRepository
from services.lead_scoring import LeadScoringService
from services.reminder_service import ReminderService
from services.export_services import ExportService


class Commands:
    """Executes core business operations by interacting with the data repository.

    Acts as a service layer that processes validated user commands from the CLI
    and delegates the actual data retrieval and manipulation to the repository interface.

    Attributes:
        repository (LeadRepository): The data repository instance to interact with.
    """

    def __init__(self, repository: LeadRepository , scoring_services: LeadScoringService  , reminder_services: ReminderService , export_service: ExportService):
        self.repository = repository
        self.scoring_services = scoring_services
        self.reminder_services = reminder_services
        self.export_service = export_service

    def search(self, user_input: str, key: str) -> list[dict] | None:
        """Searches the repository based on a specific key and input value.

        Args:
            user_input (str): The search term (e.g., ID number, company name, or category name).
            key (str): The type of search to perform ('id', 'company', or 'category').

        Returns:
            list[dict] | None: A list of matching lead records, or None if the search key is invalid.
        """
        # Store the cleaned key to avoid repeating the string manipulation
        clean_key = key.lower().strip()

        if clean_key == "id":
            return self.repository.get_by_id(user_input)

        elif clean_key == "company":
            return self.repository.get_by_company(user_input)

        elif clean_key == "category":
            return self.repository.get_category(user_input)

        else:
            print(f"Unknown search call: '{key}'")
            return None

    def delete(self, lead_id: str) -> str:
        """Removes a lead and all its associated data from the system.

        Args:
            lead_id (str): The unique identifier of the lead to delete.

        Returns:
            str: A confirmation message indicating the result of the deletion.
        """
        return self.repository.remove_lead(lead_id)

    def modify(self, id: str, category: str, key: str, change: str) -> str:
        """Updates a specific attribute of an existing lead.

        Args:
            id (str): The unique identifier of the lead.
            category (str): The data category to update (e.g., 'company', 'contacts').
            key (str): The specific field or column to modify.
            change (str): The new value to apply to the field.

        Returns:
            str: A status message indicating success or failure.
        """
        return self.repository.modify_lead(id, category, key, change)

    def add_new_lead(self) -> str:
        """Creates a new, empty lead across all configured data categories.

        Returns:
            str: A confirmation message containing the newly generated lead ID.
        """
        return self.repository.create_new_lead()

    def score_lead(self, lead_id: str) -> str:

        lead_data = self.repository.get_by_id(lead_id)

        result = self.scoring_services.score_lead(lead_id , lead_data[0])
        self.repository.save_score(result)

        return f"Lead Score: [{result.get("Score")}] Reasoning: {result.get("Reasoning")} And Confidence: ({result.get("Confidence"):.0%})"

    def get_due_leads(self , args: str) -> list[dict] | None:

        if args == "today":
            return self.reminder_services.get_due()

        elif args == "late":
            return self.reminder_services.get_overdue()

        else:
            return None

    def export(self, filename , args: str) -> str:
        if args == "csv":
            return self.export_service.export_to_csv(filename)
        elif args == "excel":
            return self.export_service.export_to_excel(filename)
        else:
            return ""





