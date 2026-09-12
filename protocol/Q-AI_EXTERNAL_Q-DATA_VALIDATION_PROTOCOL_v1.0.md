# External Q-Data Validation Protocol for the Q-AI Framework

**Protocol status:** Frozen analysis protocol, version 1.0 (locally frozen 2026-09-12 before computational reproduction)  
**Search and verification date:** 2026-09-12  
**Intended location:** Supplementary validation study; no more than one short paragraph and one compact result table in the main manuscript.

## 1. Decision and Claim Boundary

A systematic secondary analysis is feasible, but it must be framed as **external computational corroboration of selected Q-AI operations**, not validation of the Q-AI Framework as a whole. Public Q-sort data can test deterministic ingestion, provenance capture, conventional Q-analysis reproduction, robustness analysis, and selected candidate extensions. It cannot establish that Q-AI improves educational outcomes, eliminates interpretive bias, or validates AI-specific human oversight and process claims when the source study contains no Q-AI workflow logs.

The secondary analysis will use the following claim verbs:

- **Reproduce:** independently recover a source study's reported numerical results from its raw Q-sorts.
- **Corroborate:** obtain materially equivalent results under a prespecified reanalysis.
- **Stress-test:** assess sensitivity to defensible analytic alternatives.
- **Demonstrate transportability:** run a Q-AI operation on an external dataset without claiming construct or outcome validity.
- **Do not use:** prove, fully validate, confirm truth, or replicate unless the design is a genuine independent replication.

## 2. Review Question

> Can openly accessible empirical Q-methodology datasets from engineering education, or from STEM and then adjacent education fields if necessary, independently reproduce their source results and provide a deterministic external test of selected Q-AI core operations or candidate extensions?

## 3. Fixed Scope Expansion Rule

Search and screen in this order:

1. **Engineering education:** engineering students, educators, curricula, professional formation, PBL, design education, or engineering identity.
2. **STEM education:** integrated STEM, mathematics, science, computing/IT, technology, or STEM teacher education.
3. **Methodologically adjacent education:** higher education, teacher education, or professional education.

Expansion is automatic, not discretionary:

- Stop at engineering education if at least two independent studies pass all inclusion gates.
- Otherwise add STEM education.
- Add adjacent education only if fewer than two engineering/STEM studies pass all gates.
- Adjacent-education studies may test method transportability but may not support engineering-specific substantive claims.

## 4. Information Sources and Search Strings

Search Crossref, OpenAlex, DataCite, OSF, Zenodo, Figshare, Mendeley Data, Dataverse installations, institutional repositories, and publisher supplements. Search article metadata and data-repository metadata separately.

Use the following exact concept blocks, with database-specific syntax changes recorded in the search ledger:

```text
Q block:
"Q methodology" OR "Q-methodology" OR "Q method" OR "Q-sort" OR "Q sort"

Engineering block:
"engineering education" OR "engineering student*" OR "engineering educator*"
OR "engineering design" OR "problem-based learning" OR PBL

STEM block:
"STEM education" OR "science education" OR "mathematics education"
OR "technology education" OR "computing education" OR "computer science education"

Data block:
dataset OR "raw data" OR "Q sorts" OR "Q-sort data" OR supplementary
OR replication OR repository OR matrix
```

Search results are frozen by export date. Later records enter only through a documented update search, never by ad hoc addition.

## 5. Hard Inclusion Gates

A study is eligible only when every gate is `YES`:

| Gate | Deterministic criterion |
| --- | --- |
| G1 Empirical Q study | Participants completed self-referential Q-sorts and the study used by-person factor analysis. |
| G2 Domain | The population or phenomenon falls within the active scope tier. |
| G3 Raw matrix | A complete participant-by-statement matrix is downloadable without contacting the authors. |
| G4 Q-set | Full statement text, stable statement IDs, scoring direction, and sort distribution are available. |
| G5 Analytic specification | Sample size, extraction, rotation, factor-retention rule or retained solution, and loading/flagging information are recoverable. |
| G6 Target results | The source reports enough numerical or categorical results for an independent comparison. |
| G7 Reuse permission | A license or repository terms permit scholarly computational reuse. |
| G8 Integrity | Files open, identifiers align, and each sort satisfies the documented grid or ranking constraints. |

