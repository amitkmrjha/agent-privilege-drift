# PRD 2: Thesis Writing, Viva and Submission

**Study:** Dynamic Tool Authorization: Evaluating Least-Privilege Violations and Privilege Escalation under Failure Pressure in Open-Source Agents
**Programme:** MSc Data Science & AI/ML (LJMU / upGrad) | **Version:** 3.0 | **Date:** 2026-11-15 | **Deadline:** 2026-12-02
**Companion:** `PRD_1_Research_Implementation.md` (harness, runs, analysis). Task IDs are shared across both documents.
**Inputs reviewed:** research proposal; execution log; upGrad "Background of the study" lecture; two sample final theses (Kulkarni PDF, Harish DOCX); "Effective Thesis Writing" deck; "Using tenses in scientific writing" guide.

**Scope of this document:** everything from **literature review to examined submission**: review protocol, chapter specification, writing and style rules, marking rubric, viva deck, video, repository packaging for submission and upload. Its inputs from PRD 1 are the promised-outcomes register (PRD 1 §3), `results/numbers.json`, figures and tables.

---

## 1. Purpose and dependencies

**Purpose:** turn the study into a thesis that scores well on the final rubric (§3.1) and is submitted by 2 Dec 2026.

| Needs from PRD 1 | Used by |
|---|---|
| Promised-outcome register PO1–PO13 (PRD 1 §3) | Every chapter checks that each promise has evidence |
| Method register M1–M12 and decisions D2–D14 (PRD 1 §4) | Ch3, Ch4 |
| Inconsistency list I1–I8 (PRD 1 §5) | Ch1, Ch3 wording |
| Pilot results and deviations log | Ch4, Ch5, limitations |
| `results/numbers.json`, figures, tables (gate G4) | Ch5, Ch6, abstract, slides |

Chapters 1–4 and the literature review can be written **before** results exist; start them while batches run.

---

## 2. Review findings that shape this PRD

| # | Finding | Action |
|---|---|---|
| F1 | Both sample theses use six chapters with the proposal and research plan as appendices | §3 uses that structure |
| F2 | A literature-review method is required (scope, strings, sources, criteria, screening, appraisal, matrix, synthesis, gap, AI-use declaration) | §4 and WS1 |
| F8 | The deck gives the marking rubric and chapter rules; the tense guide gives tense rules; the proposal is partly in future tense | §3.1–3.4, T6.0, T6.11, rebalanced hours |
| F6 | Effort gap: this document needs about 98 h | §6 |

---

## 3. Thesis specification (structure from the sample theses)

| Section | Content | Source | Notes from the samples |
|---|---|---|---|
| Front matter | Title page, acknowledgements, abstract, tables of contents/tables/figures, abbreviations | | Abstract states problem, method, results, contribution in one page |
| 1 Introduction | 1.1 Background, 1.2 Problem statement, 1.3 Research questions, 1.4 Aim and objectives, 1.5 Scope, 1.6 Significance, 1.7 Structure | Proposal §1, §3–§6 | Reuse the proposal's text, then update |
| 2 Literature Review | Introduction; agents and tool use; access control and PoLP; privilege benchmarks and defences; injection benchmarks; chaos engineering and fault models; evaluation methods; discussion (gap); summary | WS1 matrix | Organised by theme; ends with the gap; includes comparison tables |
| 3 Methodology | Introduction; design; datasets and subsets; data preparation; independent variable; mediators; scaffold; models; metrics; statistics and power; pre-registration; threats to validity; ethics; experimental set-up (software, hardware); summary | Proposal §7–§8, §4 above | Include the algorithms and techniques used (ReAct, Wilcoxon, SHAP) as the Harish sample does |
| 4 Implementation (Analysis and Design) | Overview; data analysis of the benchmarks; preprocessing; harness architecture; injector; mediators; telemetry; runner; integrity checks; challenges and limitations; summary | Repo, `docs/plan/IMPLEMENTATION_PLAN.md` | Sample theses describe the experiments here |
| 5 Results and Evaluation | RQ1; RQ2; RQ3; secondary; exploratory; summary | WS5 | Quantitative, then qualitative (example traces), then performance (cost/throughput) |
| 6 Conclusion and Recommendations | Discussion; conclusion per RQ; contribution to knowledge; limitations; future recommendations | | Contribution: the metric Δ, the IBAC evaluation, the signal ranking, the open harness |
| References, additional references | Citation style per the university | | Every reference verified against the source |
| Appendices | A: research plan; B: research proposal; C: pre-registration and deviations; D: prompts, policies, schema; E: additional tables | | The samples put the proposal and plan in the appendices |

