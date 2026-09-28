from datetime import date, datetime
from database.repository import LeadRepository

class ReminderService:

    OVERDUE_THRESHOLD_DAYS = 3

    def __init__(self, repository:LeadRepository):
        self.repository = repository
        self.overdue: list[dict] = []
        self.due: list[dict] = []

    def startup_check(self) -> str:
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
        return self.due

    def get_overdue(self) -> list[dict]:
        return self.overdue


    def load_leads(self):
        return self.repository.get_all("leads"), date.today(), []

    def get_overdue_leads(self) -> list[dict]:

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





