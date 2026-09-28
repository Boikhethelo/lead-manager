"""
csv_repository.py

CSV-backed storage for the Lead Manager: configuration parsing, low-level
file handling, and the in-memory repository that sits on top of both.
"""
import os
import csv
import configparser
import ast
from csv import DictReader
from pathlib import Path
from database.repository import LeadRepository

BASE_DIR = Path(__file__).resolve().parent


class LeadConfig:
    """Reads config.ini and builds the CSV file definitions.

    Attributes:
        path (Path): Location of the configuration file.
    """

    def __init__(self, config_path: Path = BASE_DIR.parent / "config.ini"):
        self.path = Path(config_path)

    def get_definitions(self) -> list[dict]:
        """Returns one {'filename', 'header', 'key'} dict per configured CSV file."""
        if not self.path.exists():
            raise FileNotFoundError(f"Config file not found: {self.path}")

        config = configparser.ConfigParser()
        config.read(self.path)

        definitions = []
        for file in config["Files"]:
            name = config["Files"][file]
            key = name.removesuffix(".csv")
            header = ast.literal_eval(config["Fields"].get(key, "[]"))
            definitions.append({"filename": name, "header": header, "key": key})

        return definitions


class LeadFileHandler:
    """Low-level CSV reading and writing.

    Writes go to a temporary file first and are then swapped in with
    os.replace, so a crash mid-write can't leave a half-written CSV behind.

    Attributes:
        directory (Path): Directory holding the CSV files.
    """

    def __init__(self, directory: Path = BASE_DIR.parent / "files"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def read_file(self, filename: str) -> list[dict]:
        """Reads a CSV file into a list of row dicts."""
        with open(self.directory / filename, "r", newline="", encoding="utf-8-sig") as file:
            return list(DictReader(file))

    def write_file(self, filename: str, header: list[str]) -> None:
        """Creates a new CSV file containing only the header row."""
        self.save_files(filename, [], header)

    def save_files(self, filename: str, rows: list[dict], header: list[str]) -> None:
        """Atomically overwrites a CSV file with the given rows.

        Keys in a row that are not in the header are ignored rather than
        crashing the save.
        """
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / filename
        tmp_path = path.with_name(path.name + ".tmp")

        with open(tmp_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=header, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

        os.replace(tmp_path, path)


class CsvLeadRepository(LeadRepository):
    """Manages lead data loaded into memory from CSV files.

    Attributes:
        handler (LeadFileHandler): File handler for disk operations.
        config (LeadConfig): Source of the file definitions.
        data (dict): In-memory data, keyed by category.
    """

    def __init__(self, handler: LeadFileHandler, config: LeadConfig):
        self.handler = handler
        self.config = config
        self.data = {}
        self._definitions_cache = None

    # ------------------------------------------------------------------ helpers

    def _definitions(self) -> dict[str, dict]:
        """Returns the file definitions keyed by category (parsed once)."""
        if self._definitions_cache is None:
            self._definitions_cache = {d["key"]: d for d in self.config.get_definitions()}
        return self._definitions_cache

    @staticmethod
    def _same_id(a, b) -> bool:
        """IDs are compared case-insensitively so 'a1b2' finds 'A1B2'."""
        return str(a or "").strip().upper() == str(b or "").strip().upper()

    def ensure_loaded(self) -> None:
        """Loads (creating any missing files) on first use; a no-op afterwards."""
        if self.data:
            return

        for field in self._definitions().values():
            full_path = os.path.join(self.handler.directory, field["filename"])

            if not os.path.exists(full_path):
                self.handler.write_file(field["filename"], field["header"])

            self.data[field["key"]] = self.handler.read_file(field["filename"])

    # ------------------------------------------------------------------ reading

    def get_all(self, category: str) -> list[dict]:
        """Returns all records for a category (empty list if unknown)."""
        self.ensure_loaded()
        return self.data.get(category.strip().lower(), [])

    def get_by_id(self, lead_id: str) -> list[dict]:
        """Returns [{category: [rows]}] for the ID. Rows are copies."""
        self.ensure_loaded()
        full_lead = {
            category: [dict(row) for row in rows if self._same_id(row.get("ID"), lead_id)]
            for category, rows in self.data.items()
        }
        return [full_lead]

    def get_category(self, key: str) -> list[dict]:
        """Returns a whole category; raises KeyError for an unknown one."""
        self.ensure_loaded()
        return self.data[key]

    def search(self, term: str, category: str | None = None) -> list[dict]:
        """Partial, case-insensitive search across every non-ID column."""
        self.ensure_loaded()
        term = term.strip().lower()
        if not term:
            return []

        categories = [category.strip().lower()] if category else list(self.data)

        ids = {
            row["ID"]
            for cat in categories
            for row in self.data.get(cat, [])
            if row.get("ID")
            and any(term in str(value).lower() for key, value in row.items() if key != "ID")
        }

        return [self.get_by_id(lead_id)[0] for lead_id in sorted(ids)]

    # ------------------------------------------------------------------ writing

    def add(self, category: str, record: dict) -> None:
        """Adds a record to a category in memory."""
        self.ensure_loaded()
        self.data[category].append(record)

    def save(self, category: str) -> None:
        """Writes one category back to its CSV file."""
        definition = self._definitions()[category]
        self.handler.save_files(definition["filename"], self.data[category], definition["header"])

    def remove_lead(self, lead_id: str) -> str:
        """Deletes a lead from every category that contains it."""
        self.ensure_loaded()
        removed = False

        for category in list(self.data):
            kept = [row for row in self.data[category] if not self._same_id(row.get("ID"), lead_id)]
            if len(kept) != len(self.data[category]):
                self.data[category] = kept
                self.save(category)
                removed = True

        if not removed:
            return f"Unable to locate lead {lead_id}"
        return f"lead: {lead_id} has been removed."

    def modify_lead(self, lead_id: str, category: str, key: str, change: str) -> str:
        """Updates a field, matching category and field names case-insensitively.

        Returns an error message (and changes nothing) for an unknown category,
        an unknown/read-only field, or a missing lead.
        """
        self.ensure_loaded()

        cat = category.strip().lower()
        if cat not in self.data:
            return f"Unknown category '{category}'. Valid: {', '.join(self.data)}"

        header = self._definitions().get(cat, {}).get("header", [])
        fields = {h.lower(): h for h in header}
        field = fields.get(key.strip().lower())

        if field is None or field == "ID":
            editable = ", ".join(h for h in header if h != "ID")
            return f"Unknown or read-only field '{key}' in {cat}. Editable: {editable}"

        for row in self.data[cat]:
            if self._same_id(row.get("ID"), lead_id):
                row[field] = change
                self.save(cat)
                return f"lead: {lead_id} {field} updated to {change}"

        return f"Unable to locate lead {lead_id} in {cat}"

    def create_new_lead(self) -> str:
        """Creates an empty lead with a fresh ID across all categories."""
        self.ensure_loaded()
        existing_ids = {
            str(row.get("ID", "")).upper() for rows in self.data.values() for row in rows
        }

        lead_id = self.generate_id()
        while lead_id in existing_ids:
            lead_id = self.generate_id()

        for definition in self._definitions().values():
            category = definition["key"]
            record = {"ID": lead_id}
            record.update({key: "" for key in definition["header"] if key != "ID"})

            self.data[category].append(record)
            self.save(category)

        return f"New lead created with id of : {lead_id}"

    def save_score(self, result: dict) -> None:
        """Inserts or replaces the score row for a lead."""
        self.ensure_loaded()
        scores = self.data["scores"]

        for score in scores:
            if self._same_id(score.get("ID"), result.get("ID")):
                score.update({k: result.get(k) for k in
                              ("Score", "Reasoning", "Confidence", "Date Scored")})
                self.save("scores")
                return

        scores.append(result)
        self.save("scores")




        
    
    