Length: take the target from the university's thesis guidelines (open question Q3). The two samples are about 30,000 words (DOCX) and 127 pages (PDF, including the appended proposal).

### 3.1 Marking rubric and where the effort should go

The final thesis is marked on these weights. The writing hours in WS6 follow them.

| Criterion | Weight | Chapter | Implication for this project |
|---|---|---|---|
| General structure, formatting, grammar, spelling, style, layout | 5 % | all | T6.0 style sheet and T6.11 style pass |
| Introduction | 10 % | Ch1 | Short, not a literature review; context, problem, gap, objectives |
| Literature review | 15 % | Ch2 | WS1 protocol; critical synthesis |
| Description of materials and methods | 20 % | Ch3 | Largest write-up item with Ch4; every objective has a method, each cited |
| Experiments, implementation, tools, development | 20 % | Ch4 | The harness, runner and integrity checks are examined, not only the results |
| Results, analysis, findings, discussion | 15 % | Ch5 | One result per objective; discussed against literature |
| Conclusion, implication, recommendations | 10 % | Ch6 | Objective → method → result → meaning → conclusion |
| Citation and references | 5 % | all | T6.9 verification |

Note that **40 % of the marks sit in methods and implementation**. Do not trade harness quality or Ch3/Ch4 write-up time for extra results.

### 3.2 Chapter-by-chapter writing rules (from the Effective Thesis Writing deck)

| Chapter | Rules |
|---|---|
| Abstract | Introduction, objective, methodology, results, conclusion. Short, concise, deep. **No citations and no graphics.** Check against the journal-style abstracts in the samples |
| 1 Introduction | Theme in brief; set the context of the problem; a scenario that motivates the objectives; highlight the gaps and how this study contributes; state the implications. It is **not a literature review**. About three specific objectives in order of importance. **An objective is not a methodology** (say what is measured, not how) |
| 2 Literature Review | Contextualise the purpose of the study: show the forest (context) then the tree (specific areas). Answer what, why and sometimes where. Use peer-reviewed papers, theses and survey papers; **avoid blogs and newspaper articles**. Build a storyline; state research gaps and challenges; use flowcharts and figures. Write only what you are confident about; balance depth (neither too basic nor perfectionist). Screen papers by abstract, then read conclusions/future work |
| 3 Methodology | Answers "how". Use verbs. Describe how each objective is addressed, in the same order of importance. **For each objective there is a method; for each method cite a reference.** Cover workflow, dataset description, preprocessing, transformation, modelling techniques, evaluation metrics |
| 4 Analysis & Design / Implementation | Exploratory data analysis, hyperparameter tuning (here: pilot calibration), experiment details |
| 5 Results | **For each objective there is a result.** Clear and concise. Not personal ("I feel", "I believe"), no people's names. Avoid qualifiers and adverbs (extremely, possibly, of course, obviously, just) and non-gradable words used as gradable (unique, optimal, infinite). Do not cite references unless comparing or discussing. Explore each result, positive or negative. Spell out numbers below ten (except when used mathematically). Tables and figures only if meaningful; refer to them in the text and do not repeat their captions; clear legends, axis labels and line types; good resolution; draw flowcharts with draw.io |
| Discussion (in Ch5/Ch6) | Place results in the context of current and past work. For each result say whether the literature (same dataset or task) agrees. Be critical and do not copy ideas; explain differences, with statistical significance where used; use recent papers; avoid plagiarism; state limitations and what was done to reduce them |
| 6 Conclusion | Summarise principal findings in an organised way: objective → method → result → meaning → conclusion. **No references or citations.** Set the perspective: directions for future research |
| General style | Avoid slang and idiom. Use consistent tense. Keep sentences and paragraphs short and simple. Reference book: Zobel, *Writing for Computer Science* |

