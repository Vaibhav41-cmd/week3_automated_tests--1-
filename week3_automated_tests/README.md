# Week 3 — Automated Tests for a Python Module (`financekit`)

**Internship:** Junior Python Developer · **Task:** Week 3 of 6
**Deliverable:** a moderately complex Python module built test-first, a
comprehensive automated test suite, and documentation of the test cases
and methodology.

[`financekit`](financekit/) is a dependency-free personal-finance
mathematics library — interest, EMI/amortization, NPV/IRR/CAGR/SIP,
return statistics and CSV reporting. It was developed with strict
**Test-Driven Development**: 118 tests were written and watched failing
(117 red) before a line of implementation existed, then implemented to
green, extended by a coverage-driven cycle to **129 tests / 98% branch
coverage**, and finally refactored behind the green suite.

---

## 1. Quick start

```bash
pip install -r requirements-dev.txt     # pytest + pytest-cov (dev only)

python -m pytest                        # 129 tests, ~0.3s
python -m pytest --cov=financekit --cov-branch --cov-report=term-missing
python examples/demo.py                 # the library in action
```

```
financekit 1.0.0 demo
------------------------------------------------------------
Compound amount 10,000 @12% monthly: 11268.25
Years to double @ 8% (exact)      : 9.01 | rule of 72: 9.0

Loan Rs.1,00,000 @12% x 12 months  : EMI 8884.88 | total interest 6618.53

Project in data/sample_cashflows.csv
NPV @10%                          : 2276.48
IRR                               : 21.65%
Recommendation                    : ACCEPT
```

## 2. Project structure

```
week3_automated_tests/
├── financekit/                    # the module under test (stdlib only)
│   ├── __init__.py                # public API + rate conventions
│   ├── errors.py                  # ValidationError (a ValueError)
│   ├── validation.py              # shared input rules
│   ├── interest.py                # simple/compound interest, PV/FV
│   ├── loans.py                   # EMI + AmortizationRow schedules
│   ├── investments.py             # NPV, IRR (bisection), CAGR, SIP
│   ├── statistics.py              # mean/variance/Sharpe/drawdown/correlation
│   ├── io.py                      # cashflow CSV in, schedule CSV out
│   └── reports.py                 # integrated loan/investment reports
├── tests/                         # 53 test functions -> 129 items
│   ├── conftest.py                # shared fixtures (+ CSV factory)
│   ├── test_interest.py           # 29 items
│   ├── test_loans.py              # 18 items
│   ├── test_investments.py        # 32 items
│   ├── test_statistics.py         # 25 items
│   ├── test_io.py                 #  6 items (real temp files)
│   ├── test_reports_integration.py#  8 items (cross-module)
│   └── test_coverage_driven.py    # 11 items (final TDD cycle)
├── TEST_DOCUMENTATION.md          # every test: what, why, technique + coverage
├── docs/
│   ├── TDD_PROCESS.md             # RED -> GREEN -> REFACTOR narrative
│   ├── tdd_evidence/              # captured pytest output for each phase
│   └── coverage_report.txt        # 98% branch-coverage report
├── examples/demo.py
├── data/sample_cashflows.csv
├── pyproject.toml                 # packaging + pytest markers + coverage config
├── requirements.txt               # runtime deps: NONE
├── requirements-dev.txt           # pytest, pytest-cov
└── SUBMISSION_DESCRIPTION.txt     # 200+ word text for the portal form
```

## 3. Library tour

```python
import financekit as fk

fk.simple_interest(10_000, 5, 2)              # 1000.0
fk.compound_amount(10_000, 12, 1, 12)         # 11268.25 (monthly compounding)
fk.monthly_payment(100_000, 12, 12)           # 8884.88  (EMI)
fk.amortization_schedule(100_000, 12, 12)[0]  # AmortizationRow(month=1, ...)
fk.npv(0.10, [-1000, 500, 600])               # -49.59
fk.irr([-1000, 0, 1210])                      # 0.10
fk.cagr(10_000, 14_641, 4)                    # 0.10
fk.sip_future_value(1_000, 12, 12)            # 12682.50
fk.sharpe_ratio([0.02, -0.01, 0.03, 0.005])   # 0.643
fk.max_drawdown([100, 120, 90])               # 0.25
fk.analyze_cashflow_file("data/sample_cashflows.csv", 0.10)  # -> accept/reject report
```

**Rate conventions** (stated in `financekit/__init__.py` and pinned by
tests): `interest`/`loans` take percentages (`12` = 12%);
`investments`/`statistics` take decimals (`0.12` = 12%). Invalid inputs
raise `financekit.ValidationError` (a `ValueError`) naming the parameter.

## 4. The test suite at a glance

* **129 items**: 104 unit-marked, 14 integration-marked, 58 edge-marked
  (markers overlap — an edge case is also a unit test).
* **Techniques:** hand-computed known-answer oracles, parametrization,
  property/invariant tests (PV∘FV round-trip, Σprincipal = loan,
  NPV(IRR) ≈ 0), fixtures, `tmp_path` real-file integration,
  `pytest.approx`, `pytest.raises(match=...)`, immutability checks.
* **Coverage:** 98% branch (the 3 remaining lines are analysed, defensive
  IRR fallbacks — see `TEST_DOCUMENTATION.md` §6).
* **Sensitivity:** 3/3 manual mutation spot-checks were killed by the
  suite (`docs/tdd_evidence/04_mutation_spotchecks.txt`).

Every test, its purpose and why it was chosen:
**[`TEST_DOCUMENTATION.md`](TEST_DOCUMENTATION.md)**.
The TDD process, phase by phase with evidence:
**[`docs/TDD_PROCESS.md`](docs/TDD_PROCESS.md)**.
The requirement-to-code-to-test-to-output map:
**[`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md)**.

### Execution evidence (generated from real commands)

The figures are rendered from actual pytest/demo executions by
`python tools/generate_evidence.py` (regeneration additionally requires
Pillow for PNG rendering); the raw text transcripts are kept in
[`docs/evidence/`](docs/evidence/).

![TDD evidence chain](docs/evidence/figures/fig02_tdd_evidence_chain.png)

![Verbose pytest run](docs/evidence/figures/fig07_pytest_verbose.png)

![Branch coverage](docs/evidence/figures/fig06_coverage.png)

## 5. Requirements

| Purpose | Requirement |
|---|---|
| Use the library | Python 3.9+, **no dependencies** |
| Run the tests | `pip install -r requirements-dev.txt` (pytest, pytest-cov) |
| Optional install | `pip install .` (metadata in `pyproject.toml`) |

## 6. Known limitations / future work

* Cashflows with several sign changes can have multiple IRRs; `irr()`
  returns the root inside its bracket and documents that — enumerating
  all roots is future work, as are Hypothesis property-based tests and a
  `Decimal` money mode.

## 7. Author

Week 3 deliverable for the Junior Python Developer internship
(14-Oct-2026 → 25-Nov-2026). Builds on Week 1 (CLI design), Week 2
(debugging) — and deliberately picks up Week 2's lesson that several of
its twelve bugs were exactly the kind this week's tests exist to prevent.
