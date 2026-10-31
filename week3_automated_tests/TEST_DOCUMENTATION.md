# Test Documentation — Week 3: financekit

**Module under test:** `financekit` (personal-finance mathematics, stdlib only)
**Framework:** pytest 9 (+ pytest-cov for coverage)
**Result:** **129 test items, 129 passed**, **98% branch coverage**
**How to run:** `python -m pytest` (details in §2)
**TDD narrative and evidence:** [`docs/TDD_PROCESS.md`](docs/TDD_PROCESS.md),
[`docs/tdd_evidence/`](docs/tdd_evidence/), [`docs/coverage_report.txt`](docs/coverage_report.txt)
**Requirement-to-output map:** [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md)
(indices all 9 execution figures and raw transcripts in `docs/evidence/`)
**Work/problem record:** [`docs/WORK_LOG.md`](docs/WORK_LOG.md)

---

## 1. The module at a glance

`financekit` was designed to be *easy to test hard*: pure functions, no
global state, no hidden I/O except the two functions in `io.py`, and one
documented rate convention per submodule (percent in `interest`/`loans`,
decimal in `investments`/`statistics`).

| Submodule | Responsibility | Public functions |
|---|---|---|
| `financekit/interest.py` | Simple/compound interest, discounting | `simple_interest`, `compound_amount`, `compound_interest`, `effective_annual_rate`, `future_value`, `present_value`, `rule_of_72`, `years_to_double` |
| `financekit/loans.py` | EMI and amortization | `monthly_payment`, `amortization_schedule`, `loan_summary`, `AmortizationRow` |
| `financekit/investments.py` | Project appraisal | `npv`, `irr`, `cagr`, `sip_future_value`, `required_monthly_saving` |
| `financekit/statistics.py` | Return/price analytics | `mean_return`, `returns_variance`, `returns_stdev`, `cumulative_return`, `sharpe_ratio`, `max_drawdown`, `correlation` |
| `financekit/io.py` | CSV in/out | `load_cashflows`, `save_amortization_schedule` |
| `financekit/reports.py` | Integration surface | `build_loan_report`, `build_investment_report`, `analyze_cashflow_file` |
| `financekit/validation.py` | One home for all input rules | `ensure_number`, `ensure_positive`, `ensure_series`, ... |

## 2. Running the tests

```bash
pip install -r requirements-dev.txt   # pytest + pytest-cov (dev-only)

python -m pytest                      # whole suite (129 tests)
python -m pytest -v                   # one line per test
python -m pytest -m unit              # only isolated unit tests (104)
python -m pytest -m integration       # only cross-module / file tests (14)
python -m pytest -m edge              # boundary & error cases (58, overlaps markers)
python -m pytest tests/test_loans.py  # a single file
python -m pytest -k irr               # tests whose name contains "irr"
python -m pytest --cov=financekit --cov-branch --cov-report=term-missing
python -m pytest -x --tb=short        # stop at first failure, short tracebacks
python examples/demo.py               # see the library work end-to-end
```

The suite needs no network, no fixtures on disk and no test order: every
test that touches files uses pytest's `tmp_path`, so runs are isolated and
repeatable in any clean environment.

## 3. Methodology

### 3.1 Test-Driven Development (RED → GREEN → REFACTOR)

The suite was written from the *specification* before the implementation
existed. The full story, with captured terminal evidence, is in
[`docs/TDD_PROCESS.md`](docs/TDD_PROCESS.md):

| Phase | Evidence file | Result |
|---|---|---|
| RED — 118 tests written against stubs | `docs/tdd_evidence/01_red_phase.txt` | **117 failed, 1 passed** (only the import/version smoke test) |
| GREEN — implementation written to satisfy the tests | `docs/tdd_evidence/02_green_phase.txt` | **118 passed** |
| Coverage-driven cycle — 11 tests added for unexercised branches | `tests/test_coverage_driven.py` | coverage 94% → **98%** |
| REFACTOR — internals improved, tests untouched | `docs/tdd_evidence/03_refactor_phase.txt` | **129 passed** |

### 3.2 Techniques used, and why

