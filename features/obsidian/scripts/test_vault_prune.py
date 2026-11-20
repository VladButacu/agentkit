"""Checks for retiring notes: which ones look obsolete, and the move into the archive."""

import datetime
import tempfile
import unittest
from pathlib import Path

import vault
import vault_prune

TODAY = datetime.date(2026, 11, 18)


class PruneFixture(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.vault = Path(directory.name)
        (self.vault / vault.NOTES).mkdir()
        (self.vault / vault.INBOX).mkdir()

    def note(self, name: str, updated: str, body: str = "Text.\n", folder: str = vault.NOTES) -> Path:
        path = self.vault / folder / f"{name}.md"
        path.write_text(f"---\ndescription: d\ncreated: {updated}\nupdated: {updated}\n---\n{body}")
        return path


class CandidateChecks(PruneFixture):
    def test_old_notes_are_listed_and_fresh_ones_are_not(self):
        self.note("Old", "2026-01-01")
        self.note("Fresh", "2026-11-01")
        found = vault_prune.candidates(self.vault, TODAY, days=180)
        self.assertEqual([item["note"] for item in found], ["Old"])
        self.assertEqual(found[0]["age_days"], (TODAY - datetime.date(2026, 1, 1)).days)

    def test_a_recent_review_resets_the_age(self):
        path = self.note("Checked", "2026-01-01")
        path.write_text(path.read_text().replace("updated: 2026-01-01", "updated: 2026-01-01\nreviewed: 2026-11-10"))
        self.assertEqual(vault_prune.candidates(self.vault, TODAY, days=180), [])

    def test_a_missing_path_makes_a_fresh_note_a_candidate(self):
        gone = "/no-such-dir-zq/script.py"
        here = self.vault / vault.NOTES
        self.note("Paths", "2026-11-01", f"Run `{gone}` or see `{here}` and `~/no-such-dir-zq/x.sh`.\n")
        found = vault_prune.candidates(self.vault, TODAY, days=180)
        self.assertEqual(found[0]["missing_paths"], [gone, "~/no-such-dir-zq/x.sh"])

    def test_orphans_are_flagged(self):
        self.note("Linked", "2026-01-01")
        self.note("Lonely", "2026-01-01")
        self.note("Hub", "2026-11-01", "See [[Linked]] and [[Linked#part|alias]].\n")
        found = {item["note"]: item["orphan"] for item in vault_prune.candidates(self.vault, TODAY, days=180)}
        self.assertEqual(found, {"Linked": False, "Lonely": True})

    def test_inbox_and_archive_are_left_out(self):
        self.note("Draft", "2026-01-01", folder=vault.INBOX)
        (self.vault / vault.ARCHIVE).mkdir(parents=True)
        self.note("Retired", "2026-01-01", folder=vault.ARCHIVE)
        self.assertEqual(vault_prune.candidates(self.vault, TODAY, days=180), [])

    def test_a_note_without_dates_is_judged_by_its_file_time(self):
        (self.vault / vault.NOTES / "Bare.md").write_text("No frontmatter.\n")
        self.assertEqual(vault_prune.candidates(self.vault, TODAY, days=180), [])


class ArchiveChecks(PruneFixture):
    def test_archive_moves_the_note_and_records_when_and_why(self):
        path = self.note("Old", "2026-01-01")
        target = vault_prune.archive(self.vault, path, TODAY, "Replaced by [[New]]")
        self.assertEqual(target, self.vault / vault.ARCHIVE / "Old.md")
        self.assertFalse(path.exists())
        meta = vault.properties(target)
        self.assertEqual(meta["archived"], ["2026-11-18"])
        self.assertEqual(meta["archived_reason"], ["Replaced by New"])
        self.assertEqual(meta["description"], ["d"])
        self.assertTrue(target.read_text().endswith("---\nText.\n"))

    def test_archive_adds_frontmatter_to_a_bare_note(self):
        path = self.vault / vault.NOTES / "Bare.md"
        path.write_text("Just text.\n")
        target = vault_prune.archive(self.vault, path, TODAY, "")
        self.assertEqual(vault.properties(target)["archived"], ["2026-11-18"])
        self.assertTrue(target.read_text().endswith("Just text.\n"))

    def test_archive_refuses_to_overwrite(self):
        path = self.note("Old", "2026-01-01")
        (self.vault / vault.ARCHIVE).mkdir(parents=True)
        (self.vault / vault.ARCHIVE / "Old.md").write_text("earlier\n")
        with self.assertRaises(FileExistsError):
            vault_prune.archive(self.vault, path, TODAY, "")
        self.assertTrue(path.exists())


class ProposalChecks(PruneFixture):
    def proposal(self, name: str, target: str, approved: str = "true", action: str = "archive") -> Path:
        path = self.vault / vault.INBOX / f"{name}.md"
        path.write_text(f"---\ndescription: Superseded\nkind: proposal\naction: {action}\n"
                        f"target: \"{target}\"\napproved: {approved}\n---\n")
        return path

    def test_an_approved_archive_proposal_archives_its_target_and_is_deleted(self):
        self.note("Old", "2026-01-01")
        proposal = self.proposal("Archive Old", "[[Old]]")
        touched = vault_prune.apply_approved(self.vault)
        self.assertFalse(proposal.exists())
        self.assertEqual(vault.properties(self.vault / vault.ARCHIVE / "Old.md")["archived_reason"], ["Superseded"])
        self.assertEqual(touched, {f"{vault.INBOX}/Archive Old.md", f"{vault.NOTES}/Old.md", f"{vault.ARCHIVE}/Old.md"})

    def test_unapproved_other_and_unresolvable_proposals_stay(self):
        self.note("Old", "2026-01-01")
        waiting = self.proposal("Waiting", "[[Old]]", approved="false")
        merge = self.proposal("Merge", "[[Old]]", action="merge")
        missing = self.proposal("Missing", "[[Nowhere]]")
        self.assertEqual(vault_prune.apply_approved(self.vault), set())
        self.assertTrue(all(path.exists() for path in (waiting, merge, missing)))
        self.assertTrue((self.vault / vault.NOTES / "Old.md").exists())

    def test_only_notes_in_the_notes_folder_can_be_archived(self):
        self.note("Draft", "2026-01-01", folder=vault.INBOX)
        proposal = self.proposal("Archive Draft", "[[Draft]]")
        self.assertEqual(vault_prune.apply_approved(self.vault), set())
        self.assertTrue(proposal.exists())


if __name__ == "__main__":
    unittest.main()
