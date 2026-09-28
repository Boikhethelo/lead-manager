"""
main.py

The main entry point for the Lead Manager application.
Assembles all components (repository, controller, validator, presenter)
and runs the interactive command-line interface loop.
"""

from database.csv_repository import CsvLeadRepository, LeadFileHandler, LeadConfig
from models.cli_commands import Controller, CLIConfig
from models.commands import Commands
from models.validator import Validator
from models.presenter import Presenter
from services.lead_scoring import LeadScoringService , LeadScoringError
from services.reminder_service import ReminderService
from services.export_services import ExportService

from pathlib import Path



class App:
    """Initializes and runs the Lead Manager application.

    This class acts as the central composition root, wiring together the
    data access layer, business logic, validation, and presentation layers
    before starting the main terminal application loop.
    """

    def __init__(self):
        # 1. Initialize the Data Access Layer (Repository)
        handler = LeadFileHandler()
        config = LeadConfig()
        repository = CsvLeadRepository(handler, config)

        # 2. Initialize the Presentation and Validation Layers
        self.validator = Validator()
        self.presenter = Presenter()

        display = self.presenter.display

        # 3. Load the scoring service — key comes from GEMINI_API_KEY in .env
        #    Raises ValueError at startup if the key is missing, so you find out
        #    immediately rather than when a user runs 'score'.

        try:
            scoring_services = LeadScoringService.from_env()
        except ValueError as exc:
            print(f"[Warning] Lead scoring unavailable: {exc}")
            scoring_services = None

        #4. Load the reminder services and runs a check for due and overdue leads
        reminder_services = ReminderService(repository)
        banner = reminder_services.startup_check()

        #5. Load the export services

        export_service = ExportService(repository, Path("exports"))

        # 6. Wire everything together
        app_commands = Commands(repository, scoring_services , reminder_services, export_service)
        self.controller = Controller(CLIConfig(), app_commands , display)

        self.presenter.start_up(banner)

    def main(self) -> None:
        """Starts the main interactive application loop.

        Continuously prompts the user for terminal input, handles top-level
        commands like 'help' and 'exit', and routes all valid operational
        commands through the application controller.
        """

        run = True

        while run:
            user_input = input("\nEnter command: ")

            # Handle top-level app commands directly
            if user_input.strip() == "help":
                self.presenter.print_help()
            elif user_input.strip() in ("exit", "quit"):
                run = False
            else:
                # Pass operational commands to the validator and controller
                command = self.validator.validate_command(user_input)
                if command is not None:
                    self.controller.run(command)


if __name__ == "__main__":
    app = App()
    app.main()