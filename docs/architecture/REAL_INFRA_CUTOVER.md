# Real-Infrastructure Cutover

Status: Reference (not yet actionable)
Date: 2026-09-22

## Purpose

Every agent under `mcp/*-mcp` today operates on a **local stand-in**: real SQLite databases, real JSON manifests, real X.509 certs, real PBKDF2 password checks — but not real Oracle 19c / Content Server 23.4 / xPlore 22.1 P19 / Tomcat 10 / OTDS 23.4. This was a deliberate, confirmed choice: `dmdb01`, `dmcs01`, `dmxp01`, `dmapp01`, `otds01` don't resolve from this machine, and no licensed OpenText/Oracle installer media exists in this environment (see `mcp/*/README.md` for the same caveat stated per agent).

This document is the answer to "when real infrastructure exists, what changes?" — a checklist and per-agent migration note, written directly from the code as it stands today. **It is not itself a code change**, and none of it can be implemented or tested until the infrastructure it describes actually exists — writing that code now would be guesswork with nothing to verify it against.

## 1. Global prerequisites

Before any agent can flip from simulated to real, these must all be true:

1. **Network reachability** to every host in `documentum-ai-platform-poc/config/desired-state.yaml`'s `hosts` block (`dmdb01`, `dmcs01`, `dmxp01`, `dmapp01`, `otds01`) — the same `nslookup` check that failed earlier confirms this is currently false for all five.
2. **SSH/OS-level access** to each host, for the "Documentum Automation Worker" layer (ADR-016, target architecture §9). This is the single biggest gap: it doesn't exist as code anywhere in this repo yet, only as README stubs under `automation/ansible/{oracle,content-server,xplore,tomcat,da}/`. Every `install()`-type tool call (`oracle.install`, `cs.install`, `tomcat.install`) needs this before anything else — installing software is an OS-level action no database driver or REST client can do on its own.
3. **Licensed installer media** for Oracle 19c and every OpenText component, staged somewhere each host can reach, plus license keys resolvable through SECURITY-MCP.
4. **A real secrets backend.** `config/desired-state.yaml` already declares `security.secrets_backend: vault`, but `mcp/security-mcp/src/security_mcp/vault_store.py` is a local JSON file (`data/vault.json`, gitignored). This has to become a real Vault client before any other agent's credential resolution can be real — see §2 and the rollout order in §4.

## 2. The migration mechanism

Rather than rewriting each `*_ops.py` module in place, give each one a **pluggable backend**: the existing class (`OracleAgent`, `ContentServerAgent`, `OtdsAgent`, `XploreAgent`, `TomcatAgent`, `DaAgent`) keeps its current method signatures — those are already what `server.py` calls and what the test suites exercise — and a new real-backend class implements the same methods against the real system. A config/env flag per agent (e.g. `ORACLE_MCP_BACKEND=simulated|real`, following the existing `DOCUMENTUM_AI_PLATFORM_*` env-var convention in `agent_common.paths`) selects which one `server.py` instantiates.

This matters for two reasons:
- **Nothing already working has to change or risk breaking.** All 113 existing tests keep exercising the simulated backend unchanged.
- **Agents can cut over independently**, in the order infrastructure actually becomes available (§4), rather than as one atomic rewrite.

One piece needs **no** pluggable backend at all: `agent_common.component_store.ComponentStore`. It's a JSON-file "last-known state" cache — that's a reasonable role to keep regardless of whether a real driver or a local stand-in populated it. This is why VALIDATOR-MCP (§3.9) is expected to need zero changes: it only ever reads `ComponentStore` state, never calls another agent's tools directly.

## 3. Per-agent migration notes

### 3.1 SECURITY-MCP (`mcp/security-mcp/src/security_mcp/vault_store.py`)
- **Infra needed**: a reachable Vault (or equivalent) instance; credentials for the automation account itself.
- **Code changes**: replace `read_vault`/`write_vault`/`put_secret`'s local-JSON implementation with a real client (e.g. the `hvac` package). `agent_common.secrets_client.resolve_secret`'s signature (`resolve_secret(vault_path, ref) -> value`) can stay conceptually the same — every other agent's call site doesn't need to change, only what's behind it.
- **First in rollout order**: every other agent's real backend needs real credentials from here.