### 3.3 Tense rules by section (from the tenses guide)

| Section | Tense | Example for this study |
|---|---|---|
| Abstract | Past (reports your own results) | "Violation rates increased under failure injection." |
| Introduction: accepted background | Present | "LLM agents select tools at run time." |
| Introduction: previous research | Present for findings you regard as still true; **present perfect** for the research gap ("currency") | "No study has measured privilege behaviour under tool failure." |
| Methodology | **Simple past**, often passive | "Failures were injected with probability p." |
| Figures, tables, diagrams (any chapter) | Present | "Figure 5.1 shows the violation rate by failure rate." |
| Results | Past | "Llama's violation rate rose by 14 percentage points." |
| Discussion: significance | Present, with limiting words where unsure ("suggests", "may") | "This suggests that retry pressure drives escalation." |
| Discussion: summarising findings | Past, then present to interpret | |
| Conclusion | Mixed: past for what was done, present for what the findings mean, future/present for future work | |

**Conversion rule for this project:** the proposal is written in the present and future tense ("the study runs", "will be locked"). When Ch1 and Ch3 are built from the proposal, convert the design description to the **past tense** and the problem description to the present tense. The tense check is part of T6.11.

### 3.4 Style checklist (applied in T6.11 to every chapter)
- [ ] Tense matches §3.3 for the section.
- [ ] No first person or personal opinion in Results; no people's names used as agents ("Yang et al. found" is acceptable in the literature review only).
- [ ] No unsupported qualifiers or adverbs (extremely, obviously, just, of course).
- [ ] Numbers below ten spelled out, except mathematical uses; units and percentages consistent.
- [ ] Every figure and table is referred to in the text, has a meaningful caption that is not repeated in the paragraph, and has readable axes and legends.
- [ ] Results chapter has one result for each objective (O1, O2, O3); Methodology has one method for each objective, each cited.
- [ ] Introduction and Conclusion contain no unneeded citations (Conclusion has none).
- [ ] Abstract has no citations or graphics.
- [ ] Sentences are short; paragraphs are short; no slang or idioms.

---

---

## 4. Literature review protocol (from the upGrad lecture)

- **Type:** critical/narrative review with a documented, bounded search. It argues a position; it does not claim exhaustive coverage. State this in the methods.
- **Scope (PCC):** Population = LLM agents using external tools; Concept = privilege/least-privilege behaviour, access-control mediation, fault injection; Context = benchmarks and defences under stable or perturbed conditions.
- **Review questions:** (1) How is over-privileged tool use measured and defended against? (2) What perturbations have been applied in agent evaluations? (3) What is missing about failure conditions?
- **Search blocks:**
  1. ("large language model" OR "LLM agent*" OR "tool-using agent*" OR "tool-use")
  2. ("least privilege" OR "privilege escalation" OR "over-privileged" OR "access control" OR "tool authorization" OR "prompt injection")
  3. ("fault injection" OR "chaos engineering" OR "transient failure" OR "tool failure" OR "error handling")
  - Run blocks 1 AND 2; blocks 1 AND 3; blocks 1 AND 2 AND 3. Reproduce the exact strings in an appendix.