| Technique | Where | Why it matters here |
|---|---|---|
| **Known-answer (oracle) tests** | EMI 8,884.88; NPV −49.59; SIP 12,682.50 | Expected values were computed by hand *before* coding, so a wrong formula cannot “agree with itself” |
| **`pytest.mark.parametrize`** | interest, investments, statistics tables | One readable test function exercises 4–11 input/output pairs, including the zeros |
| **Property / invariant tests** | PV∘FV round-trip; principal components sum to the loan; NPV(IRR) ≈ 0; balances monotone | Verifies the *relationships* financial code must keep, not just spot values |
| **Fixtures** (`conftest.py`) | reference loan, cashflows, returns, prices, CSV factory | The arrange step exists once; tests read as pure act/assert |
| **Boundary & negative tests** (`@pytest.mark.edge`) | 58 items | Zero rate (the EMI formula divides by zero there), empty series, ±100% returns, months = 0, `True` masquerading as an int |
| **`pytest.raises(..., match=...)`** | all error tests | Checks both the exception *type* and that the message helps the user (e.g. “line 3”) |
| **`pytest.approx`** | every float assertion | Financial floats are compared with explicit tolerances instead of brittle equality |
| **Real temp files** (`tmp_path`) | `test_io.py`, integration | I/O is tested against the real filesystem — no mocks that could hide encoding/newline bugs |
| **Markers** | `unit` / `integration` / `edge` | Fast feedback subsets during development; registered in `pyproject.toml` |
| **Branch coverage** | pytest-cov | Drove the final 11 tests; remaining gaps are analysed in §6 |
| **Immutability test** | `AmortizationRow` is a frozen dataclass | A schedule is a record; a test proves it cannot be silently edited |

## 4. Test inventory by file

Counts are *collected items* (parametrization expands functions into cases):
53 test functions → **129 items**.

### `tests/test_interest.py` — 29 items (unit)

