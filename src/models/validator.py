"""
validator.py

Provides input validation and parsing logic for the CLI. Ensures user input
meets the structural requirements before passing it to the controller.
"""
import shlex


class Validator:
    """Validates and formats raw terminal input for the CLI controller.

    Checks commands against known valid operations and ensures required
    arguments are present and correctly structured, particularly handling
    multi-word inputs for search terms and modification values.

    Attributes:
        VALID_COMMANDS (set[str]): A set of allowed primary commands.
        VALID_KEYS (set[str]): A set of allowed search categories/keys.
    """

    def __init__(self):
        self.VALID_COMMANDS = {"search", "delete", "modify", "new", "score", "due", "export",
                               "exit", "quit", "help"}
        self.VALID_KEYS = {"company", "contacts", "interactions", "id"}

    def validate_command(self, raw_input: str) -> list[str] | None:
            try:
                # Fix: Use shlex.split to keep quoted strings intact
                parts = shlex.split(raw_input.strip())
            except ValueError as exc:
                print(f"Input error: {exc}")
                return None

            if not parts:
                return None

            command = parts[0].lower()

            if command not in self.VALID_COMMANDS:
                print(f"Unknown command: '{command}'. Enter 'help' for valid commands.")
                return None

            if command == "search":
                return self.parse_search(parts)
            elif command == "modify":
                return self.parse_modify(parts)
            else:
                return parts

    def parse_search(self, parts: list[str]) -> list[str] | None:
        """Validates the syntax and structure of a 'search' command.

        Args:
            parts (list[str]): The split input string starting with 'search'.

        Returns:
            list[str] | None: A formatted list containing ['search', 'search_term', 'key'],
                              or None if the structure is invalid.
        """
        # Need a <command> <term> <key> structure (minimum 3 parts)
        if len(parts) < 3:
            print(f"'{parts[0]}' requires a search term and a category.")
            print("  Example: search Acme Corp company")
            return None

        # Ensure the key is lowercase to match the VALID_KEYS set
        key = parts[-1].lower()

        if key not in self.VALID_KEYS:
            print(f"Unknown category: '{key}'. Valid: {', '.join(sorted(self.VALID_KEYS))}")
            return None

        # Re-join middle tokens to preserve spaces in multi-word search names
        search_term = " ".join(parts[1:-1])

        return ["search", search_term, key]

    def parse_modify(self, parts: list[str]) -> list[str] | None:
        if len(parts) < 5:
            print("'modify' requires: modify <id> <category> <field> <value>")
            print("  Example: modify 1 leads Status Closed Won")
            # Fix: Add a hint for users regarding quotes
            print('  Note: Use quotes for multi-word fields, e.g., "Next Scheduled Contact"')
            return None

        lead_id = parts[1]
        category = parts[2]
        field = parts[3]

        # Re-join remaining tokens to support multi-word values (e.g., "Closed Won")
        change = " ".join(parts[4:])

        return ["modify", lead_id, category, field, change]