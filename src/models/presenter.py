"""
presenter.py

Handles the presentation and formatting of data for the terminal user interface.
This acts as the view layer, ensuring data is displayed cleanly to the user.
"""


class Presenter:
    """Formats and prints application output to the terminal.

    Attributes:
        help (str): A predefined multiline string containing the CLI usage instructions.
    """

    def __init__(self):
        self.help = """
            Commands:
                search <value> id                          - Find all records by ID
                search <value> contacts|company            - Search by field value
                new                                        - Create a blank lead
                modify <id> <category> <field> <value>     - Update a field
                delete <id>                                - Remove a lead by ID
                score  <id>                                - Scores a lead by ID
                due    <frame>                             - Get leads due for contact
                help                                       - Show this message
                exit / quit                                - Close the app
                   """

    def start_up(self, banner):
        print("Welcome to Lead Manager. \nThis is a fast CRM designed to manage high quality B2B leads.\n")
        print(banner)
        print("\n\n")


    def print_help(self) -> None:
        """Prints the available commands and usage instructions to the console."""
        print(self.help)

    def display(self, results: list[dict] | str | None) -> None:
        """Parses and cleanly formats the output from a command for terminal display.

        Handles various input types: gracefully exits on empty data, prints raw
        status strings directly, and heavily formats nested dictionary structures
        for readable lead data.

        Args:
            results (list[dict] | str | None): The data to display. Can be a string
                (status message), a list of dictionaries (lead data), or None.
        """
        # 1. Handle empty states or None returns from unknown commands
        if not results:
            print("No results found.")
            return

        # 2. Handle simple string messages (e.g., confirmations from add/delete/modify)
        if isinstance(results, str):
            print(results)
            return

        # 3. Handle complex lead data structures
        print("\n-RESULT-")

        for result in results:
            # Result is expected to be a dictionary mapping a category to its rows
            for category, rows in result.items():
                if rows:
                    print(f"\n── {category.upper()} ──")

                    # Iterate through each record in the category
                    for row in rows:
                        # Print each key-value pair, defaulting to '—' if the value is empty
                        for k, v in row.items():
                            print(f"  {k}: {v or '—'}")












