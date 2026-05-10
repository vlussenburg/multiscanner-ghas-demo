# Multi-scanner → GHAS demo

End-to-end demo that surfaces security findings from **multiple scanners across multiple vendors** in a single GitHub repo's Security tab — via SARIF and the GHAS native pipeline.

The thesis: any scanner that produces SARIF lands in GitHub Code Scanning, regardless of vendor. Teams don't pick a scanner — they pick a *surface*. GHAS is that surface; SARIF is the open contract that lets every scanner feed it.

## What runs

**GHAS-native** (no YAML, configured in repo settings):

| Layer | Tool | Lands in |
|---|---|---|
| **SAST** | CodeQL — Default Setup | Security → Code scanning → `CodeQL` |
| **SCA** | Dependabot — auto on `requirements.txt` | Security → Dependabot alerts |
| **Secrets + Push Protection** | Secret scanning | Security → Secret scanning |
| **SBOM (manifest)** | Dependency graph (auto) | Insights → Dependency graph |

**Workflow** (`.github/workflows/security.yml`, 3 jobs):

| Job | Tool | Vendor | Lands in |
|---|---|---|---|
| `Build · API image` | Docker | — | GHCR |
| `DAST · Mayhem API` | `forallsecure/mapi-action` | Mayhem | Security → Code scanning → `Mayhem-API` |
| `SBOM · Syft` | `anchore/sbom-action` | Anchore | Workflow run → Step Summary + artifact |

Five distinct security signals from three different vendors, one Security tab to triage them all.

## The target

`api/` is a small FastAPI service backed by Redis. Two branches:

- **`main`** — sanitized v1: parameterized auth, validated input, scoped CORS, accurate OpenAPI spec. Zero open scanner findings.
- **`vulnerable`** — feature PR adding an admin user lookup (`admin.py`), a telemetry export endpoint (`exports.py`), and an S3 archival stub (`storage.py`). Each commit looks like normal feature work; bugs are *just bugs that slipped in* (junior-dev SQL string-format, naive path concat, "I'll move keys to env later" TODO).

Open at any time: **PR #3** — `vulnerable → main`, blocked by the failing CodeQL check.

## Repo layout

```
.
├── .github/workflows/security.yml  # build · sbom · mapi (3 jobs)
├── api/
│   ├── Dockerfile                  # python:3.11-slim + uvicorn + self-signed certs
│   ├── requirements.txt
│   ├── generate-certs.sh
│   └── app/
│       ├── main.py                 # /health, /location, /locations
│       ├── config.py
│       ├── admin.py                # vulnerable-branch-only: /admin/users
│       ├── exports.py              # vulnerable-branch-only: /export/{filename}
│       └── storage.py              # vulnerable-branch-only: hardcoded creds
├── docker-compose.yml              # api + redis (used by mapi job + local dev)
└── README.md
```

The workflow lives at [`.github/workflows/security.yml`](.github/workflows/security.yml).

## One-time setup (≈ 5 min)

1. **Push to a public GitHub repo** (public so GHAS Code Scanning is free; private repos need GHAS-licensed seats).
   ```sh
   gh repo create vlussenburg/multiscanner-ghas-demo --public --source=. --push
   ```

2. **Add the Mayhem secret + workspace variable** (Settings → Secrets and variables → Actions):
   - **Secret** `MAYHEM_TOKEN` — your token from <https://app.mayhem.security/-/installation>
   - **Variable** `MAYHEM_WORKSPACE` — your workspace slug (URL segment after `/app.mayhem.security/`)

3. **Enable GHAS-native scanning** in Security → Code security:
   - **Code scanning** → Default Setup → Set up. Defaults are fine (CodeQL covers `python` + `actions`).
   - **Secret scanning** → already on for public repos by default.
   - **Push protection** → toggle on (account-level default also works).
   - **Dependabot alerts** + **security updates** → on by default for public repos.

4. **Branch protection on `main`** (Settings → Rules → Rulesets, or legacy Branches → Add rule):
   - Required status check: `CodeQL`
   - Enforce on admins: yes
   - No required reviews / linear history / conversation resolution — keep the *only* visible blocker security-driven.

## Running

Manually:
```sh
gh workflow run security.yml -f mapi_duration=120
gh run watch
```

Auto: every push to `main` and every PR triggers the workflow.

End-to-end wall-clock (parallel jobs):

| Job | Time |
|---|---|
| `Build · API image` (build → GHCR) | ~45 s |
| `SBOM · Syft` | ~30 s |
| `DAST · Mayhem API` (120 s default) | ~3 min |
| **Total (longest path)** | **~4 min** |

CodeQL Default Setup runs on its own schedule + on push/PR; usually completes within a few minutes of the workflow.

Bump `mapi_duration` to 600 for a deeper DAST sweep (~7 min total).

## What you see after a run

- **Security → Code scanning alerts** — populated by CodeQL (SAST) + Mayhem-API (DAST), filterable by category.
- **Security → Secret scanning** — push-protection blocks at push time + alerts for any keys committed (vulnerable branch leaks AWS creds in `storage.py`).
- **Security → Dependabot alerts** — populated automatically from `api/requirements.txt`.
- **Insights → Dependency graph** — full Python dependency tree, manifest-derived SBOM downloadable as SPDX.
- **Workflow run → SBOM job → Step Summary** — inline package table from Syft (image SBOM, includes base-OS packages).
- **Workflow run → Artifacts** — `sbom-spdx.json` (full Syft output).

Open **PR #3** to see all of the above land *as PR review comments and failed checks* — blocking merge until resolved.

## Why this matters

- The five security signals come from three different vendors (GitHub, Mayhem, Anchore). The pattern works for any SARIF-producing scanner — Snyk, Veracode, Checkmarx, Semgrep, Trivy, Grype, etc.
- Every SARIF upload uses the same canonical `github/codeql-action/upload-sarif@v3` action. SARIF is the open contract; Code Scanning is the open surface.
- GHAS doesn't ship DAST, fuzzing, IAST, or runtime monitoring — that's a deliberate scope choice. The augmentation pattern via SARIF lets you keep the scanners you already trust and still get one triage UI, one audit trail, one PR experience.
- Branch protection wired to the `CodeQL` status check means **the only thing blocking merge on the demo PR is "security findings exist"** — no review noise, no policy gates. Pure security gating.

## Local sanity check (no GitHub needed)

```sh
docker compose up --build -d
curl -k https://localhost:8443/openapi.json | jq .info
docker compose down -v
```

If the API responds, the workflow's `mapi` job will work end-to-end once secrets are set.

## Cost

- Public repo + GitHub-hosted runner: **free** within Actions free tier
- Mayhem usage: counts against your workspace quota
- GHAS Code Scanning + Secret Scanning + Dependabot: **free for public repos** (GHAS license required for private)
- GHCR storage: free for public images

## Provenance

Vulnerable target lifted from [ForAllSecure-CustomerSolutions/mayhem-demo](https://github.com/ForAllSecure-CustomerSolutions/mayhem-demo) (MIT). Workflow + scanner orchestration + this README rewritten from scratch.
