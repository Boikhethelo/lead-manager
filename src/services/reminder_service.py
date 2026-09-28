from datetime import date, datetime
from database.repository import LeadRepository

class ReminderService:
    """A service that checks and tracks lead follow-up schedules.

    This service filters through lead data to identify which accounts are currently
    due for contact or have breached the acceptable communication window.

    Attributes:
        OVERDUE_THRESHOLD_DAYS (int): The maximum allowed days since last contact
            before a lead is flagged as overdue.
    """

    OVERDUE_THRESHOLD_DAYS = 3

    def __init__(self, repository: LeadRepository):
        """Initializes the ReminderService with a database repository and empty alert lists.

        Args:
            repository (LeadRepository): The repository layer used to pull and query lead details.
        """
        self.repository = repository
        self.overdue: list[dict] = []
        self.due: list[dict] = []

    def startup_check(self) -> str:
        """Executes a system check to populate and count active reminders.

        This fetches up-to-date lists of due and overdue leads, caches them internally,
        and builds a user-facing dashboard notification string.

        Returns:
            str: A formatted reminder overview summary or a 'No reminders today' message.
        """
        self.overdue = self.get_overdue_leads()
        self.due = self.get_due_leads()

        overdue_count = len(self.overdue)
        due_count = len(self.due)

        if not overdue_count and not due_count:
            return "No reminders today."

        parts = []
        if overdue_count:
            parts.append(f"{overdue_count} overdue lead(s)")
        if due_count:
            parts.append(f"{due_count} due today")

        return f"[Reminders] {' | '.join(parts)} — type 'due' to review"


    def get_due(self) -> list[dict]:
        """Retrieves the cached list of leads due for contact today.

        Note:
            This returns the data cached during the last execution of `startup_check`.

        Returns:
            list[dict]: A list of full lead records that are scheduled for today.
        """
        return self.due

    def get_overdue(self) -> list[dict]:
        """Retrieves the cached list of overdue leads.

        Note:
            This returns the data cached during the last execution of `startup_check`.

        Returns:
            list[dict]: A list of full lead records that have missed their contact window.
        """
        return self.overdue


    def load_leads(self):
        """Helper method to pull all raw leads and establish a baseline execution date.

        Returns:
            tuple: A tuple containing:
                - list[dict]: All lead records from the repository.
                - datetime.date: Today's current date.
                - list: An empty list used to accumulate results.
        """
        return self.repository.get_all("leads"), date.today(), []

    def get_overdue_leads(self) -> list[dict]:
        """Queries the repository to evaluate which leads have stale engagement timelines.

        Calculates the delta between today and the lead's 'Last Contact' date. If it matches
        or exceeds `OVERDUE_THRESHOLD_DAYS`, the comprehensive record is appended to the output.

        Returns:
            list[dict]: Full lead payload dictionaries including an injected
                "Days Overdue" key representing the delta string.
        """

        leads, today, output = self.load_leads()


        for lead in leads:
            last_contacted = lead.get("Last Contact" , "")
            if not last_contacted:
                continue

            try:
                last_contact_date = datetime.strptime(last_contacted, "%Y-%m-%d").date()
                delta = (today - last_contact_date).days

                if delta >= self.OVERDUE_THRESHOLD_DAYS:
                    lead_id = lead.get("ID")
                    full_lead = self.repository.get_by_id(lead_id)
                    full_lead[0]["leads"][0]["Days Overdue"] = f"{delta} days"
                    output.append(full_lead[0])

            except ValueError:
                continue

        return output

    def get_due_leads(self) -> list[dict]:
        """Queries the repository to determine which leads have reached their scheduled follow-up.

        Parses the 'Next Scheduled Contact' date and checks if it falls on or before today's date.

        Returns:
            list[dict]: Full lead payload dictionaries including an injected
                "Days Overdue" key set to "Due today".
        """

        leads, today, output = self.load_leads()

        for lead in leads:
            scheduled_str = lead.get("Next Scheduled Contact", "")
            if not scheduled_str:
                continue


            try:
                scheduled = datetime.strptime(scheduled_str, "%Y-%m-%d").date()
                if scheduled <= today:
                    lead_id = lead.get("ID")
                    full_lead = self.repository.get_by_id(lead_id)
                    full_lead[0]["leads"][0]["Days Overdue"] = "Due today"
                    output.append(full_lead[0])

            except ValueError:
                continue

        return output