- **Sources:** arXiv (with care: appraise as preprints), IEEE Xplore, ACM DL, Scopus/Web of Science, dblp. Google Scholar only for forward chasing. Log date, string and hit count.
- **Dates and language:** 2019–2026, English; foundation works (Saltzer & Schroeder 1975; Alvaro 2015; Basiri 2016) enter through snowballing.
- **Include:** empirical studies, benchmarks and defences about tool-using LLM agents; chaos engineering foundations; access-control foundations. **Exclude:** opinion pieces with no method, blogs and newspaper articles (university guidance), duplicates, unrelated domains. Preprints, technical reports and model cards are allowed only when appraised for credibility and flagged as non-peer-reviewed; the lecture's grey-literature advice is applied within this limit and the volume is reported.
- **Screening:** flow of records identified, duplicates removed, title/abstract, full text with exclusion reasons, included. Double-screen a 10–20 % sample with the supervisor and report agreement.
- **Appraisal:** matrix with the lecture's questions (dataset representative? baseline fair? metrics appropriate? validation robust? limitations acknowledged? claim stronger than the evidence?); extract ML studies against REFORMS items.
- **Synthesis:** by theme, in sentences of the form pattern + explanation + limitation. Not paper-by-paper notes.
- **Gap:** an empirical gap (no failure pressure) and a methodological gap (stable conditions only; one guardrail style). Avoid "no one has studied X".
- **Golden thread:** problem → literature → gap → aim → objectives → method. Check each paragraph moves along it.
- **Generative AI use:** acceptable for synonym lists, first-pass templates, and checking prose; not as a search engine, screener, or source of citations. Never cite a paper that you have not opened. Declare use per the university policy.
- **Quality checklist:** use the lecture's six questions at the end of Ch2.

---

---

## 5. Work breakdown (writing, viva and submission)

**Conventions.** Priority: **P0** required; **P1** strongly wanted; **P2** drop first. Hours are estimates. "Needs" lists tasks that must finish first (some are in PRD 1).

### WS1 Literature review (follows the upGrad lecture, §4)

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T1.1 | Write the review protocol: type (critical/narrative review with a documented search), scope (PCC), review questions, 3 concept blocks, search strings, sources, date range, language, inclusion/exclusion | `docs/lit/protocol.md` | Another person could rerun the search | P0 | 2 | |
| T1.2 | Run searches (arXiv, IEEE Xplore, ACM DL, Scopus/Web of Science, dblp); log database, date, string, hits; export to a reference manager | `docs/lit/search_log.csv`, library | Counts recorded per source | P0 | 3 | T1.1 |
| T1.3 | Backward/forward snowballing from the key papers (Yang, Ji, Debenedetti, Zhang, Weng, Wallace) | Added records with route noted | Records per route reported | P1 | 1.5 | T1.2 |
| T1.4 | Screen: de-duplicate, title/abstract, full text with recorded exclusion reasons; double-screen a 10–20 % random sample with the supervisor and compute agreement | PRISMA-style flow numbers, agreement statistic | Flow diagram data complete | P0 | 3 | T1.3 |
| T1.5 | Reconcile with the proposal's 37-paper corpus: map every cited paper into the screening record | Mapping table | No cited paper is missing from the review record | P0 | 1.5 | T1.4 |
| T1.6 | Appraise and extract into the review matrix (Study, Data, Method, Metrics, Strength, Limitation, Use in gap); use REFORMS items for ML studies | `docs/lit/matrix.xlsx` | Every included study has analytical notes, not summaries | P0 | 6 | T1.4 |
| T1.7 | Synthesise by three themes (problem domain; methods and defences; evidence limitations); write synthesis sentences (pattern + explanation + limitation) | Theme notes | Each theme has cross-study claims | P0 | 4 | T1.6 |
| T1.8 | State the research gap using the gap typology (empirical gap: no failure pressure; methodological gap: only stable conditions, one guardrail style) and link to aim and objectives (golden thread) | Gap paragraph + thread diagram | Gap is defensible, not "no one has studied X" | P0 | 1.5 | T1.7 |
| T1.9 | Update Table 2.1 (comparison) using the matrix | Table 2.1 v2 | Matches the matrix | P1 | 1 | T1.6 |
| T1.10 | AI-use record for the review (what was used for, what was verified) | `docs/ai_use.md` | Meets the university's integrity policy | P0 | 0.5 | T1.1 |

