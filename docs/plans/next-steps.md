# SDDG next steps

Written 11 Nov 2026 (session 1: analyse and design). Session 2 executes it, one milestone at a time.

This is a milestone plan, not a step-by-step task list. Before coding a milestone, session 2 expands it into
tasks with exact tests (superpowers:writing-plans), then builds it.

## 1. Where things stand

Audited: `github.com/RonakVataliya/SDDG` `main` at `95f4dee`.

- Web: typecheck, 95 tests and build pass. AI service: 172 tests pass, 28 skipped (need Kroki). API tests need a
  database and were not run.
- The AI service and API implement seven diagram types. The web app offers only Use Case
  (`apps/web/src/features/generate/diagram-types.ts` marks the rest `available: false`).
- Each diagram is one LLM call that returns a typed spec; code turns the spec into PlantUML/DOT. The LLM never
  writes diagram syntax. Keep this.
- There is no shared model behind the diagrams (FR16). Stored items hold name, description and links only.
  `apps/api/core/diagram_models.py::build_ai_model` sends `attributes=[]`, `type="human"`, `cardinality=None`,
  so every diagram re-invents those from the requirement text.
- Jobs run in-process (`JOB_SLOTS` semaphore of 5 in `routers/integrated.py`); a restart fails them.
- No CI on `main`.