| Test | Covers | Why chosen |
|---|---|---|
| `test_simple_interest` (×6) | Textbook case + zero rate/principal/time + fractional years | The zeros are where careless formulas divide or misbehave |
| `test_compound_amount` (×4) | Annual & monthly compounding, 0%, 100% | Cross-checks `(1+r/n)^(nt)` against independent arithmetic |
| `test_compound_interest_is_amount_minus_principal` | amount − interest identity | Guards against returning the amount where interest is promised (Week 2's BUG-04 pattern) |
| `test_more_frequent_compounding_never_earns_less` | monotonicity property | Catches inverted exponents that single values might miss |
| `test_effective_annual_rate` | EAR 12.6825% for 12% nominal monthly | Standard reference value |
| `test_present_and_future_value_are_inverses` (×3) | PV∘FV round-trip | A property no single example can establish |
| `test_present_value_known_example` | 12,100 @10% × 2y → 10,000 | Anchors the round-trip to an absolute value |
| `test_rule_of_72_and_exact_years_to_double` | heuristic vs `ln2/ln(1+r)` | Two independent methods must agree to ~0.1y at 8% |
| `test_interest_rejects_invalid_inputs` (×11) | negatives, `n=0`, float/bool `n`, strings, NaN, inf | Error contract: one exception type, parameter named |

### `tests/test_loans.py` — 18 items (unit)

| Test | Covers | Why chosen |
|---|---|---|
| `test_monthly_payment` (×5) | reference loan, 5-year loan, 0%, 1 month | 0% is the divide-by-zero trap inside the annuity formula |
| `test_schedule_shape_and_first_rows` | row 1: pay 8,884.88, interest 1,000, balance 92,115.12 | Pins the exact cent-level arithmetic |
| `test_schedule_fully_repay_the_loan` | Σprincipal = 100,000; final balance 0.00; balances decrease | **The** amortization invariants, including final-instalment rounding absorption |
| `test_schedule_interest_share_declines_over_time` | interest components monotone | Defining shape of an amortizing loan |
| `test_zero_interest_schedule` | all interest 0, equal payments | Degenerate schedule must still terminate at zero |
| `test_schedule_rows_are_immutable_and_serialisable` | `FrozenInstanceError`, `to_dict` keys | Schedules are records; reports/CSV need the dict view |
| `test_loan_summary_is_internally_consistent` | total = principal + interest | Summary must agree with its own schedule |
| `test_loans_reject_invalid_inputs` (×7) | months 0/negative/float/bool, principal ≤ 0 | Instalment maths has no meaning outside the domain |

### `tests/test_investments.py` — 32 items (unit)

| Test | Covers | Why chosen |
|---|---|---|
| `test_npv` (×4) | known NPVs, 0% = plain sum, period-0 undiscounted | NPV is the suite's most reused oracle |
| `test_irr` (×4) | 10% (1y & 2y forms), 0%, 21.65% project | Closed-form cases where the solver's answer is known exactly |
| `test_irr_actually_zeroes_the_npv` | NPV(IRR) ≈ 0 on fixture cashflows | Verifies the *definition*, independent of the bisection internals |
| `test_irr_rejects_cashflows_without_a_root` (×4) | all-positive, all-negative, empty, all-zero | No sign change ⇒ no IRR; must fail loudly, not loop |
| `test_cagr` (×4) | +10%, 0%, −50% growth | Negative growth is valid input, unlike negative prices |
| `test_sip_future_value` (×4) | 12,682.50 (1y), 408,348.35 (5y), 0%, 1 month | Ordinary-annuity convention is pinned down explicitly |
| `test_required_monthly_saving_is_the_inverse_of_sip` | goal-seek inverts SIP | Inverse-function property, plus the 0% straight-line case |
| `test_investments_reject_invalid_inputs` (×10) | rate ≤ −100%, empty flows, NaN flow, bad CAGR bounds | The −100% boundary is where discounting divides by zero |

### `tests/test_statistics.py` — 25 items (unit)

| Test | Covers | Why chosen |
|---|---|---|
| `test_mean_return` | fixture mean 0.01125, single value, ±10% | Baseline correctness |
| `test_variance_and_stdev_sample_vs_population` | n−1 vs n denominators; single-value rules | Sample/population confusion is the classic silent error here |
| `test_cumulative_return` (×4) | +10%/−10% = **−1%**, +21%, zeros, empty = 0 | Compounding is not addition; the empty case is a documented design decision |
| `test_sharpe_ratio` / `..._zero_volatility...` | 0.643 & 0.357 with risk-free rate; constant series | Zero volatility must be a clear error, not `inf` |
| `test_max_drawdown` (×5) | 25% fixture fall, never-falls, later-peak case | `100→80→120→60` proves the *worst* peak-to-trough wins (50%, not 20%) |
| `test_correlation_perfect_and_inverse` | +1.0, −1.0, in-between | Both extremes of the coefficient |
| `test_statistics_reject_invalid_inputs` (×10) | empty series, non-positive prices, length mismatch, return < −100% | Economically impossible inputs are rejected, not averaged |

### `tests/test_io.py` — 6 items (integration)

| Test | Covers | Why chosen |
|---|---|---|
| `test_load_cashflows_happy_path` | fixture CSV round-trips to floats | Real file, real parser |
| `test_load_cashflows_tolerates_blank_lines_and_spaces` | messy human-made files | Robustness users actually need |
| `test_load_cashflows_reports_the_offending_line` | error says “line 3” | Actionable errors are part of the contract |
| `test_load_cashflows_rejects_a_wrong_header` | schema enforcement | A renamed column must not be silently treated as data |
| `test_load_cashflows_missing_file_and_directory` | `FileNotFoundError`, `OSError` | OS errors surface naturally instead of being masked |
| `test_save_amortization_schedule_round_trip` | 12 rows written, re-read, Σprincipal = loan | loans + io agree through a real file |

### `tests/test_reports_integration.py` — 8 items (integration)

| Test | Covers | Why chosen |
|---|---|---|
| `test_package_public_api_and_version` | every `__all__` name importable | Catches packaging/export mistakes unit tests can't see |
| `test_build_loan_report_...` | report = summary + 12-row schedule, totals agree | Two modules must tell the same story |
| `test_build_investment_report_accepts_a_good_project` | NPV 2,276.48, IRR 21.65%, payback 3, “accept” | The whole appraisal pipeline on the fixture |
| `test_..._rejects_a_bad_project` | NPV −49.59 → “reject” | Decision rule is the NPV sign |
| `test_..._without_an_irr` | all-positive flows → `irr is None`, still decides | Graceful degradation instead of an exception |
| `test_analyze_cashflow_file_end_to_end` | file → decision | io + investments wired together |
| `test_full_user_journey` | CSV in → accept; schedule → CSV out | Closest analogue of a real user's session |
| `test_reports_propagate_validation_errors` | bad inputs stay loud through composition | Integration must not swallow unit-level errors |

### `tests/test_coverage_driven.py` — 11 items (edge, final TDD cycle)

| Test | Gap it closed |
|---|---|
| `test_irr_above_one_hundred_percent_widens_the_bracket` | The IRR bracket-widening loop (root at 200%) |
| `test_irr_exactly_one_hundred_percent` | Root at the initial bracket endpoint |
| `test_investment_report_for_a_project_that_never_pays_back` | `payback_period is None` path |
| `test_load_cashflows_rejects_structurally_bad_files` (×4) | Empty file, multi-column row, `nan`, `inf` |
| `test_series_validation_rejects_non_sequences` (×4) | string/bytes/int/None passed where a series belongs |

## 5. Fixtures (`tests/conftest.py`)

| Fixture | Value | Used by |
|---|---|---|
| `standard_loan` | Rs. 1,00,000, 12%, 12 months | loans, io, integration |
| `sample_cashflows` | −10,000 / 4,000 / 5,000 / 6,000 | investments, io, integration |
| `sample_returns` | 2%, −1%, 3%, 0.5% | statistics |
| `sample_prices` | 100→110→105→120→90→95 (25% drawdown) | statistics |
| `write_cashflow_csv` | factory writing real CSVs into `tmp_path` | io, integration |
| `tmp_path` (builtin) | per-test temporary directory | all file tests |

## 6. Coverage report and the remaining 2%

```
Name                        Stmts   Miss Branch BrPart  Cover
financekit/__init__.py         10      0      0      0   100%
financekit/errors.py            2      0      0      0   100%
financekit/interest.py         34      0      0      0   100%
financekit/investments.py      53      3     20      3    92%
financekit/io.py               41      0     12      0   100%
financekit/loans.py            46      0      6      0   100%
financekit/reports.py          30      0      4      0   100%
financekit/statistics.py       52      0     14      0   100%
financekit/validation.py       42      0     18      0   100%
TOTAL                         310      3     74      3    98%
129 passed
```

The three uncovered statements are all inside `irr()` and are *defensive*
lines that bisection makes practically unreachable once a bracket exists:
the “could not be bracketed” raise (line 53), an exact-zero return at the
−99.99% bracket end (line 55), and the after-200-iterations fallback return
(line 68 — bisection halves the interval every pass, so the tolerance test
always fires first). They are deliberately **not** forced with contrived
monkey-patching: a test that exists only to touch a line would document the
test-writer's determination, not the program's behaviour. Recording the
analysis here is the professional alternative to gaming the metric.

## 7. What is intentionally *not* tested (and why)

* **Performance at scale** — the library is formulaic; micro-benchmarking
  belongs to Week 4's profiling task.
* **Currency/rounding to legal tender rules** — amounts are floats rounded
  to 2dp in schedules by documented policy; jurisdiction-specific rules are
  out of scope for a maths library.
* **Multiple-IRR cashflow signatures** — non-conventional flows can have
  several roots; `irr()` documents that it returns the root in its bracket.
  Flagged as future work (with a note in the README) rather than papered over.

## 8. How defects would be caught (mutation spot-checks performed)

During development, three deliberate mutations were injected (in a
throwaway copy — the submitted code was never modified) to confirm the suite
is *sensitive*, not just green. Changing the SIP formula to an annuity-due
(× (1+r)) failed **4 tests**; using `n` instead of `n−1` in the sample
variance failed **2 tests**; dropping the final-instalment rounding
adjustment failed **4 tests** — all three mutants killed. The transcript is
preserved in `docs/tdd_evidence/04_mutation_spotchecks.txt`. (This is a
manual preview of the mutation-testing idea discussed in the report's
future-work section.)