### WS6 Thesis writing (chapters follow the sample theses; §3)

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T6.0 | Write a one-page style sheet from §3.2–3.4 (tense table, banned qualifiers, number rule, figure rules) and keep it open while writing | `docs/style_sheet.md` | Matches the two reference documents | P0 | 1 | |
| T6.1 | Ch1 Introduction (10 %): background, problem, RQs, aim and three ordered objectives, scope, significance, structure. Not a literature review; objectives name what is measured, not how | Draft | Golden thread visible; maps to the proposal; no literature-review passages | P0 | 5 | T6.0 |
| T6.2 | Ch2 Literature Review (15 %) from the matrix and themes; forest-then-tree order; peer-reviewed sources, no blogs or news | Draft | Synthesis not summary; ends with the gap | P0 | 10 | T1.8, T6.0 |
| T6.3 | Ch3 Methodology (20 %): workflow, datasets, preprocessing, injection, mediators, scaffold, models, metrics, statistics, power, threats, ethics, pre-registration; one cited method per objective; **past tense** | Draft | Every M-item and decision D appears; each objective has a method | P0 | 9 | T3.7, T6.0 |
| T6.4 | Ch4 Implementation (20 %): architecture, benchmark analysis, preprocessing, harness, injector, mediators, telemetry, runner, integrity checks, pilot calibration, challenges | Draft | Reproducible from the description | P0 | 8 | T2.11, T6.0 |
| T6.5 | Ch5 Results and discussion (15 %): RQ1, RQ2, RQ3, secondary, exploratory kept separate; one result per objective; discussed against the literature | Draft | Each RQ answered with effect size, CI and corrected p; style rules in §3.2 met | P0 | 8 | T5.6, T6.0 |
| T6.6 | Ch6 Conclusion (10 %): objective → method → result → meaning → conclusion; contribution to knowledge; limitations; future work; **no citations** | Draft | Answers PO7, PO8; limitations include I7 and others | P0 | 4 | T6.5 |
| T6.7 | Abstract (intro, objective, method, results, conclusion; past tense; no citations or graphics), acknowledgements, lists of tables/figures/abbreviations | Front matter | Numbers match Ch5 | P0 | 2 | T6.6 |
| T6.8 | Appendices: research plan, research proposal, pre-registration, deviations, prompts, policies, schema | Appendices | Present as in the samples | P0 | 2 | |
| T6.9 | References and citation check: every in-text citation resolves; every source opened and verified | Reference list | No unverified or invented reference | P0 | 3 | |
| T6.10 | Consistency and proofread pass; formatting to university template; similarity check; AI-use declaration | Final PDF | Numbers identical across thesis, deck, video | P0 | 3 | T6.7–T6.9, T6.11 |
| T6.11 | Style pass on every chapter using §3.4: tense by section, qualifiers, numbers, figure references, no first person in Results, convert the proposal's future/present tense in reused text to past | Style-checked chapters | Checklist ticked per chapter | P0 | 2 | T6.1–T6.8 |

### WS7 Viva and video

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T7.1 | Viva deck structure and slides (problem, gap, method, results per RQ, limits, contribution) | VDPPT | Follows the viva guidelines | P0 | 6 | T6.5 |
| T7.2 | Speaker notes and prepared answers to likely challenges | Notes | Covers: why independent Bernoulli; Llama classifying for Llama; single scaffold; subsets; power at n = 50; Q4 vs fp16 | P0 | 2 | T7.1 |
| T7.3 | Two timed rehearsals | Timing log | Within the time limit | P0 | 3 | T7.2 |
| T7.4 | Record and review the video | Video file/link | Audio and visuals clear | P0 | 3 | T7.3 |

