# Shared GitHub workflows

Public reusable workflows for `swagner-de` repositories. Repository settings are
managed by the private `gh-rules` repository. No application repository has been
rewired yet; validation CI tests this repository without publishing artifacts.

## Workflow contracts

| Workflow | Inputs | Purpose |
| --- | --- | --- |
| `release-please.yaml` | chart path, config/manifest paths; named App secrets | Release Please + auto-merge requests; app/chart release versions and SHAs as outputs |
| `semantic-pr.yaml` | no inputs/secrets | Validate PR title and every commit for squash/rebase, using read-only API metadata without executing PR code |
| `container-check.yaml` | build context, Dockerfile | Local PR build and fixed HIGH/CRITICAL vulnerability gate; no registry credentials |
| `container-publish.yaml` | released SHA, SemVer, context/Dockerfile | Native amd64 + arm64 build/scan, SBOM, immutable GHCR tag, final-digest provenance attestation |
| `chart-check.yaml` | chart path, image repository | Dependency build, strict lint/render, published app image availability |
| `chart-publish.yaml` | chart path, released SHA, chart SemVer, image repository | Verify chart/app versions, package independently, publish to `ghcr.io/<owner>/charts` |

Every remote action is pinned to a verified commit SHA. Callers must pin these
workflows to a commit SHA as well. Renovate treats shared workflow reference changes
as **`ci(deps)`**, never `fix(deps)`.

## Merge policy

Allow both squash and rebase; disallow merge commits and retain linear history.
Humans choose the method; Renovate and Release Please default to squash.
Both the PR title and every commit subject must use Conventional Commit syntax.
Workflow-only PRs require `ci` subjects on the title and every commit, so rebased
workflow changes cannot accidentally contribute to a later release. Renovate uses
`ci(deps)` specifically. No bot exemption is granted.

The caller must trigger semantic validation on `opened`, `synchronize`, `reopened`,
and **`edited`** (title changes), as shown in `examples/semantic-caller.yaml`.
Add the observed semantic check context to required checks or to the fail-closed
aggregate CI gate; merely having the workflow file does not enforce it. The example
is documentation, not active public-consumer wiring, and uses an immutable SHA.
Large PRs whose commits/files exceed GitHub's
API limits fail closed instead of validating a partial list.

## App → Renovate → chart

`examples/release-please-config.json` demonstrates independently tracked root app
and `chart` components. Replace the illustrative versions in the example manifest
with actual last published versions when bootstrapping a consumer. Python consumers
use `release-type: python`; Go uses `go`. Configure the real chart path per repo.

1. Runtime update → required PR checks → Renovate auto-merge.
2. App release PR → required checks → App-token auto-merge → published app image.
3. Renovate discovers the published image and updates chart `appVersion` and any
   explicit default image tag/digest, using `fix(deps)`.
4. Chart release PR → required checks → App-token auto-merge → OCI chart.

Only Release Please writes chart `version`. Do not use Renovate `bumpVersion` or
shell increment scripts for the same chart. Chart-only changes are excluded from
app version calculation. Do not overwrite chart version with app version at packaging.

The chart application tracking annotation can look like:

```yaml
# renovate: image=ghcr.io/swagner-de/authentik-envoy-operator
appVersion: "0.2.8"
```

Native Renovate managers do not automatically interpret this custom annotation:
`renovate/chart-app.json` provides the regex manager for this convention, with
Docker datasource and the image as dependency name. Explicit image fields also need
the matching native Helm-values manager or a custom rule. Verify generated PR diffs
before enabling auto-merge. Use the preset
`github>swagner-de/github-workflows//renovate/chart-app` alongside the default preset.
Versions/tags must match the consumer's published image
convention (these publishers use unprefixed SemVer image tags).

## Security boundaries

- Release orchestration and publishers only run on default-branch pushes.
- Release eligibility refuses workflow-only diffs, even mislabeled `fix` commits;
  `ci`/docs changes never create releases. Release PR merge commits are processed
  so their proposed releases get tags. Mixed runtime+workflow updates may release.
- The eligibility function in `scripts/release_policy.py` is embedded in the workflow
  because checkout resolves to the **consumer**, not this repository. CI verifies the
  embedded function matches the tested source exactly.
- App tokens are scoped to the caller repository and contents/PR/issues permissions;
  supply `release-app-client-id` and `release-app-private-key` by name. Do not pass
  every secret with `inherit`. Existing numeric App IDs can be migrated to client IDs.
- Callers grant permissions explicitly. PR jobs get read-only tokens and no secrets;
  never execute PR code with `pull_request_target` publishing credentials.
- Release image builds/scans run without publishing credentials. A separate job pushes
  the scanned exported artifacts, then signs provenance for the final multiarch digest.
- Vulnerability gate currently blocks **fixable** HIGH/CRITICAL findings; unfixed
  findings remain visible and need triage. This is not blanket proof an image is safe.
- SBOMs are retained as separate 30-day artifacts. Add long-term SBOM attestation and
  scheduled deployed-image scans before production rollout.

## Production rollout still required

This bootstrap is syntactically validated, not end-to-end validated against every
application. Repository-specific smoke tests, operator E2E, UniFi privileged boot tests,
schema tests, and packaging revision logic remain local integration requirements.
The general container publisher supports amd64/arm64 applications, **not** the specialized
ARMv5/multi-app/upstream-installer adapters yet.

The immutable publishers deliberately refuse an existing version tag instead of
overwriting it. Recover a partially published release by verifying its provenance and
retrying missing attestations separately; automated idempotent recovery is not yet
implemented. Chart validation requires a published image, so initial bootstrap needs
an existing application release. Do not activate mandatory rules on missing checks.

Release Please can rebase stale release PRs (`always-update`), but workflow-only pushes
do not invoke it. If a strict-base rule makes an open release PR stale, update that PR
via an App-authenticated maintenance path without enabling new releases on CI-only pushes.

## Validation

```sh
python3 -m unittest discover -s tests -v
go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.11 .github/workflows/*.yaml
```

Use `uv run --with PyYAML==6.0.3 python scripts/validate_workflows.py` to check that
embedded policy functions match the tested source. Only release eligibility and
semantic-message behavior have custom test suites; Actionlint handles workflow
syntax. Local tests do not build containers or require release credentials.
