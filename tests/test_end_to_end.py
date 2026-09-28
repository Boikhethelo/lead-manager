import unittest
import tempfile
import shutil
from pathlib import Path

from database.csv_repository import LeadFileHandler, LeadConfig, CsvLeadRepository
from models.commands import Commands
from services.reminder_service import ReminderService
from services.export_services import ExportService


class TestLeadManagerE2E(unittest.TestCase):
    """End-to-End tests for the Lead Manager application core logic."""

    def setUp(self):
        """Set up a temporary directory and fresh database instance for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

        # Initialize mock repository in the temp folder
        self.handler = LeadFileHandler(directory=self.test_path)
        self.config = LeadConfig()  # Assumes config.ini is in the default location
        self.repository = CsvLeadRepository(self.handler, self.config)

        # Initialize services (omitting AI scoring to avoid API calls during testing)
        self.reminder_service = ReminderService(self.repository)
        self.export_service = ExportService(self.repository, self.test_path / "exports")

        self.commands = Commands(
            repository=self.repository,
            scoring_services=None,
            reminder_services=self.reminder_service,
            export_service=self.export_service
        )

    def tearDown(self):
        """Clean up the temporary directory after tests run."""
        shutil.rmtree(self.test_dir)

    def test_full_lead_lifecycle(self):
        """Tests creating, modifying, searching, and deleting a lead."""

        # 1. Create a new lead
        creation_msg = self.commands.add_new_lead()
        self.assertIn("New lead created with id of", creation_msg)

        # Extract the ID from the success message
        lead_id = creation_msg.split(": ")[1].strip()

        # 2. Modify the lead
        mod_msg_status = self.commands.modify(lead_id, "leads", "Status", "Warm")
        mod_msg_company = self.commands.modify(lead_id, "company", "Name", "TechCorp")

        self.assertIn("updated to Warm", mod_msg_status)
        self.assertIn("updated to TechCorp", mod_msg_company)

        # 3. Search for the lead by ID
        search_results = self.commands.search(lead_id, "id")
        self.assertIsNotNone(search_results)
        self.assertEqual(len(search_results), 1)

        # Verify modifications persisted
        lead_data = search_results[0]
        self.assertEqual(lead_data["leads"][0]["Status"], "Warm")
        self.assertEqual(lead_data["company"][0]["Name"], "TechCorp")

        # 4. Search by Company Name
        company_search = self.commands.search("TechCorp", "company")
        self.assertEqual(len(company_search), 1)
        self.assertEqual(company_search[0]["company"][0]["Name"], "TechCorp")

        # 5. Delete the lead
        delete_msg = self.commands.delete(lead_id)
        self.assertIn("has been removed", delete_msg)

        # Verify deletion
        empty_search = self.commands.search(lead_id, "id")
        # The get_by_id logic returns an aggregate dict; if empty, the nested lists will be empty
        self.assertEqual(len(empty_search[0]["leads"]), 0)


if __name__ == "__main__":
    unittest.main()