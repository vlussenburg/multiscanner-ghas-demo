# Multi-scanner → GHAS demo

End-to-end demo that runs **four independent OSS security scanners** against a deliberately-vulnerable FastAPI target and surfaces every finding in **GitHub Code Scanning** (the Security tab) via SARIF.

The thesis: any scanner that produces SARIF lands in GHAS, regardless of vendor. Teams don't pick a scanner — they pick a *surface*. GHAS is that surface; SARIF is the open contract that lets every scanner feed it.

## What runs

| Layer | Tool | Vendor | Output | Lands in |
|---|---|---|---|---|
| **DAST** (API) | `forallsecure/mapi-action` | Mayhem | SARIF | Security → `Mayhem-API` |
| **SAST** (Python) | `semgrep/semgrep` (`--config=auto`) | Semgrep | SARIF | Security → `Semgrep-OSS` |
| **SCA** (image) | `aquasecurity/trivy-action` | Aqua | SARIF | Security → `Trivy` |
| **SBOM** (image) | `anchore/sbom-action` (Syft) | Anchore | SPDX-JSON | Build artifact + Insights → Dependency graph |

Three SARIF uploads → three category filters in the Security-tab dropdown. Three different vendors, one unified UI, one triage workflow, one audit trail. **That's the slide-3 thesis, demonstrated.**

## The target

`api/` is a FastAPI service from the upstream [ForAllSecure-CustomerSolutions/mayhem-demo](https://github.com/ForAllSecure-CustomerSolutions/mayhem-demo) with intentional **SQL injection**, **path traversal**, and **auth bypass** vulnerabilities. Backed by Redis. Runs on HTTPS port 8443 with a self-signed cert generated at image build.

Why this target: it has surface area for *all four* scanner categories at once — Python source for SAST, Python deps + base image for SCA + SBOM, running HTTP API for DAST.

## Repo layout

```
.
├── .github/workflows/security.yml  # 5-job multi-scanner pipeline
├── api/                            # Vulnerable FastAPI target
│   ├── Dockerfile                  # python:3.9-slim + uvicorn + self-signed certs
│   ├── requirements.txt            # FastAPI, redis-py, etc.
│   ├── generate-certs.sh
│   └── app/
│       ├── main.py                 # the vulnerable endpoints
│       └── config.py
├── docker-compose.yml              # api + redis (used by mapi job + local dev)
└── README.md
```

The workflow lives at [`.github/workflows/security.yml`](.github/workflows/security.yml).

## One-time setup (≈ 5 min)

1. **Push this repo to a public GitHub repo.**
   Public so GHAS Code Scanning is free; private repos need GHAS-licensed seats.

   ```sh
   cd demo
   git init && git add . && git commit -m "Initial multi-scanner demo"
   gh repo create vlussenburg/multiscanner-ghas-demo --public --source=. --push
   ```

2. **Add the Mayhem secret + workspace variable** in repo settings → Secrets and variables → Actions:
   - **Secret** `MAYHEM_TOKEN` — your token from <https://app.mayhem.security/-/installation>
   - **Variable** `MAYHEM_WORKSPACE` — your workspace slug (URL segment after `/app.mayhem.security/`)

3. **Enable Code Scanning** in Security → "Set up code scanning" (one click; GitHub remembers).

## Running

Manually:

```sh
gh workflow run security.yml -f mapi_duration=120
gh run watch
```

Auto: pushes to `main` (or PRs) that touch `demo/**` or the workflow file kick off the run.

End-to-end wall-clock (parallel jobs):

| Job | Time |
|---|---|
| `build` (api image → GHCR) | ~45 s |
| `semgrep` (SAST) | ~30 s |
| `trivy` (SCA) | ~30 s |
| `sbom` (Syft) | ~15 s |
| `mapi` (DAST, 120 s default) | ~3 min |
| **Total (longest path)** | **~4 min** |

Bump `mapi_duration` to 600 for a deeper DAST sweep (~7 min total).

## What you see after a run

**Security → Code scanning alerts** populated with:
- Mayhem API findings (SQLi, path traversal, etc.) — category `Mayhem-API`
- Semgrep findings (Python source patterns) — category `Semgrep-OSS`
- Trivy findings (vulnerable Python packages, base-image CVEs) — category `Trivy`

**Insights → Dependency graph → SBOM** shows the SPDX SBOM Syft generated.

Filter by category in the Security tab dropdown to show "this is the SARIF from scanner X" — that's the live demo of the unified surface.

## Why this matters

- Three different vendors (Mayhem, Semgrep, Aqua/Trivy), one Security tab. The pattern works for Snyk, Veracode, Checkmarx, Grype, anything that outputs SARIF.
- The Action call differs per scanner — but **every** SARIF upload uses the canonical `github/codeql-action/upload-sarif@v3`. SARIF is the open contract; Code Scanning is the open surface.
- SBOM via `anchore/sbom-action` also pushes to GitHub's **Dependency Graph snapshot endpoint** (`dependency-snapshot: true`), so the SBOM shows up in two places: as a build artifact and in the repo's native dependency graph.
- This is the `~$X / committer / month` value of GHAS. The customer keeps their existing scanner stack; GitHub provides triage, dedup, audit, and PR integration on top.

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
- GHAS Code Scanning: **free for public repos**
- GHCR storage: free for public images

## Provenance

Vulnerable target lifted from [ForAllSecure-CustomerSolutions/mayhem-demo](https://github.com/ForAllSecure-CustomerSolutions/mayhem-demo) (MIT). Workflow + scanner orchestration + this README rewritten from scratch.
