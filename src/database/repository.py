from abc import ABC, abstractmethod
import secrets

class LeadRepository(ABC):
    """Abstract base class defining the standard interface for lead repositories.

    This interface dictates the required methods that any concrete repository implementation
    (such as a CSV or SQL database handler) must provide to manage lead data.
    """

    def generate_id(self) -> str:
        """Generates a secure, unique four-character alphanumeric identifier.

        Returns:
            str: A randomized 4-character hex string in uppercase (e.g., 'A1B2').
        """
        return secrets.token_hex(2).upper()

    @abstractmethod
    def get_all(self, category: str) -> list[dict]:
        """Retrieves the entire database contents for a specific category in memory.

        Args:
            category (str): The data category to retrieve.

        Returns:
            list[dict]: A list of all records within the specified category.
        """
        ...

    @abstractmethod
    def get_by_id(self, lead_id: str) -> list[dict]:
        """Fetches all data across categories associated with a specific lead ID.

        Args:
            lead_id (str): The unique identifier for the lead.

        Returns:
            list[dict]: A list containing the aggregated data linked to the ID.
        """
        ...

    @abstractmethod
    def get_category(self, key: str) -> list[dict]:
        """Retrieves an entire category based on its configuration key.

        Args:
            key (str): The configuration key representing the category.

        Returns:
            list[dict]: A list of dictionaries representing the category's records.
        """
        ...

    @abstractmethod
    def get_by_company(self, name: str) -> list[dict]:
        """Performs a partial text search on company names to find matching leads.

        Args:
            name (str): The full or partial name of the company to search for.

        Returns:
            list[dict]: A list of full lead profiles that match the search criteria.
        """
        ...

    @abstractmethod
    def add(self, category: str, record: dict) -> None:
        """Adds a new lead record to the database in memory.

        Args:
            category (str): The category to append the new record to.
            record (dict): The dictionary containing the record data.
        """
        ...

    @abstractmethod
    def save(self, category: str) -> None:
        """Persists the in-memory data for a specific category to permanent storage.

        Args:
            category (str): The category to save.
        """
        ...

    @abstractmethod
    def remove_lead(self, lead_id: str) -> str:
        """Deletes a lead and all associated records from the database.

        Args:
            lead_id (str): The unique identifier of the lead to remove.
        """
        ...

    @abstractmethod
    def modify_lead(self, lead_id: str, category: str, key: str, change: str) -> str:
        """Updates a specific field for an existing lead.

        Args:
            lead_id (str): The unique identifier of the lead.
            category (str): The category where the change should occur.
            key (str): The specific field or column to update.
            change (str): The new value to apply.

        Returns:
            str: A status message indicating the result of the update operation.
        """
        ...

    @abstractmethod
    def create_new_lead(self) -> str:
        """Scaffolds and initializes a new empty lead across all data categories.

        Returns:
            str: A confirmation message containing the newly generated lead ID.
        """
        ...

    @abstractmethod
    def save_score(self, result: dict) -> None: ...





    