Exclusions are coded with the first failed gate. Examples include article-only records, factor arrays without individual sorts, inaccessible statements, ordinary Likert surveys labelled as Q, and ranked-item studies that do not perform by-person factor analysis.

## 6. Candidate Prioritization

After the hard gates, rank eligible studies using the fixed score below. Resolve ties by DOI in ascending lexical order.

| Dimension | Points |
| --- | ---: |
| Engineering education | 3 |
| Other STEM education | 2 |
| Adjacent education | 1 |
| Raw sorts + statements + original analytic output | 3 |
| Raw sorts + statements only | 2 |
| Peer-reviewed article | 2 |
| Completed dissertation/thesis | 1 |
| Longitudinal, pre/post, or multi-group design | 2 |
| Single-time design | 1 |
| Open analysis code | 1 |
| Explicit open license | 1 |

Use the highest-ranked eligible engineering/STEM study as the primary reanalysis and the highest-ranked independent study as the transportability analysis. Do not optimize the selection after observing reanalysis results.

## 7. Verified Candidate Audit

### 7.1 Provisionally eligible

| Candidate | Scope and design | Accessible materials | Role | Status before analysis |
| --- | --- | --- | --- | --- |
| Pidgeon (2025), *A Q Methodology Study of Why Some People Love Mathematics*; dataset DOI `10.25946/30122956.v1`; thesis DOI `10.25946/30736379` | Mathematics/STEM; 47 participants; 45 statements; PCA and varimax; five reported factors/personas | `Participants Q sorts.xlsx`, a second analysis workbook, and a 357-page dissertation | Primary STEM reproduction; candidate persona/interpretation extension | **YES, with one declared repair.** The raw workbook contains `Q Sort !C48 = -14`, outside the documented `-4` to `+4` grid. Its row otherwise has the exact forced-grid frequencies with one `+1` missing. Apply the unique repair `-14 -> +1`, log it, and rerun with that participant excluded as a sensitivity analysis. |
| Weger (2025), *Dynamics in Pre-Service Teachers' Beliefs about Multilingualism and Linguistic Diversity in Education*; article DOI `10.1080/2331186X.2025.2533611`; data DOI `10.11587/JKSQQH` | Adjacent teacher education; pre-test `n=52`, post-test `n=35`; 30-statement intervention study | Open pre/post XLSX files, questionnaire, English method report, project plan, and curation record; CC BY 4.0 | Transportability and candidate longitudinal/pre-post extension | **Provisional YES.** Included only because fewer than two engineering/STEM datasets currently pass all gates. |
| Polat (2026), *Academicians' Opinions on the Use of Artificial Intelligence in Higher Education*; data DOI `10.6084/m9.figshare.32002857.v1` | Adjacent higher education and AI; 25 academics; 40 statements; PCA and varimax; three reported factors | Ken-Q input template, Ken-Q result workbook, dataset PDF, and collection documentation; CC BY 4.0 | Exploratory AI-domain extension and file-contract test | **Pilot only.** No linked peer-reviewed article was verified; do not use as confirmatory evidence. |

### 7.2 Relevant but currently ineligible

| Candidate | Relevance | Exclusion decision |
| --- | --- | --- |
| Tarlochan, Chaaban, and Du (2026), *Engineering Students' Agency for Sustainability in a PBL Context: Q Methodology Research*, DOI `10.1080/03043797.2026.2641122` | Direct engineering education | No downloadable participant-by-statement raw matrix verified. Fail G3 pending an update search. |
| Markman and Du (2025), *Career Orientation of First-Year Students in STEM Education*, DOI `10.1007/s10775-024-09682-7` | Direct STEM higher education | Open article located, but no raw individual Q-sort deposit verified. Fail G3. |
| McLain et al. (2021), *Preservice Teachers' Perspectives on Modelling and Explaining in STEM Subjects*, data/article DOI `10.6084/m9.figshare.14664945.v1` | STEM teacher education | Deposit contains the article PDF only. Fail G3. |
| Zagumny (2016), *Q-Test of Undergraduate Epistemology and Scientific Thought*, DOI `10.5281/zenodo.1124261` | STEM undergraduate scientific epistemology | Instrument/article located; raw participant matrix not verified. Fail G3. |
| Serdyuk, Vakaliuk, and Antonyuk (2026), *Educational Priorities in IT: A Cross-Sectional Q-Sort Study*, data DOI `10.5281/zenodo.20622109` | IT education; exceptionally complete data and code | Participants rank only eight items; reported analysis compares item ranks across groups rather than using by-person factor analysis. Fail G1. Retain as an ipsative-ranking comparator, not as Q-method validation evidence. |

