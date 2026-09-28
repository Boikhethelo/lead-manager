"""
CLI Controller module for the Lead Manager tool.
Handles parsing user inputs and routing them to the correct command handlers.
"""

import argparse
from models import commands

class CLIConfig:
    """
    Configures the main argparse command-line parser and its subcommands.
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Lead Manager")
        self.subparsers = self.parser.add_subparsers(dest="command", required=True)
        self.search_parser()
        self.delete_parser()
        self.modify_parser()
        self.add_lead_parser()
        self.score_parser()
        self.due_parser()
        self.export_parser()

    def search_parser(self):
        """Configures the 'search' subcommand and arguments."""
        search_parser = self.subparsers.add_parser("search")
        search_parser.add_argument("name_number", help="None")
        search_parser.add_argument("key", choices=["company", "contacts", "interactions", "id"])

    def delete_parser(self):
        """Configures the 'delete' subcommand and arguments."""
        delete_parser = self.subparsers.add_parser("delete")
        delete_parser.add_argument("id", help="The id of the lead")

    def modify_parser(self):
        """Configures the 'modify' subcommand and arguments."""
        modify_parser = self.subparsers.add_parser("modify")
        modify_parser.add_argument("id", help=None)
        modify_parser.add_argument("category", help=None)
        modify_parser.add_argument("key", help=None)
        modify_parser.add_argument("change", help=None)

    def add_lead_parser(self):
        """Configures the 'new' subcommand for adding a lead."""
        add_lead_parser = self.subparsers.add_parser("new")

    def score_parser(self):
        score_parser = self.subparsers.add_parser("score")
        score_parser.add_argument("id" , help="None")

    def due_parser(self):
        due_parser = self.subparsers.add_parser("due")
        due_parser.add_argument("timeframe" , choices=["today" , "late"])

    def export_parser(self):
        export_parser = self.subparsers.add_parser("export")
        export_parser.add_argument("filename" , help="What you would like to name the file")
        export_parser.add_argument("type" , choices=["csv" , "excel"])

class SearchHandler:
    """
    Handler to execute search commands.

    Args:
        commands (commands.Commands): The core logic instance.
    """

    def __init__(self, commands: commands.Commands):
        self.commands = commands

    def handle(self, args: argparse.Namespace) -> list[dict] | None:
        """Executes the search command with the provided arguments."""
        return self.commands.search(args.name_number, args.key)


class DeleteHandler:
    """
    Handler to execute delete commands.

    Args:
        commands (commands.Commands): The core logic instance.
    """

    def __init__(self, commands: commands.Commands):
        self.commands = commands

    def handle(self, args: argparse.Namespace) -> str:
        """Executes the delete command with the provided ID."""
        return self.commands.delete(args.id)


class ModifyHandler:
    """
    Handler to execute modify commands.

    Args:
        commands (commands.Commands): The core logic instance.
    """

    def __init__(self, commands: commands.Commands):
        self.commands = commands

    def handle(self, args: argparse.Namespace) ->str:
        """Executes the modify command with the provided arguments."""
        return self.commands.modify(args.id, args.category, args.key, args.change)


class AddLeadHandler:
    """
    Handler to execute commands that add new empty leads.

    Args:
        commands (commands.Commands): The core logic instance.
    """

    def __init__(self, commands: commands.Commands) :
        self.commands = commands

    def handle(self, args) -> str:
        """Executes the new lead command."""
        return self.commands.add_new_lead()

class ScoreHandler:

    def __init__(self, commands: commands.Commands):
        self.commands = commands

    def handle(self, args) -> str:
        return self.commands.score_lead(args.id)

class DueHandler:

    def __init__(self, commands: commands.Commands):
        self.commands = commands

    def handle(self, args) -> list[dict] | None:
        return self.commands.get_due_leads(args.timeframe)

class ExportHandler:

    def __init__(self, commands: commands.Commands):
        self.commands = commands

    def handle(self, args) -> str:
        return self.commands.export(args.filename , args.type)


class Controller:
    """
    Main controller for handling user input and triggering handlers.

    Args:
        config (CLIConfig): The initialized CLI configuration.
        commands (commands.Commands): The core logic instance.
        display (callable): Function responsible for rendering output.
    """

    def __init__(self, config: CLIConfig, commands: commands.Commands, display):
        self.display = display
        self.parser = config.parser
        self.handlers = {"search": SearchHandler(commands),
                         "delete": DeleteHandler(commands),
                         "modify": ModifyHandler(commands),
                         "new": AddLeadHandler(commands),
                         "score": ScoreHandler(commands),
                         "due": DueHandler(commands)}

    def run(self, user_input: list[str]) -> None:
        """
        Parses the raw user input and routes it to the correct handler.

        Args:
            user_input (list[str]): The split string input from the terminal.
        """
        try:
            args = self.parser.parse_args(user_input)
            handler = self.handlers.get(args.command)

            if handler:
                self.display(handler.handle(args))
        except SystemExit:
            print("Invalid arguments. Type 'help' for usage. ")