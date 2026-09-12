# Pidgeon Source-Study Reproduction Results

**Status:** Exact numerical reproduction  
**Completed:** 2026-09-12  
**Claim boundary:** Reproduction of the source Q-method analysis, not validation of the complete Q-AI framework.

## Data Integrity

- Repository-authenticated matrix: 47 participants by 45 statements.
- Forty-six raw sorts matched the required forced distribution.
- `P47/s2` at `Q Sort !C48` contained `-14`; the prespecified `+1` repair uniquely restored the distribution.
- The original workbook remains read-only and checksum-identical.
- A second 46-participant matrix excludes P47 for sensitivity analysis.

## Reproduced Method

- By-person Pearson correlation matrix.
- Principal-components extraction.
- Five retained factors.
- Varimax rotation with Kaiser row normalization, recovering the omitted KADE implementation detail.
- Hungarian factor alignment with permitted sign reversal.

## Numerical Agreement

| Factor | Loading correlation | Maximum absolute loading difference | Reproduced variance | Source variance |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.9999997 | 0.000644 | 21.02% | 21% |
| 2 | 0.9999997 | 0.000387 | 9.38% | 9% |
| 3 | 0.9999996 | 0.000665 | 12.39% | 12% |
| 4 | 0.9999986 | 0.000859 | 8.63% | 9% |
| 5 | 0.9999979 | 0.001047 | 4.82% | 5% |

The first four reported eigenvalues reproduce within rounding tolerance: `15.1093`, `3.9598`, `3.0234`, and `2.5774`. The thesis omits Factor 5's eigenvalue in its narrative; the reproduced value is `1.7614`.

All 47 primary-factor assignments agree, with factor counts `20, 7, 10, 7, 3`. All 225 integer factor-array scores are identical. All 29 source-marked distinguishing-statement directions agree when evaluated from continuous factor z-scores. The source reports no consensus statements for the five-factor solution.

## Repair Sensitivity

After excluding P47, matched factor correlations with the full repaired solution are:

`0.9963, 0.9975, 0.9945, 0.9934, 0.9718`

The five-factor structure therefore remains materially aligned when the affected participant is removed.

## Source Limitation

The thesis reports 32 significant Q-sorts, but their identities are conveyed partly through color in Table 6.2 and cannot be recovered reliably from PDF text extraction. Primary-factor membership and the factor arrays are nevertheless independently recoverable and agree exactly. The thesis also labels the `0.384` loading cutoff as `p < .001` while giving the `2.58 / sqrt(45)` formula conventionally associated with `p < .01`; both source statements remain preserved without silent correction.

No Q-AI secondary interpretation has been run, and the main manuscript has not been changed.

## Prespecified Robustness Analysis

**Stage D status:** Complete  
**Five-factor classification:** **Fragile solution** under both PCA and centroid extraction  
**Interpretability:** Pending independent assessment

Parallel analysis retained Components 1 and 2 after 1,000 within-sort permutations. Maximum-acceleration scree analysis also selected two components. Under both the source loading threshold (`0.384`) and the calculated `2.58 / sqrt(45)` threshold (`0.384604`), the full five-factor results were:

| Extraction | Defining sorts by factor | All factors have at least two | Total variance |
| --- | --- | --- | ---: |
| PCA | 16, 6, 6, 4, 1 | No | 56.24% |
| Centroid | 17, 8, 6, 5, 2 | Yes | 50.08% |

Two-, three-, and four-factor candidates met the minimum-defining-sort rule under both extraction methods. PCA candidates with five through eight factors and centroid candidates with six through eight factors contained at least one underdefined factor. Interpretability was not inferred from these numerical diagnostics.

### Five-Factor Stability

Failed or underdefined factor recovery contributes correlation zero under the frozen addendum. No factor met both the leave-one-sort-out and bootstrap stability criteria.

| Method | Factor | LOO 5th percentile | Bootstrap median | Bootstrap 5th percentile | LOO recovery | Bootstrap recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PCA | 1 | 0.947 | 0.873 | 0.560 | 100.0% | 99.9% |
| PCA | 2 | 0.913 | 0.687 | 0.420 | 100.0% | 99.9% |
| PCA | 3 | 0.920 | 0.773 | 0.347 | 100.0% | 99.9% |
| PCA | 4 | 0.633 | 0.560 | 0.240 | 100.0% | 99.8% |
| PCA | 5 | 0.000 | 0.000 | 0.000 | 0.0% | 0.0% |
| Centroid | 1 | 0.873 | 0.887 | 0.633 | 100.0% | 99.2% |
| Centroid | 2 | 0.779 | 0.713 | 0.000 | 100.0% | 91.3% |
| Centroid | 3 | 0.853 | 0.747 | 0.000 | 97.9% | 86.3% |
| Centroid | 4 | 0.000 | 0.567 | 0.000 | 63.8% | 70.3% |
| Centroid | 5 | 0.000 | 0.207 | 0.000 | 8.5% | 54.2% |

All 47 leave-one-sort-out runs completed for each method. All 1,000 centroid bootstrap runs completed. One PCA bootstrap run, frozen seed `318804317`, did not converge within 1,000 varimax iterations and was retained as zero recovery rather than discarded.

### Extraction Sensitivity

The aligned absolute factor-array correlations between the full-data PCA and centroid solutions were:

| PCA factor | Matched centroid factor | Absolute correlation |
| ---: | ---: | ---: |
| 1 | 1 | 0.927 |
| 2 | 2 | 0.867 |
| 3 | 3 | 0.940 |
| 4 | 4 | 0.600 |
| 5 | 5 | 0.000 |

The zero for PCA Factor 5 reflects its single defining sort, which fails the frozen minimum of two. The extraction comparison is descriptive and does not replace independent interpretability assessment.

## Combined Conclusion

The source-study result remains an **exact numerical reproduction**. Separately, the prespecified five-factor robustness result is **fragile** for both extraction methods because fewer than three factors satisfy all frozen stability criteria. These statements are compatible: exact reproduction establishes fidelity to the published computation, while the robustness result identifies sensitivity of the five-factor structure to retention evidence, extraction method, participant omission, and resampling. Neither result validates the complete Q-AI framework.
