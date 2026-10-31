# TDD Process Record — Week 3

How `financekit` and its 129 tests were actually built, phase by phase.
Each phase's raw terminal output is preserved in
[`tdd_evidence/`](tdd_evidence/) so the process can be audited rather than
merely asserted.

---

## 0. Design decision before any code: what makes a module “easy to test”?

The brief requires a module structured for testing, so testability was a
design constraint, not an afterthought:

* **Pure functions everywhere possible** — same input, same output, no
  clocks, randomness or hidden files. Only `io.py` touches the disk.
* **No global mutable state** — tests never need reset logic or ordering.
* **Small, single-purpose functions** — each formula can be pinned by a
  handful of known-answer tests.
* **One validation module** — error behaviour is uniform and written once.
* **Conventions stated in the package docstring** (percent vs decimal
  rates) — the most common finance-test failure is an ambiguous spec, so
  the spec was made explicit *before* the tests encoded it.
* **Expected values computed independently first** (textbook formulas and
  hand arithmetic) and only then written into assertions.

## 1. RED — tests first

A package skeleton was created whose every function was:

```python
def monthly_payment(principal, annual_rate_percent, months):
    raise NotImplementedError("TDD stub")
```

Then 118 test items were written across six files — interest, loans,
investments, statistics, io and reporting/integration — plus shared
fixtures in `conftest.py`.

```
$ python -m pytest --tb=no -q
FAILED tests/test_interest.py::test_simple_interest[10000-5-2-1000.0]
FAILED tests/test_loans.py::test_monthly_payment[100000-12-12-8884.87...]
... (117 failures, all NotImplementedError) ...
exit_code=1
```
**117 failed, 1 passed** (`01_red_phase.txt`). The one pass is the
package-API smoke test: the skeleton imports and exposes `__version__`.
That split is itself informative — it proves the failures are *missing
behaviour*, not broken plumbing.

*Design pressure felt during RED:* writing the amortization tests forced
two specification decisions before any implementation could fudge them —
schedule rows are returned as an immutable `AmortizationRow` dataclass,
and cent-level rounding is absorbed by the final instalment so the
invariants “Σprincipal = loan” and “final balance = 0.00” hold exactly.

## 2. GREEN — the smallest honest implementation

The formulas were implemented submodule by submodule in dependency order
(`validation` → `interest` → `loans` → `investments` → `statistics` →
`io` → `reports`), running the matching test file after each one. No test
was edited to make the code pass; where an assertion and a formula
initially disagreed, the formula derivation was re-checked by hand.

```
$ python -m pytest -o addopts= -q
118 passed in 0.11s
```
(`02_green_phase.txt`)

*Notable GREEN decisions, each driven by a failing test:*

* **Zero-rate EMI**: the annuity formula divides by `(1+r)^n − 1`, so the
  0% test case required an explicit straight-line branch.
* **IRR by bisection**: Newton-Raphson can diverge on awkward cashflows;
  bisection cannot once a bracket exists, and the “no sign change” tests
  pin the error behaviour.
* **`bool` rejection**: `months=True` must not quietly mean 1 month —
  Python's `bool ⊂ int` is guarded in every validator.

## 3. Coverage-driven cycle — letting the gaps choose the next tests

First coverage run: **94% branch**. The uncovered lines were not noise;
they were unexercised *behaviour* (IRR above 100%, empty CSV files, a
never-paying-back project, non-sequence inputs). Eleven tests were added
in `tests/test_coverage_driven.py`, raising coverage to **98%** and the
suite to 129 items. The 3 remaining statements are defensive lines inside
`irr()` that bisection makes practically unreachable; they are analysed —
not gamed — in `TEST_DOCUMENTATION.md` §6.

## 4. REFACTOR — improve internals without touching a single test

With everything green, three behaviour-preserving improvements were made:

1. **Shared validators** (`financekit/validation.py`) — every public
   function checks inputs through the same helpers, so the error contract
   is uniform and each rule lives once.
2. **Single money-rounding policy** (`_round_money`, including the
   `-0.00 → 0.00` normalisation) instead of scattered `round(...)` calls.
3. **`_summarize_schedule` extracted** — `build_loan_report` previously
   computed the amortization schedule twice (once directly, once inside
   `loan_summary`); it now summarises the one schedule it already built.

```
$ python -m pytest --cov=financekit --cov-branch -o addopts= -q
129 passed in 0.30s      TOTAL coverage 98%
```
(`03_refactor_phase.txt`, also saved as `docs/coverage_report.txt`)

## 5. Sensitivity check — would the suite notice a real defect?

Three deliberate mutations were injected into a throwaway copy:

| Mutant | Result |
|---|---|
| SIP formula × (1+r) (annuity-due instead of ordinary annuity) | **4 tests failed** — killed |
| Sample variance divides by n instead of n−1 | **2 tests failed** — killed |
| Final-instalment rounding adjustment removed | **4 tests failed** — killed |

(`04_mutation_spotchecks.txt`) A suite that stays green under mutation is
decoration; this one bites.

## 6. Final check — clean environment

The submitted ZIP was extracted into a fresh directory and, from there:

* `python -m pytest` → 129 passed;
* marker subsets (`-m unit`, `-m integration`, `-m edge`) all pass;
* `python examples/demo.py` prints the verified headline numbers;
* coverage reproduced at 98% branch.

## 7. Reflections

* Writing tests first changed the *API*, for the better: immutable
  schedule rows, an explicit “empty cumulative return = 0.0” rule, and an
  investment report that returns `irr=None` instead of exploding are all
  decisions the tests demanded up front.
* The most valuable tests are the *property* ones (invariants and inverse
  functions). They say what financial code means, and they survive
  refactorings that example-only suites do not.
* Coverage is a flashlight, not a goal: it found real behavioural gaps at
  94%, and it correctly stopped being useful at 98%, where the remaining
  lines are defensive by construction.
