"""Ticket validation checks. Run with: python3 -m unittest discover -s skills/to-tickets/scripts"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from validate_tickets import check_tickets, main

NONE = "None (can start immediately)"


def ticket(number, blocked_by=NONE, body="- [ ] Criterion one"):
    return (
        f"# {number}: Ticket {number}\n\n"
        "**What to build:** the end-to-end behaviour.\n\n"
        f"**Blocked by:** {blocked_by}\n\n"
        "**Status:** ready-for-agent\n\n"
        f"{body}\n"
    )


def tickets(*files):
    return {name: text for name, text in files}


class TicketChecks(unittest.TestCase):
    def test_linear_chain_passes(self):
        found = check_tickets(
            tickets(
                ("01-schema.md", ticket("01")),
                ("02-api.md", ticket("02", "01: Schema")),
            )
        )
        self.assertEqual(found, [])

    def test_file_name_must_start_with_two_digit_number_and_slug(self):
        found = check_tickets(tickets(("1-schema.md", ticket("01"))))
        self.assertTrue(any("file name" in problem for problem in found), found)

    def test_heading_number_must_match_file_number(self):
        found = check_tickets(tickets(("01-schema.md", ticket("02"))))
        self.assertTrue(any("heading" in problem for problem in found), found)

    def test_numbering_must_have_no_gaps(self):
        found = check_tickets(
            tickets(("01-schema.md", ticket("01")), ("03-api.md", ticket("03")))
        )
        self.assertTrue(any("consecutive" in problem for problem in found), found)

    def test_blocker_must_exist(self):
        found = check_tickets(tickets(("01-schema.md", ticket("01", "05: Missing"))))
        self.assertTrue(any("05" in problem and "does not exist" in problem for problem in found), found)

    def test_blocker_must_come_first(self):
        found = check_tickets(
            tickets(
                ("01-schema.md", ticket("01", "02: API")),
                ("02-api.md", ticket("02")),
            )
        )
        self.assertTrue(any("must come before" in problem for problem in found), found)

    def test_blocker_without_a_number_is_rejected(self):
        found = check_tickets(tickets(("01-schema.md", ticket("01", "Schema work"))))
        self.assertTrue(any("start with a ticket number" in problem for problem in found), found)

    def test_missing_status_is_rejected(self):
        text = ticket("01").replace("**Status:** ready-for-agent\n\n", "")
        found = check_tickets(tickets(("01-schema.md", text)))
        self.assertTrue(any("Status" in problem for problem in found), found)

    def test_ticket_needs_an_acceptance_criterion(self):
        found = check_tickets(tickets(("01-schema.md", ticket("01", body="No boxes here."))))
        self.assertTrue(any("acceptance criterion" in problem for problem in found), found)

    def test_file_path_in_body_is_rejected(self):
        found = check_tickets(
            tickets(("01-schema.md", ticket("01", body="- [ ] Update src/billing/invoice.py")))
        )
        self.assertTrue(any("file path" in problem for problem in found), found)

    def test_code_fence_in_body_is_rejected(self):
        found = check_tickets(
            tickets(("01-schema.md", ticket("01", body="- [ ] Works\n\n```python\nx = 1\n```")))
        )
        self.assertTrue(any("code" in problem for problem in found), found)

    def test_and_or_is_not_a_path(self):
        found = check_tickets(
            tickets(("01-schema.md", ticket("01", body="- [ ] Handles create and/or update")))
        )
        self.assertEqual(found, [])

    def test_empty_folder_is_rejected(self):
        self.assertTrue(check_tickets({}))


class Command(unittest.TestCase):
    def run_main(self, files):
        with tempfile.TemporaryDirectory() as folder:
            for name, text in files.items():
                Path(folder, name).write_text(text, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = main([folder])
        return status, output.getvalue()

    def test_passing_folder_exits_zero(self):
        status, output = self.run_main(tickets(("01-schema.md", ticket("01"))))
        self.assertEqual(status, 0)
        self.assertIn("1 ticket", output)

    def test_failing_folder_exits_one_and_names_the_problem(self):
        status, output = self.run_main(tickets(("01-schema.md", ticket("01", "09: Gone"))))
        self.assertEqual(status, 1)
        self.assertIn("01-schema.md", output)


if __name__ == "__main__":
    unittest.main()