Unmerged branches worth keeping: `ai-extraction` (requirements-first flow, LLM gateway, chunking, eval harness),
`Input_methods_and_Validation`, `diagram_validation` (#39, API only), `visual_customisation` (#38),
`project_management`. `feat/completion-notifications` (#36) is 49 commits behind and needs a rewrite.

Not verified in session 1: issues #30-#43 (GitHub was not linked), the API test suite, and the local build
`D:\Claude\SDDG\SDDG-Upgraded-Refined`.

## 2. Decisions

| # | Decision |
|---|---|
| D1 | The plan serves two horizons: the course evaluation (work finished by 18 Nov 2026, deadline 2-5 Dec) and the product after the semester. |
| D2 | Until the evaluation: GitHub `main` plus teammate branches, small fixes only. Nobody's branch is rewritten. |
| D3 | After the evaluation: the local build `SDDG-Upgraded-Refined` becomes the product base, in `SDDG-Private`, once verified (M7). |
| D4 | Capacity: 20+ hours before 18 Nov, 15+ hours a week after. The product half is assumed to be Ronak alone. |
| D5 | A shared model is built first in the product half. Every diagram element references a model item. |
| D6 | New dimensions, in order: cross-diagram design linter with completeness score; change-request impact with semantic diff; scaffold export (SQL DDL + OpenAPI skeleton). |
| D7 | Reduce LLM work: code-based split by default; DFD, class and Use Case built from the model by code; rename/add/remove edits done directly. Each change ships only if the golden set scores no worse. |
| D8 | SDDG as an MCP server is a small, last milestone. |
| D9 | Claude never commits or pushes to `RonakVataliya/SDDG`. Milestones M1-M6 are delivered to Ronak as branches in `SDDG-Private` (or per-commit zips) for him to apply. |

## 3. Rejected, and why

| Idea | Why not |
|---|---|
| Push the local build before the evaluation | 90 unreviewed commits a week before the deadline; conflicts with all open branches; grading is individual. |
| As-built drift (import code/schema, diff against the design) | Needs parsers for real schemas; least proven; no base to diff against until M8 exists. Revisit after M13. |
| Gap-driven clarification interview | Another LLM path competing for the same free-tier daily quota. Revisit after M10 frees quota. |
| SRS generation from the model | Users arrive with an SRS. Low value. |
| Evaluation harness as a new idea | Already built on `ai-extraction`. It is used as a gate (M5, M9), not rebuilt. |
| Durable job queue before the evaluation | Medium effort, invisible in a demo; the local build must be checked first for what it already has. |
| Rule-based extraction replacing the LLM extraction nodes | Extraction is the one step that needs language understanding. Only merging calls is in scope (M9, optional). |

## 4. Milestones

Tags: **[FABLE]** where a design mistake is expensive (LLM pipeline, model-to-diagram mapping, evaluation
harness, security and access control). Everything else **[OPUS]**.

Every milestone ends with: web `npm test && npm run typecheck && npm run build`, AI service `pytest`, and the
API test scripts against a test database. A milestone is merged only when all pass.

### Horizon A: before 18 Nov, on `main`

Order matters: M1 first, M5 before M4 (both edit the same web files), M6 last.

#### M1. CI on main [OPUS: standard workflow file, no design risk]
- Acceptance: a pull request runs web test/typecheck/build and AI-service pytest; a failing test blocks the check.
  API tests run only if a `TEST_DATABASE_URL` secret exists, otherwise they are skipped with a visible notice.
- Files: `.github/workflows/ci.yml` (new).
- Tests: the workflow itself; prove it by a PR with a deliberately failing test.
- Shippable: adds a file only.

#### M2. Consent and correctness fixes [FABLE: access-control behaviour on AI paths]
- Acceptance:
  1. `POST /diagrams/{id}/revisions`, flag `answer` and flag `apply-fix` return the same 403 `consent_required`
     as `POST /projects/{id}/inputs` when consent is missing or outdated.
  2. The web app names the provider from one place; the input page no longer says "Google Gemini" while the
     policy says "Groq". The name comes from the API (`GET /me/consent` gains `ai_provider`), not a constant.
  3. `apply-fix` clears the project confirmation (`touch_project(clear_confirmation=True)`).
  4. Submitting text whose statements already exist in the project (same normalised text) does not add them
     again; the job reports how many were skipped.
- Files: `apps/api/routers/integrated.py`, `apps/api/routers/flags.py`, `apps/api/core/db.py`,
  `apps/web/src/features/input/input-page.tsx`, `apps/web/src/features/privacy/*`,
  `apps/web/src/api/openapi.draft.yaml`, `apps/web/src/mocks/handlers.ts`.
- Tests: `tests_access.py` (consent on each path), `tests_flags.py` (confirmation cleared), `tests_integration.py`
  (duplicate submit), one web test for the provider label.
- Shippable: no schema change. Conflicts with `ai-extraction` in `integrated.py`; if M5 lands first, rebase onto it.

#### M3. AI quotas [FABLE: abuse limits protect the only LLM budget]
- Acceptance: per-user daily caps on extraction jobs, generation jobs and revisions, and one deployment-wide
  daily cap, all from environment variables with safe defaults. Over the cap returns 429 with a plain message
  and the time it resets. A second extraction for a project that already has one queued or running returns 409.
- First step: read how the local build did this (its notes call it T12) and port that design rather than invent
  a second one. `ai-extraction` adds an `llm_usage` table (`apps/api/migrations/0004_llm_usage.sql`); reuse it
  if M5 has landed.
- Files: `apps/api/core/limits.py` (new), `apps/api/routers/integrated.py`, `apps/api/schema.sql`,
  `apps/api/.env.example`, README configuration table.
- Tests: `apps/api/tests_limits.py` (new): under cap, at cap, reset next day, deployment cap, duplicate job.
- Shippable: schema change is additive and idempotent, as `schema.sql` already is.

#### M5. Merge `ai-extraction` [FABLE: changes the LLM pipeline and the workflow]
- Acceptance: branch rebased on current `main`; all suites pass; `SPLIT_MODE` defaults to the code-based split
  with LLM fallback for prose; one golden-set run on Groq is committed to `services/ai-extraction/evals/results/`
  as the baseline; the requirements-first flow works end to end on the deployed stack with the sample text.
- Risk: 87 files, 36 of them in web/API. Rebase, do not merge-commit. Resolve `integrated.py` and
  `workspace-layout.tsx` by hand.
- Files: as on the branch.
- Tests: the branch's own (`test_llm_gateway.py`, `test_node_runner.py`, `test_evals.py`, `tests_ai_wait.py`).
- Shippable: yes if the deployed AI service gets its new environment variables first. List them in the PR.
- Owner note: the AI extraction service is Ronak's, so this PR is his.

#### M4. Turn on the six built diagram types [OPUS: flag flips plus copy; backend is done and tested]
- Acceptance: Class, Activity, Sequence, DFD, Component and State can be selected and generated in the web app;
  each card shows its own description (today every card says "Actors and goals"); the step rail no longer says
  "Use Case diagram"; `state` is added to the web `DiagramType`; README "What it does today" and "Known
  limitations" are corrected.
- Check first: Mermaid does not render on the hosted Kroki. All defaults in
  `services/ai-extraction/app/rendering/engines.py` are PlantUML or Graphviz; confirm on the deployed Kroki
  before the demo.
- Files: `apps/web/src/features/generate/diagram-types.ts`, `generate-panel.tsx`,
  `apps/web/src/routes/workspace-layout.tsx`, `apps/web/src/api/openapi.draft.yaml`, `schema.d.ts`,
  `apps/web/src/mocks/*`, `README.md`.
- Tests: web test that each type can be selected and starts a job; mock handler returns a diagram per type.
- Shippable: yes. If a type fails on the deployed stack, set only that one back to unavailable.

#### M6. Validation warnings in the viewer [OPUS: UI on an existing API]
- Acceptance: `diagram_validation` merged; the viewer lists a diagram's warnings and lets the user accept one;
  the spec `errors` the AI service already returns are stored instead of dropped.
- Also here, small accessibility fixes in the same file: a text list of the diagram's elements under the image
  (the data is already in `diagram.elements`), and requirement text reachable without hover.
- Files: `apps/api/routers/validation.py` (from the branch), `apps/api/routers/integrated.py`
  (`store_generated_diagram`), `apps/web/src/features/viewer/viewer-page.tsx`, a new `warnings-panel.tsx`.
- Tests: `tests_validation.py` (from the branch), web tests for the panel and the element list.
- Shippable: yes. Cut this milestone first if time runs out.
- Owner note: #39 is Naisargi's; this is her merge, with the UI added on top.

**Freeze on 17 Nov.** No merges after that except fixes found in the demo run-through.

### Horizon B: after exams, in `SDDG-Private`

#### M7. Verify the local build and make it the base [FABLE: security and access review of unreviewed code]
- Acceptance: `SDDG-Upgraded-Refined` pushed to `SDDG-Private` on a branch; every suite it claims passes is
  re-run; a written check of roles and invites, quotas, account deletion and archived-project rules against the
  code; M2-M6 changes from Horizon A ported or confirmed present; a list of what its notes claim that the code
  does not do.
- Note: `SDDG-Private` `main` is a single commit from 17 Oct and is far behind `SDDG` `main`. Replace it; do not
  merge into it.
- Tests: all existing suites plus the build's Playwright smoke test.
- Shippable: nothing deploys from this milestone.

#### M8. Shared model [FABLE: every later milestone depends on this schema]
- Acceptance:
  1. Items keep what extraction already returns: entity attributes (name, type), actor type, process inputs and
     outputs, relationship cardinality. A new `items.properties` JSON column, encrypted like the other content
     columns. `build_ai_model` stops overwriting them.
  2. Every diagram element carries a `model_item_id` or is marked an assumption. No element is matched by label
     text.
  3. Renaming a model item changes its label in every diagram on the next render, without an LLM call.
  4. The review screen shows and edits attributes and cardinality.
- Design questions to settle first, in writing: where the model version lives; how a diagram records which
  model version it was drawn from; migration of existing items.
- Files: `apps/api/schema.sql`, `core/db.py`, `core/diagram_models.py`, the items router, the review page.
- Tests: round-trip of properties through extraction, storage and generation; rename propagation; migration.
- Shippable: additive column; old diagrams keep rendering from their stored source.

#### M9. DFD, class and Use Case built by code [FABLE: model-to-diagram mapping, gated by the eval harness]
- Acceptance: for each of the three types, a pure function `model -> spec` with no LLM call:
  - DFD: actors in a flow become external entities; processes, stores and flows map one to one; a flow with no
    process at either end is reported as a warning, not silently rerouted.
  - Class: one class per entity with its stored attributes; relationships with cardinality; operations omitted
    in the first version.
  - Use Case: actors, one use case per process, associations from interactions. Include/extend comes from an
    optional LLM call the user asks for.
- Gate: on the golden set, element precision and recall for each type are no worse than the LLM baseline from
  M5, and the same input gives the same diagram every time. If a type fails the gate it stays on the LLM.
- Optional, only with eval evidence: merge the actors, entities and processes extraction calls into one.
- Files: `services/ai-extraction/app/{dfd,class_diagram,usecase}/from_model.py` (new), the three services,
  `services/ai-extraction/evals/score.py`.
- Tests: unit tests per mapping rule; eval comparison committed to `evals/results/`.
- Shippable: behind a per-type setting, default off until its gate passes.

#### M10. Direct edits [OPUS: CRUD on the spec with existing validation]
- Acceptance: rename, add and remove an element or a link are done in the viewer without an LLM call and create
  a new version; the free-text box remains for anything else; a rename of a model-backed element renames the
  model item (M8).
- Files: a new `routers/edits.py`, `viewer-page.tsx`, a new edit panel.
- Tests: each operation per diagram type; removing an element removes its links; spec validation runs on every
  edit.
- Shippable: yes; the LLM edit path is untouched.

#### M11. Cross-diagram linter and completeness score [OPUS: rules are listed here; plain code]
- Acceptance: a project-level check, no LLM, that reports:
  1. a sequence participant that is neither an actor nor a class;
  2. a DFD data store with no entity;
  3. a use case with no activity or sequence diagram;
  4. an entity in no diagram; a requirement in no diagram;
  5. one model item shown under two names.
  Each finding links to the elements and requirements involved. The score is the share of checks passed, shown
  with its parts, never as a bare number.
- Files: `apps/api/core/lint.py` (new), a router, a project page section.
- Tests: one fixture project per rule, with and without the fault.
- Shippable: read-only feature.

#### M12. Change-request impact with semantic diff [OPUS: built on traceability already in the base]
- Acceptance: the user pastes a change request; SDDG shows the requirements it touches, the model items and
  diagrams that would change, and a diff (added, removed, renamed) before anything is regenerated. Applying it
  is a separate, explicit step. Matching the change text to requirements may use one LLM call; everything after
  that is code.
- Depends on: M8, and the base's out-of-date tracking (verify in M7).
- Files: `core/diff.py` (new), `core/impact.py` (new), a router, a new page.
- Tests: diff of two specs per diagram type; impact of a change to one requirement on a fixture project.
- Shippable: read-only until the user applies.

#### M13. Scaffold export [OPUS: deterministic templates]
- Acceptance: from the confirmed model, download PostgreSQL DDL (tables from entities and attributes, foreign
  keys from relationships with cardinality) and an OpenAPI 3.1 skeleton (one resource per entity, operations
  from processes). Both files parse with a standard validator. Assumptions are written as comments.
- Files: `apps/api/core/scaffold.py` (new), the export router, the export menu.
- Tests: generated DDL runs on an empty Postgres; the OpenAPI file validates; golden output for the library sample.
- Shippable: new export formats only.

#### M14. MCP server [FABLE: exposes project data to outside tools; auth design matters]
- Acceptance: read-only tools (list projects, get model, get diagram source, run linter) for a user's own
  projects, authenticated per user with a revocable token, rate limited by M3. No write tools in this milestone.
- Files: a new small service or router; token table.
- Tests: access tests mirroring `tests_access.py` (a non-member gets "not found").
- Shippable: off by default.

## 5. Stress test

Five hard questions asked of this plan, and what changed.

1. **Six milestones in six days, on a repo where other people merge. Realistic?** Only M1-M4 are safe. M5 is
   the risk and M6 is the first cut. Changed: order is M1, M2, M3, M5, M4, M6, with a freeze on 17 Nov.
2. **Why trust the local build as a base when nobody has read it?** We do not. Changed: M7 is a verification
   milestone with a written review, and nothing deploys from it.
3. **Will code-built diagrams be worse than the LLM ones?** Possibly. Changed: M9 has a per-type gate on the
   golden set and a per-type switch that stays off until the gate passes.
4. **Does Claude delivering M2-M6 blur individual grading?** It can. Changed: D9 and the owner notes; the
   branch owners make their own merges.
5. **Is the completeness score a vanity number?** It would be as a bare percentage. Changed: M11 shows the
   score only with its parts and links every finding to elements.

## 6. Open points for Ronak

- Link or paste issues #30-#43 so milestones can cite them.
- Confirm no teammate continues after the semester (D4).
- Confirm the deployed Kroki renders PlantUML and Graphviz for all seven types before M4.
- `/mattpocock-skills:grill-me` could not be started by Claude in session 1; run it yourself on this file if you
  want the interview version of section 5.