### 3.2 DB-MCP (`mcp/oracle-mcp/src/oracle_mcp/oracle_ops.py`)
- **Infra needed**: network access to `dmdb01:1521` (per `desired-state.yaml`'s `hosts.database`); SSH/OS access for listener setup; an Oracle admin credential resolvable via SECURITY-MCP.
- **Code changes**:
  - `create_database`/`create_tablespace`/`create_user` currently operate on a local SQLite file with simplified catalog tables (`__tablespaces`, `__users`). These become real Oracle DDL (`CREATE TABLESPACE ... DATAFILE ...`, `CREATE USER ... IDENTIFIED BY ...`, `GRANT ...`) via a real driver (e.g. `oracledb`).
  - `test_connection`/`health` swap `sqlite3.connect(...)` for `oracledb.connect(...)` and a real `SELECT 1 FROM DUAL`.
  - `create_listener` is currently pure record-keeping (its own return value says so) — real listener setup needs `listener.ora` generation + `lsnrctl start`, which requires the automation-worker/SSH layer from §1, not just a DB driver.
  - Credentials: `orchestrator_mcp/deploy_cli.py` currently passes a literal `"placeholder-not-a-real-hash"` for the new DB user — this must resolve a real secret via SECURITY-MCP instead.
- **Unchanged**: the dependency-ordering logic itself (`create_tablespace` requiring a database to exist first, etc.) — those checks are already real, just against local state instead of a real catalog.

### 3.3 CS-MCP (`mcp/content-server-mcp/src/content_server_mcp/cs_ops.py`)
- **Infra needed**: `dmcs01` reachable; CS installer media + license; SSH/OS access.
- **Code changes**: `install` becomes a real silent-install invocation (OpenText's response-file pattern) via the automation-worker layer. `configure_docbroker` and `create_repository` become real docbroker file edits and `dm_repository_config_program` invocations instead of `ComponentStore` manifest entries. `test_repository` becomes a real DFC/`iapi` connection test.
- **Unchanged**: the cross-component dependency check in `create_repository` (`ComponentStore.peek(..., "oracle")`) keeps working exactly as written — it just ends up reading whatever DB-MCP's real backend now writes into its own `ComponentStore`, since that abstraction doesn't change (§2).

### 3.4 OTDS-MCP (`mcp/otds-mcp/src/otds_mcp/otds_ops.py`)
- **Infra needed**: `otds01:8443` reachable.
- **Code changes**: `validate_tls` currently *generates* a local self-signed cert (since there's nothing real to inspect) — it should instead fetch and validate the certificate OTDS is actually serving (`ssl.get_server_certificate((host, port))`). `configure_identity_source`, `register_user`, and `test_authentication` become real OTDS Admin/REST API calls instead of the local PBKDF2-backed user store.
- **Unchanged**: none of the cert-parsing/password-hashing *logic* was fake — `cryptography` and `agent_common.password` are real libraries doing real work today. What changes is the data source (generated locally vs. fetched from a real server), not the validation technique.

### 3.5 XPLORE-MCP (`mcp/xplore-mcp/src/xplore_mcp/xplore_ops.py`)
- **Infra needed**: `dmxp01` reachable; CS already real (xPlore registers against a real repository).
- **Code changes**: this is the largest *behavioral* change of any agent. `search_test` currently runs a genuine local inverted-index search — built specifically because no real xPlore was reachable — and needs to become a real xPlore `dsearch` query instead. `register_repository`, `create_collection`, and `index_status` become real IndexAdmin API calls.
- **Unchanged**: the dependency chain enforcement (`register_repository` requiring the CS repository to exist) — same pattern as CS-MCP/DB-MCP.

### 3.6 APP-MCP (`mcp/tomcat-mcp/src/tomcat_mcp/tomcat_ops.py`)
- **Infra needed**: `dmapp01` reachable; SSH/OS access; the resolved-compatible JDK actually installable there.
- **Code changes**: `install` becomes a real Tomcat + JDK installation via the automation-worker layer.
- **Unchanged**: `precheck`'s Java-compatibility-matrix enforcement (reading `compatibility/java.yaml`, hard-stopping on `UNKNOWN`/`VERIFY`) is already real and infra-independent — it doesn't change at all.

### 3.7 DA-MCP (`mcp/da-mcp/src/da_mcp/da_ops.py`)
- **Infra needed**: Tomcat and CS already real.
- **Code changes**: `deploy` becomes a real WAR deployment to Tomcat. `login_test` currently reads OTDS-MCP's local user-store state directly (`ComponentStore.peek(..., "otds")`) and verifies the password locally — it should instead make a real HTTP/DFC login call against the deployed DA instance. The **property being tested doesn't change** (does the DA → OTDS/CS authentication path actually work) — only the mechanism (local state read vs. network call).

### 3.8 COMPATIBILITY-MCP (`compatibility/*.yaml`)
- Not a code change. Every file in `compatibility/` already states explicitly that its data is illustrative, not sourced from OpenText's real compatibility documentation (ADR-007 requires the latter). Cutover here means replacing the YAML *data* with real support-matrix entries — `compatibility_mcp/matrix.py`'s reading logic doesn't need to change.

### 3.9 VALIDATOR-MCP (`mcp/validator-mcp/src/validator_mcp/validator_ops.py`)
- **Expected: zero changes.** It only ever reads `ComponentStore` state and xPlore's index-file document counts — it never calls another agent's MCP tools itself (that's `deploy_cli.py`'s job). As long as each real backend keeps writing its results into `ComponentStore` the same shape it does today, golden-transaction aggregation keeps working unmodified.

### 3.10 Orchestrator dispatch (`mcp/orchestrator-mcp/src/orchestrator_mcp/deploy_cli.py`)
- **Code changes**: today it hardcodes demo values inline — `"dmcs01"`/`1489` for the docbroker, a literal placeholder password hash for the DB user, `"jane.doe"`/a literal password for the OTDS/DA login demo. Cutover means loading real host/port values from `config/desired-state.yaml` instead of the inline literals, and resolving every credential through SECURITY-MCP's `secret.resolve` rather than passing plaintext.
- **Unchanged**: the pipeline structure itself — compatibility gate → DB → CS → OTDS → concurrent xPlore/Tomcat+DA branches → Validator, gated by `policy.check`/`approval.request` — doesn't depend on simulated vs. real backends at all.

## 4. Suggested rollout order

Matches real dependencies, not file order:

```
SECURITY-MCP (real vault)
        │
        ▼
     DB-MCP
        │
        ▼
     CS-MCP
        │
        ▼
    OTDS-MCP
        │
   ┌────┴────┐
   ▼         ▼
XPLORE-MCP  APP-MCP → DA-MCP
   │         │
   └────┬────┘
        ▼
  VALIDATOR-MCP (expected: no change needed)
        │
        ▼
  deploy_cli.py credential/host wiring (last — depends on every
  agent's real backend already existing)
```

## Caveats

Specifics above (exact OpenText CLI invocations, exact REST endpoint paths, exact driver package names) are best-known-pattern illustrations, not verified against OpenText's actual current documentation — confirm each against the real support matrix and installation guides (target architecture §15) before acting on it, per ADR-007's standing rule against inferring certification/procedure rather than verifying it.