### WS8b Submission

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T8.2 | Assemble the submission folder: thesis PDF, video link, code zip | Folder | Checklist complete | P0 | 1 | T6.10, T7.4 |
| T8.3 | Upload and verify; keep confirmation; buffer day | Receipt | Downloads verified | P0 | 1.5 | T8.2 |

**Estimated total for this PRD:** WS1 24 h, WS6 57 h, WS7 14 h, T8.2–T8.3 2.5 h, about **98 h**.

---

## 6. Schedule and gates

### 6.1 Calendar mapping (execution log)

| Log week | Dates | Tasks |
|---|---|---|
| 1–2 | 25 Oct–7 Nov | T1.1–T1.4 (start early), T6.3 draft |
| 3 | 8–14 Nov | T6.5, T6.6 once results exist; T6.2 Literature Review; supervisor Call 4 (10 Nov) |
| 4 | 15–21 Nov | T6.1, T6.7, T6.9, T6.11, T6.10 draft; send to supervisor (Call 5, 17 Nov); T7.1 |
| 5 | 22–28 Nov | Feedback; T7.2–T7.4; T6.10 final |
| Final | 29 Nov–2 Dec | T8.2, T8.3, buffer |

WS1 (literature review) has no slot in the log beyond one drafting day, so start it first because T6.2 depends on it.

### 6.2 Effort and priority
If time is short, protect Ch3 and Ch4 (40 % of the marks), then Ch2 and Ch5 (15 % each). Cut slide polish and optional figures before cutting method description. Write Ch1, Ch3, Ch4 and the literature review while batches run.

### 6.3 Gates

| Gate | Before | Checks |
|---|---|---|
| G4 | Writing Ch5 | PRD 1 gate G4: every number reproduces from raw traces |
| G5 | Submission | T6.10 consistency pass and T8.2 checklist done |

---

## 7. Non-functional requirements (writing)

| ID | Requirement |
|---|---|
| NFR-W1 | Every number is identical across thesis, deck, video and abstract (taken from `numbers.json`) |
| NFR-W2 | Every reference was opened and verified; none invented; AI use declared per university policy |
| NFR-W3 | Formatting, word limit and front matter follow the university template |
| NFR-W4 | Confirmatory and exploratory results are separated; deviations are reported |

---

## 8. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| K8 | Cited preprints not verifiable | Med | I8 / T0.5; verify all before use |
| K9 | Writing overruns | High | Draft Ch1, Ch3, Ch4 and the literature review while runs execute |
| K10 | Numbers differ across thesis, deck and video | Med | One generated `numbers.json`; T6.10 consistency pass |
| K11 | Upload or portal failure | High | Upload a day early; keep the buffer |

---

## 9. Open questions

| # | Question | Needed by |
|---|---|---|
| Q1 | Which tasks (T-IDs) are already done, and which levers have already been used? | Now |
| Q3 | University thesis template, word or page limit, citation style, viva time limit, AI-disclosure rule | Before T6.1 |
| Q5 | Is the 2 Dec deadline movable if the minimum-viable scope proves too large? | Now |

---

## 10. Traceability

| RQ / outcome | Evidence (PRD 1) | Thesis | Slides |
|---|---|---|---|
| RQ1: PO1–PO3, PO13 | T5.2 | Ch5.1 | escalation delta chart |
| RQ2: PO4–PO5 | T5.3 | Ch5.2 | utility–security plot |
| RQ3: PO6 | T5.4 | Ch5.3 | SHAP charts |
| PO7–PO8 | all results | Ch6 | conclusion slide |
| PO9–PO12 | WS3, T8.1 | Ch3, Ch4, appendices | method slide |

---

## 11. Document control

| Version | Date | Change |
|---|---|---|
| 1.0–2.1 | 2026-11-15 | Single combined PRD |
| 3.0 | 2026-11-15 | Split: this document covers writing, viva and submission; research implementation moved to PRD 1 |
