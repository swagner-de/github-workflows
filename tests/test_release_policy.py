import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleasePolicyTests(unittest.TestCase):
    def test_policy_behavior(self):
        path = ROOT / "scripts" / "release_policy.py"
        self.assertTrue(path.exists(), "release eligibility policy is missing")
        spec = importlib.util.spec_from_file_location("release_policy", path)
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        cases = [
            ("fix(deps): update checkout", [".github/workflows/ci.yaml"], False),
            ("ci(deps): update shared workflows", [".github/workflows/release.yaml"], False),
            ("fix(deps): update base image", ["Dockerfile"], True),
            ("fix(deps): update library", ["go.mod", "go.sum"], True),
            ("fix(deps): update app", ["chart/Chart.yaml"], True),
            ("docs: update usage", ["README.md"], False),
            ("fix: mixed update", ["Dockerfile", ".github/workflows/ci.yaml"], True),
            ("chore(main): release 1.2.3", ["CHANGELOG.md"], True),
            ("fix: empty diff", [], False),
        ]
        for message, paths, expected in cases:
            with self.subTest(message=message):
                self.assertEqual(policy.eligible(message, paths), expected)


if __name__ == "__main__":
    unittest.main()
