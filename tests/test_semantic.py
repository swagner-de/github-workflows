import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SemanticTests(unittest.TestCase):
    def test_titles_and_every_commit_are_validated(self):
        path = ROOT / "scripts/semantic_policy.py"
        self.assertTrue(path.exists(), "semantic validator missing")
        spec = importlib.util.spec_from_file_location("semantic_policy", path)
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        cases = [
            ("feat: add feature", ["feat: add feature", "fix: review feedback"], ["main.go"], False, True),
            ("chore(main): release 1.2.3", ["chore(main): release 1.2.3"], ["CHANGELOG.md"], False, True),
            ("fix!: change API", ["feat(api)!: change API\n\nBREAKING CHANGE: new API"], ["main.go"], False, True),
            ("add feature", ["feat: add feature"], ["main.go"], False, False),
            ("feat: add feature", ["wip", "feat: add feature"], ["main.go"], False, False),
            ("ci(deps): update action", ["ci(deps): update action"], [".github/workflows/ci.yaml"], True, True),
            ("fix(deps): update action", ["fix(deps): update action"], [".github/workflows/ci.yaml"], True, False),
            ("ci: adjust CI", ["fix: adjust CI"], [".github/workflows/ci.yaml"], False, False),
            ("fix(deps): update image and CI", ["fix(deps): update image"], ["Dockerfile", ".github/workflows/ci.yaml"], True, True),
            ("fix: feature", [], ["main.go"], False, False),
        ]
        for title, commits, files, renovate, expected in cases:
            with self.subTest(title=title, commits=commits):
                self.assertEqual(not policy.errors(title, commits, files, renovate), expected)


if __name__ == "__main__":
    unittest.main()