This audit is not a final systematic-review yield. It is a feasibility set that justifies preregistration and a full search.

The Pidgeon anomaly was verified directly from the deposited files on 2026-09-12. Forty-six rows contain the complete 45-score signature `{-4:1, -3:3, -2:6, -1:8, 0:9, +1:8, +2:6, +3:3, +4:1}`. The remaining participant row contains the same signature except for one missing `+1` and one impossible value of `-14`. The accompanying analysis workbook contains no `-14` value, but the dissertation section searched does not document the correction. This is a useful test of Q-AI's provenance and exception-handling requirements, not a reason to conceal or normalize the error silently.

## 8. Frozen Analysis Pipeline

### Stage A: Acquisition and provenance

1. Download files only from DOI-resolved repository records.
2. Record retrieval UTC timestamp, version, filename, byte size, repository checksum, license, and URL.
3. Hash each local file with SHA-256.
4. Preserve originals read-only; analyze normalized copies.
5. Create a machine-readable manifest and decision ledger.

### Stage B: Structural validation

For each participant row:

1. Confirm unique anonymized participant ID.
2. Confirm exactly one score per statement.
3. Confirm score range and required column frequencies against the documented sort grid.
4. Confirm statement order and polarity.
5. Flag duplicate Q-sorts but do not remove them unless the source protocol defines them as duplicate records.
6. Produce a deterministic validation report; any unresolved structural error stops analysis.

An out-of-range value may be repaired only when all of the following are true: exactly one cell is invalid, the documented forced distribution identifies exactly one missing legal score, replacing the invalid value with that score restores the complete distribution, and the repair is disclosed in the manifest. The analysis must also be repeated with the affected participant excluded. Any other malformed sort fails G8 and stops analysis.

### Stage C: Exact source reproduction

Reproduce the source specification before trying any Q-AI extension:

1. Construct the by-person correlation matrix.
2. Use the source extraction and rotation method.
3. Apply the source factor-retention and defining-sort rules when fully specified.
4. Reconstruct factor loadings, defining sorts, factor arrays, distinguishing statements, consensus statements, eigenvalues, and explained variance.
5. Compare against source outputs without altering settings to improve agreement.

### Stage D: Prespecified robustness analysis

Run the same alternatives for every eligible dataset:

- PCA and centroid extraction.
- Varimax rotation; judgmental rotation only if the source provides reproducible rotation instructions.
- Retention candidates determined by parallel analysis, scree evidence, minimum two defining sorts per factor, and interpretability recorded independently.
- Loading significance threshold `2.58 / sqrt(number_of_statements)` for `p < .01`, plus the source threshold.
- A defining sort must load significantly on one retained factor and exceed every other retained loading by the prespecified confounding margin.
- Leave-one-sort-out analysis.
- Nonparametric participant bootstrap with a fixed seed list stored in the preregistration.

### Stage E: Deterministic factor alignment

Factor labels are not used for matching. Align reproduced and source factors by:

1. Permitting factor sign reversal.
2. Computing all pairwise factor-array correlations.
3. Selecting the maximum-total-correlation assignment with the Hungarian algorithm.
4. Breaking exact ties by lower source factor number and then lower reproduced factor number.

## 9. A Priori Reproduction Criteria

Classify each result without post hoc threshold changes:

| Result | Criterion |
| --- | --- |
| Exact numerical reproduction | Correlations/eigenvalues within rounding tolerance; loadings within `0.01`; factor-array integer scores identical. |
| Material corroboration | Matched factor-array correlation `>= .95`; defining-sort agreement `>= 90%`; same substantive distinguishing-statement direction for `>= 90%`. |
| Partial corroboration | At least half of source factors meet material criteria, with discrepancies fully traced to specified decisions. |
| Non-corroboration | Fewer than half meet material criteria or the source result cannot be reconstructed from the deposited files. |

