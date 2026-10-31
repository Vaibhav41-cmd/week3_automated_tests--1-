# Development Work Log — Week 3

This is a phase-level record of the work sequence. It is intentionally
organised around verifiable outputs rather than unsupported time claims:
every phase below ends in a file, command result or test count that is
preserved in this submission.

| Phase | Work performed | Concrete output / decision |
|---|---|---|
| 1. Scope and oracle design | Selected a coherent finance domain; specified percent-vs-decimal rate conventions; hand-computed expected values for EMI, NPV, SIP and statistics before coding | Test expectations are independent of implementation; conventions recorded in `financekit/__init__.py` |
| 2. Testable architecture | Split the library into pure calculation modules, one CSV boundary and one validation module | `financekit/{interest,loans,investments,statistics,io,reports,validation}.py` |
| 3. RED | Created package stubs and wrote 118 test items across 6 files plus shared fixtures | **117 failed, 1 passed** — `docs/tdd_evidence/01_red_phase.txt` |
| 4. GREEN: validation + interest | Implemented finite/positive/series validators, then simple/compound/PV/FV formulas | Interest tests turned green; invalid-input contract established |
| 5. GREEN: loans | Implemented EMI, paise rounding and immutable amortization rows; final instalment absorbs rounding residue | Schedule invariants hold: Σprincipal = loan and final balance = 0.00 |
| 6. GREEN: investments + statistics | Implemented NPV, bisection IRR, CAGR, SIP inverse, moments, Sharpe, drawdown and correlation | Closed-form cases and NPV(IRR)=0 property pass |
| 7. GREEN: I/O + reports | Implemented line-numbered CSV errors, schedule export, loan/investment report composition | Full suite: **118 passed** — `02_green_phase.txt` |
| 8. Coverage cycle | Inspected uncovered branches, then wrote tests for IRR at 100%/200%, malformed CSV structures, never-payback report and non-sequence series | **129 tests, 98% branch coverage**; remaining 3 statements analysed |
| 9. REFACTOR | Extracted `_summarize_schedule`; consolidated rounding through `_round_money`; reviewed validation duplication | Same 129 tests green before and after — `03_refactor_phase.txt` |
| 10. Sensitivity check | Injected three deliberate mutations into a throwaway copy only | SIP mutant killed by 4 tests; variance mutant by 2; schedule-rounding mutant by 4 |
| 11. Evidence packaging | Generated real execution transcripts and terminal figures; measured source/test metrics by AST | `docs/evidence/`, 9 figures, evidence index |
| 12. Final clean check | Extracted the ZIP into a clean directory and repeated test, coverage and demo commands | Results reproduced for report §9 |

## Problems encountered during the work

1. **The 0% EMI case divides by zero** in the standard annuity formula. A
   dedicated straight-line branch was written and tested explicitly.
2. **IRR can have no answer** when cashflows never change sign. The solver
   reports a clear validation error and the integrated report degrades to
   `irr=None` while still making an NPV decision.
3. **Cent rounding can leave a residual balance.** The final instalment
   clears the remaining balance, turning an approximate schedule into one
   satisfying exact paise-level invariants.
4. **Coverage initially hid behind a good score.** At 94%, the uncovered
   lines were not cosmetic; they exposed whole behaviours (for example,
   the IRR bracket-widening path) that the first test pass had missed.
5. **A rendered coverage figure initially captured a missing-plugin error**
   when the development environment was reset. The evidence generator now
   records command failures visibly, and the final figure was regenerated
   after installing `requirements-dev.txt`.
