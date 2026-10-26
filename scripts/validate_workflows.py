"""Ensure workflows embed exactly the policy functions covered by unit tests."""
import ast
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
source = ast.parse((ROOT / "scripts" / "release_policy.py").read_text())
expected = next(node for node in source.body if isinstance(node, ast.FunctionDef))
release = yaml.load((ROOT / ".github/workflows/release-please.yaml").read_text(), Loader=yaml.BaseLoader)
script = next(step["run"] for step in release["jobs"]["release"]["steps"] if step.get("id") == "policy")
embedded = script.split("# BEGIN RELEASE POLICY\n", 1)[1].split("# END RELEASE POLICY", 1)[0]
actual = ast.parse(textwrap.dedent(embedded)).body[0]
assert ast.dump(expected, include_attributes=False) == ast.dump(actual, include_attributes=False)
semantic_source = ast.parse((ROOT / "scripts/semantic_policy.py").read_text())
semantic_expected = next(node for node in semantic_source.body if isinstance(node, ast.FunctionDef))
semantic = yaml.load((ROOT / ".github/workflows/semantic-pr.yaml").read_text(), Loader=yaml.BaseLoader)
semantic_script = semantic["jobs"]["semantic"]["steps"][0]["run"]
embedded = semantic_script.split("# BEGIN SEMANTIC POLICY\n", 1)[1].split("# END SEMANTIC POLICY", 1)[0]
semantic_actual = ast.parse(textwrap.dedent(embedded)).body[0]
assert ast.dump(semantic_expected, include_attributes=False) == ast.dump(semantic_actual, include_attributes=False)
print("Embedded release and semantic policies match their tested source functions")