Robustness is reported separately. A reproduced result can still be fragile, and a robust alternative solution does not retroactively reproduce the source solution.

## 10. Q-AI Tests Supported by External Data

### Core operations that can be tested

- Deterministic data ingestion and schema validation.
- Traceable transformation from raw Q-sorts to analysis-ready matrices.
- Reproduction of conventional Q-analysis outputs.
- Separation of computational output, interpretive judgment, and evidentiary claim.
- Complete audit trail for exclusions, parameter choices, factor alignment, and result classification.
- Cross-run determinism under a frozen environment, fixed seeds, and versioned prompts/configuration.

### Candidate extensions that can be tested

1. **Semantic Q-set coverage audit:** compare machine-generated statement groupings with source domains without changing the Q-set.
2. **Blinded factor-interpretation support:** generate factor summaries from arrays and distinguishing statements, then compare them with published interpretations using a preregistered human rubric.
3. **Ambiguity flags:** identify confounded sorts, unstable factors, semantically heterogeneous factors, and interpretations unsupported by distinguishing statements.
4. **Longitudinal/pre-post comparison:** use the Weger dataset to test whether the extension preserves time-point separation and avoids treating repeated cross-sections as paired observations.
5. **Persona audit:** use Pidgeon's source personas to test whether persona generation remains traceable to factor evidence rather than adding unsupported attributes.

### Claims these datasets cannot test

- Effectiveness of the full Q-AI core protocol as an intervention.
- Educational learning gains caused by Q-AI.
- Quality of human-AI collaboration without process logs.
- Completeness of concourse generation when the original concourse and reduction history are absent.
- Causal, population-prevalence, or cross-cultural claims.
- General validation of AI-generated interpretation.

## 11. Interpretation Evaluation

To avoid circular validation:

1. Freeze the numerical solution before interpretation.
2. Withhold source factor names and narrative findings from the interpretation process.
3. Give the interpreter only factor arrays, distinguishing/consensus statements, and approved de-identified metadata.
4. Require every interpretive sentence to cite statement IDs and factor scores/loadings.
5. Use two human raters, blinded to source labels, to score factual support, overreach, polarity errors, and semantic similarity to the source interpretation.
6. Reveal and compare source interpretations only after ratings are locked.

Agreement with a published label is not truth validation. The analysis assesses traceability and convergence with the source interpretation.

## 12. Reproducibility Package

The validation package should contain:

```text
external-q-validation/
  protocol/
    preregistration.pdf
    search-ledger.csv
    screening-decisions.csv
  data-manifest/
    source-files.csv
    sha256sums.txt
  src/
    validate_inputs.*
    reproduce_source.*
    robustness.*
    align_factors.*
    render_results.*
  config/
    frozen-analysis.yml
    environment-lock.*
  outputs/
    integrity/
    reproduction/
    robustness/
    interpretation-audit/
  README.md
```

All derived tables must be generated from scripts. Manual spreadsheet edits are prohibited.

## 13. Minimal Manuscript Footprint

The main manuscript should contain only:

1. One methods paragraph identifying the preregistered external reanalysis and its claim boundary.
2. One compact table reporting dataset, domain, source-result reproduction class, robustness class, and the Q-AI operation tested.
3. One limitations sentence stating that external reanalysis corroborates selected operations rather than validating the complete framework.

Place the search strategy, screening flow, data manifests, analytic settings, factor matching, full results, and interpretation rubrics in a supplement or external repository. Do not add a new full literature-review section to the manuscript.

## 14. Go/No-Go Rule

Proceed to manuscript reporting only if:

- at least one engineering/STEM study passes all eight gates;
- its source analysis is independently reproducible or discrepancies are conclusively explained;
- all files, scripts, decisions, and Q-AI outputs are archived; and
- the manuscript claim remains limited to the tested operations.

If no engineering/STEM study passes, report the search as a feasibility limitation in the supplement and do not substitute adjacent education evidence for an engineering-specific validation claim.
