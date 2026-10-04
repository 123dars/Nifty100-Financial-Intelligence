# SPRINT 3 — SCREENER ENGINE

## Assigned To: Priya Singh (PS)

## Focus: Filtering Logic, Configuration, Preset Screeners

### Sprint Scope

Implement the Screener Engine for the existing financial-analysis project.

My assigned work consists of:

**Day 15 — Filter Engine Core**

* Create `config/screener_config.yaml`
* Implement `src/screener/engine.py`
* Support 15 metric-based filters
* Support configurable comparison operators and thresholds
* Handle Financials-specific D/E exception
* Handle Debt-Free ICR edge cases
* Make the engine reusable for all presets
* Add unit/integration tests

**Day 16 — Six Preset Screeners**
Implement and test:

1. Quality Compounder
2. Value Pick
3. Growth Accelerator
4. Dividend Champion
5. Debt-Free Blue Chip
6. Turnaround Watch

Each preset must return a meaningful company set and be validated against the project requirement that the result count should be between **5 and 50 companies** on the project dataset/fixture.

---

# 1. FIRST: INSPECT THE EXISTING PROJECT

Before writing or modifying code, inspect the repository thoroughly.

Do NOT immediately start coding.

Inspect:

* `src/`
* `config/`
* `tests/`
* database/schema files
* Sprint 1 ETL/loader implementation
* Sprint 2 financial ratio implementation
* any README/specification/design documents
* existing company, financial, ratio, and sector fields
* existing utilities/helpers
* existing test conventions
* existing database access layer

Especially inspect:

* `src/analytics/ratios.py`
* `financial_ratios` table/schema
* company master table
* financial/year tables
* sector/industry columns
* existing repository/database utilities
* existing naming conventions

### Important

The Screener Engine must consume the **existing calculated financial metrics** from Sprint 2.

Do not duplicate or rewrite Sprint 2 ratio formulas unless absolutely necessary.

Do not invent different formulas for existing KPIs.

If the exact names of the 15 metrics are already defined in project documentation or the database, use those exact names.

If there is a mismatch between documentation, schema, and implementation:

1. identify the mismatch,
2. preserve existing database/schema conventions where possible,
3. document the mapping,
4. avoid silently changing Sprint 2 behavior.

---

# 2. UNDERSTAND THE DATA FLOW

The intended flow should be:

```text
Source Financial Data
        ↓
Sprint 1 ETL / SQLite
        ↓
Sprint 2 Financial Ratio Engine
        ↓
financial_ratios
        ↓
Screener Engine
        ↓
Metric Filters
        ↓
Preset Screener Rules
        ↓
Matching Companies
```

The Screener Engine should NOT calculate financial ratios from raw statements again.

It should use already calculated metrics wherever available.

---

# 3. DECIDE THE SCREENING GRAIN

Determine how screening is represented in the existing project.

Preferred behavior:

```text
Company + latest available year
```

unless the project specification explicitly requires another year-selection strategy.

The engine should not accidentally return the same company multiple times simply because multiple historical years exist.

Create/reuse a helper that determines the relevant observation for each company.

Example conceptual flow:

```text
Company A
 ├── FY2021
 ├── FY2022
 ├── FY2023
 ├── FY2024  ← latest available
 └── FY2025

Screener operates on the selected/latest observation
```

If the project already defines a different screening year, follow that definition instead.

The year-selection rule must be deterministic and tested.

---

# 4. DESIGN THE CONFIGURATION FILE

Create:

```text
config/screener_config.yaml
```

The YAML should become the central configuration source for:

* available metrics
* filter operators
* thresholds
* sector exceptions
* preset definitions
* edge-case behavior
* minimum/maximum result-count validation
* sorting/output preferences where appropriate

Do not hard-code preset thresholds throughout Python files.

The Python engine should read rules from YAML.

---

# 5. RECOMMENDED YAML STRUCTURE

Use a structure similar to:

```yaml
version: 1

screening:
  observation: latest_available_year

result_validation:
  min_companies: 5
  max_companies: 50

missing_value_policy: fail

metrics:
  metric_name:
    source_column: existing_metric_column
    type: numeric

operators:
  - gt
  - gte
  - lt
  - lte
  - eq
  - neq

exceptions:

  debt_to_equity:
    enabled: true
    excluded_sectors:
      - Banking
      - Financial Services
      - NBFC
      - Insurance

  interest_coverage_ratio:
    debt_free_policy:
      enabled: true
      debt_zero_threshold: 0
      zero_interest_policy: inf
      negative_interest_policy: inf

presets:

  quality_compounder:
    description: ...
    filters:
      - metric: ...
        operator: ...
        value: ...

  value_pick:
    ...

  growth_accelerator:
    ...

  dividend_champion:
    ...

  debt_free_blue_chip:
    ...

  turnaround_watch:
    ...
```

This exact structure can be adapted to the existing project's conventions.

Do not blindly copy the example fields if the repository already has a configuration architecture.

---

# 6. DEFINE THE 15 FILTERABLE METRICS

The project specification defines 15 metric filters.

Before implementing the engine, identify the exact 15 metric names from:

* existing schema
* Sprint 2 KPI list
* project specification
* ratio engine output

Create one canonical mapping.

For example conceptually:

```text
Config Metric Name
        ↓
Database/DataFrame Column
```

Do NOT assume that the YAML name and database column name are automatically identical.

Example:

```yaml
roe:
  source_column: return_on_equity
```

The actual mapping must follow the existing implementation.

### Validation requirement

The engine should validate that every configured metric refers to a valid source column/metric.

A typo such as:

```yaml
roe:
```

pointing to a non-existing field should produce a clear configuration error.

Do not silently ignore invalid metrics.

---

# 7. IMPLEMENT FILTER OPERATORS

The engine should support generic operators rather than writing separate code for every metric.

Required operators:

```text
>
>=
<
<=
==
!=
```

It is acceptable to expose config-friendly names such as:

```text
gt
gte
lt
lte
eq
neq
```

Example conceptual rule:

```yaml
- metric: ROE
  operator: gte
  value: 15
```

The engine should interpret this as:

```text
ROE >= 15
```

Another example:

```yaml
- metric: PE
  operator: lte
  value: 25
```

means:

```text
PE <= 25
```

Centralize operator handling in one function.

Do not duplicate comparison logic throughout the presets.

---

# 8. IMPLEMENT `src/screener/engine.py`

Create:

```text
src/screener/engine.py
```

Keep the implementation modular.

Recommended conceptual functions:

```python
load_screener_config()
validate_config()
resolve_metric()
apply_single_filter()
apply_filters()
handle_exceptions()
select_screening_observation()
screen()
run_preset()
validate_result_count()
```

Exact function names may be adapted to the project's style.

---

# 9. ENGINE RESPONSIBILITIES

The engine should:

1. Load configuration.
2. Validate configuration.
3. Load the required company/ratio data.
4. Select the correct observation for each company.
5. Resolve configured metric names to data columns.
6. Apply filters.
7. Apply configured exceptions.
8. Handle missing/invalid values.
9. Remove duplicate companies.
10. Return the screened company set.
11. Preserve useful metadata such as:

* company name
* ticker/symbol
* sector
* screening year
* values of relevant metrics

12. Provide deterministic output.

---

# 10. FILTER EVALUATION DESIGN

Conceptually:

```text
Input Data
   ↓
Select company observation
   ↓
For each configured filter
   ↓
Resolve metric
   ↓
Check value
   ↓
Apply operator
   ↓
True / False
   ↓
Apply exceptions
   ↓
Final eligible company
```

For multiple filters in the same preset, default behavior should be:

```text
AND
```

Example:

```text
ROE >= 15
AND
ROCE >= 15
AND
Debt/Equity <= 1
AND
Profit Growth >= threshold
```

The company must satisfy all required conditions.

Do not accidentally implement OR logic unless specifically defined by the preset.

---

# 11. MISSING VALUES

Define one consistent missing-value policy.

Recommended default:

```text
Missing metric = filter fails
```

Example:

```text
ROE = NULL
Rule = ROE >= 15

Result = FAIL
```

Do not automatically replace missing financial metrics with:

```text
0
```

unless explicitly required by the project specification.

Why:

```text
NULL ≠ 0
```

A missing financial ratio should not silently become a real numerical value.

The policy should be configurable where useful.

---

# 12. INVALID NUMERIC VALUES

Handle:

* `NaN`
* `NULL`
* `inf`
* `-inf`
* non-numeric strings
* division-by-zero artifacts

The engine should normalize or reject them according to the existing ratio-engine conventions.

Avoid silently converting invalid data into misleading financial values.

---

# 13. FINANCIALS D/E EXCEPTION

This is an explicit Sprint 3 requirement.

Debt-to-equity behaves differently for financial companies because leverage is structurally part of their business model.

The D/E filter therefore needs a configurable sector/industry exception.

Conceptually:

```text
Normal company
    ↓
Apply D/E filter

Financial company
    ↓
Skip/waive D/E filter
```

The exception must be configuration-driven.

Do not hard-code only one string such as:

```python
if sector == "Bank":
```

because the dataset may contain several financial sector labels.

Instead, define configurable excluded sectors/categories.

Example:

```yaml
debt_to_equity:
  excluded_sectors:
    - Banking
    - Financial Services
    - NBFC
    - Insurance
```

Use the exact sector names present in the repository.

### Required tests

Test at least:

```text
Normal company + acceptable D/E
Normal company + unacceptable D/E
Financial company + acceptable D/E
Financial company + high D/E
Financial company + missing D/E
```

The financial-sector behavior must be explicit and deterministic.

---

# 14. INTEREST COVERAGE RATIO — DEBT-FREE EDGE CASE

ICR:

```text
Interest Coverage Ratio = EBIT / Interest Expense
```

A debt-free company may have:

```text
Debt = 0
Interest Expense = 0
```

This can produce an undefined division:

```text
EBIT / 0
```

Do not allow this to cause:

* crash
* division-by-zero exception
* accidental filter failure
* meaningless numeric output

The handling must be explicitly defined in configuration.

---

# 15. ICR EDGE-CASE POLICY

Use the project's existing financial definitions wherever available.

Conceptually handle:

### Case A — Debt-free + zero interest

```text
Debt = 0
Interest = 0
```

This should be treated as a special case, generally representing no interest burden rather than a conventional finite ICR.

A common screening interpretation is:

```text
ICR = +∞
```

or equivalent "passes any positive ICR threshold" behavior.

Implement the project's specified behavior rather than inventing a contradictory interpretation.

### Case B — Debt-free but interest expense > 0

```text
Debt = 0
Interest > 0
```

Do NOT automatically assume ICR is infinite.

Calculate/use the existing ICR definition.

### Case C — Interest expense = 0

Handle without division-by-zero.

### Case D — Negative/invalid interest expense

Do not silently convert it to zero.

Follow the project's data-quality/ratio conventions and add an explicit test.

### Case E — Missing debt or interest data

Do not infer debt-free status from missing values.

```text
NULL debt ≠ zero debt
```

---

# 16. DEBT-FREE DETECTION

Prefer using the underlying debt field rather than relying only on the displayed D/E ratio.

For example:

```text
total_debt == 0
```

is more reliable for identifying a debt-free company than:

```text
D/E == 0
```

because ratio behavior can depend on equity and calculation conventions.

If the repository has an explicit debt metric/flag, reuse it.

Make the debt-free condition consistent throughout the engine.

---

# 17. ERROR HANDLING

The engine should fail clearly for configuration problems.

Examples:

```text
Unknown preset
Unknown metric
Unknown operator
Malformed YAML
Invalid threshold
Missing required column
Invalid sector configuration
```

Use meaningful error messages.

Bad:

```text
KeyError
```

Better:

```text
Unknown screener metric 'roe_growthk'. Expected one of: ...
```

Do not catch all exceptions and silently continue.

---

# 18. RESULT OBJECT

The screener should return structured results.

Preferred conceptual result:

```text
{
    preset_name,
    screening_year,
    total_input_companies,
    matched_companies,
    matched_count,
    applied_filters,
    exceptions_applied
}
```

The actual implementation may use:

* DataFrame
* list of records
* dataclass
* dictionary

depending on existing project architecture.

The important requirement is that downstream code can easily consume the result.

---

# 19. PRESET SCREENERS

Implement six presets through the same generic engine.

Do NOT create six completely independent filtering implementations.

Use:

```text
Preset configuration
        ↓
Generic Screener Engine
        ↓
Result
```

The presets should differ primarily by their configuration.

---

# 20. PRESET 1 — QUALITY COMPOUNDER

Purpose:

Identify companies combining:

* profitability
* capital efficiency
* sustainable growth
* healthy balance sheet
* reasonable quality indicators

Use only metrics available in the project.

Conceptual rule categories:

```text
Profitability
Capital efficiency
Growth
Debt/solvency
Optional valuation sanity check
```

Thresholds must come from the project specification or be defined in YAML.

Do not hard-code thresholds in `engine.py`.

---

# 21. PRESET 2 — VALUE PICK

Purpose:

Identify relatively attractively valued companies while maintaining reasonable financial quality.

Conceptual rule categories:

```text
Valuation
Profitability
Balance sheet
Optional earnings stability
```

Typical valuation metrics may include whatever is already available in Sprint 2, such as:

```text
P/E
P/B
EV/EBITDA
Dividend Yield
```

Do not invent a metric that is not present in the project.

---

# 22. PRESET 3 — GROWTH ACCELERATOR

Purpose:

Identify companies showing stronger-than-required growth.

Possible categories:

```text
Sales growth
Profit growth
EPS growth
ROE/ROCE
Profitability improvement
```

Use the exact KPI columns already available.

Avoid making a preset dependent on raw data that the Screener Engine is not designed to consume.

---

# 23. PRESET 4 — DIVIDEND CHAMPION

Purpose:

Identify companies with strong dividend characteristics.

Conceptual categories:

```text
Dividend yield
Dividend consistency
Payout ratio
Profitability
Balance-sheet strength
```

Use only metrics actually available in the existing project.

Be careful with payout-ratio edge cases.

For example:

```text
Negative earnings
+
dividend payout ratio
```

may make the metric invalid or economically meaningless.

Follow existing KPI conventions and explicitly test these cases where relevant.

---

# 24. PRESET 5 — DEBT-FREE BLUE CHIP

Purpose:

Identify financially strong companies with no meaningful debt burden.

Core categories:

```text
Debt-free condition
Strong profitability
Strong returns
Stable/healthy growth
Optional valuation constraint
```

This preset must specifically exercise the debt-free/ICR logic.

Expected behavior:

```text
Debt = 0
+
ICR edge case handled correctly
+
other required filters pass
=
eligible
```

---

# 25. PRESET 6 — TURNAROUND WATCH

Purpose:

Identify companies showing signs of financial improvement rather than merely having high absolute quality metrics.

Conceptual categories:

```text
Improving growth
Improving profitability
Improving operating performance
Potential balance-sheet improvement
Possible valuation condition
```

This preset is different from Quality Compounder:

```text
Quality Compounder
= already strong

Turnaround Watch
= improving / recovering
```

Use year-over-year metric data if the project specification requires improvement calculations.

Do not falsely classify a company as turnaround based only on a single static-year value.

---

# 26. PRESET CONFIGURATION

Each preset should be defined in YAML.

Example conceptual structure:

```yaml
presets:

  quality_compounder:
    enabled: true

    filters:
      - metric: METRIC_1
        operator: gte
        value: THRESHOLD_1

      - metric: METRIC_2
        operator: gte
        value: THRESHOLD_2

  value_pick:
    enabled: true
    filters: []

  growth_accelerator:
    enabled: true
    filters: []

  dividend_champion:
    enabled: true
    filters: []

  debt_free_blue_chip:
    enabled: true
    filters: []

  turnaround_watch:
    enabled: true
    filters: []
```

The actual metric names and thresholds must be populated from the project requirements.

---

# 27. DO NOT SILENTLY MANIPULATE PRESET COUNTS

The requirement says each preset should return:

```text
5–50 companies
```

Do NOT do this:

```text
if results < 5:
    automatically relax filters
```

Do NOT do this:

```text
if results > 50:
    arbitrarily cut to 50
```

That would hide problems in the screening logic.

Instead:

```text
Run preset
   ↓
Count results
   ↓
5–50?
   ├── YES → pass
   └── NO  → fail validation and report why
```

Thresholds can then be reviewed/configured intentionally.

---

# 28. RESULT COUNT VALIDATION

Create a reusable validation step:

```text
validate_result_count(results, min_count, max_count)
```

Expected behavior:

```text
count < min
    → validation failure

count > max
    → validation failure

min <= count <= max
    → pass
```

The validation message should clearly identify the preset.

Example:

```text
Preset 'value_pick' returned 3 companies.
Expected between 5 and 50.
```

---

# 29. DETERMINISTIC RESULTS

Repeated execution against unchanged data should produce the same:

* companies
* count
* order

unless the project explicitly specifies random sampling.

Sort results deterministically.

Recommended sort keys:

```text
company name
ticker
```

or another clearly defined project-specific ordering.

Do not rely on database row order.

---

# 30. TEST STRUCTURE

Create/update tests under:

```text
tests/
```

Recommended organization:

```text
tests/screener/
    test_config.py
    test_engine.py
    test_exceptions.py
    test_presets.py
    test_result_validation.py
```

Adapt to the project's existing test layout if one already exists.

---

# 31. UNIT TESTS — CONFIGURATION

Test:

### Valid config

* YAML loads successfully
* version exists
* preset definitions exist
* operators are valid

### Invalid config

* malformed YAML
* unknown metric
* invalid operator
* missing threshold
* invalid threshold type
* invalid preset structure

Every configuration error should be understandable.

---

# 32. UNIT TESTS — OPERATORS

Test every supported operator independently.

Example test matrix:

```text
5 > 3   → True
5 > 5   → False

5 >= 5  → True
5 >= 6  → False

5 < 6   → True
5 < 5   → False

5 <= 5  → True
5 <= 4  → False

5 == 5  → True
5 != 5  → False
```

Also test floating-point values where relevant.

---

# 33. UNIT TESTS — MISSING VALUES

Test:

```text
metric = NULL
```

against each relevant filter.

Expected behavior must follow the configured missing-value policy.

Also test:

```text
NaN
inf
-inf
invalid string
```

---

# 34. UNIT TESTS — D/E FINANCIAL EXCEPTION

Required scenarios:

```text
1. Non-financial + low D/E → pass
2. Non-financial + high D/E → fail
3. Financial + high D/E → D/E exception applied
4. Financial + missing D/E → verify configured policy
5. Sector label variation → verify mapping
```

Make the test prove that the exception comes from configuration rather than an accidental hard-coded branch.

---

# 35. UNIT TESTS — ICR

Required scenarios:

```text
EBIT = 100
Interest = 10
→ ICR = 10

Debt = 0
Interest = 0
→ debt-free policy applied

Debt = 0
Interest > 0
→ normal ICR behavior

Interest = 0
→ no division-by-zero crash

Missing interest
→ configured missing-value behavior

Invalid/negative interest
→ configured policy
```

The exact expected result must match the project's financial-definition convention.

---

# 36. INTEGRATION TEST — FULL ENGINE

Create a small deterministic fixture.

Example structure:

```text
Company A
Company B
Company C
Company D
...
```

Include:

* normal company
* financial company
* debt-free company
* company with high D/E
* company with high ICR
* company with zero interest
* company with missing metrics
* company that passes all conditions
* company that fails one condition

Run the complete engine against this fixture.

Verify:

```text
correct companies selected
correct filters applied
correct exceptions applied
correct count
no duplicates
```

---

# 37. PRESET TESTS

For each preset:

```text
run_preset("quality_compounder")
run_preset("value_pick")
run_preset("growth_accelerator")
run_preset("dividend_champion")
run_preset("debt_free_blue_chip")
run_preset("turnaround_watch")
```

Verify:

* preset exists
* preset loads from YAML
* all configured metrics exist
* result schema is valid
* result count is calculated
* no duplicate companies
* result is deterministic

---

# 38. PRESET COUNT VALIDATION

Run every preset against the project's intended dataset.

Create a test/report similar to:

```text
Quality Compounder      → XX
Value Pick              → XX
Growth Accelerator      → XX
Dividend Champion       → XX
Debt-Free Blue Chip     → XX
Turnaround Watch        → XX
```

Every result should satisfy:

```text
5 <= count <= 50
```

If a preset falls outside this range:

1. investigate the data,
2. verify filter logic,
3. verify metric mapping,
4. verify sector exception,
5. verify year-selection logic,
6. verify thresholds,
7. adjust YAML intentionally if the specification permits it.

Never modify the engine simply to force the count.

---

# 39. DATA QUALITY CHECK BEFORE BLAMING THE ENGINE

When a preset returns an unexpected number of companies, debug in this order:

```text
1. Is input data populated?
2. Are metric columns correct?
3. Are units correct?
4. Is the latest-year selection correct?
5. Are NULL values being handled correctly?
6. Is the operator correct?
7. Are thresholds correct?
8. Is the Financial D/E exception working?
9. Is ICR edge-case handling correct?
10. Is duplicate elimination correct?
```

This avoids changing correct filtering logic to compensate for upstream data problems.

---

# 40. LOGGING / DEBUG INFORMATION

Add useful debug information without making normal output noisy.

When debugging a preset, it should be possible to see:

```text
Preset
Input company count
Filter count
Companies removed by each filter
Exceptions applied
Final company count
```

A useful debug representation is:

```text
Input: 92

ROE >= X
Remaining: 70

ROCE >= Y
Remaining: 54

D/E <= Z
Remaining: 45

...
```

For production/default mode, avoid excessive logs.

---

# 41. FILTER TRACEABILITY

Whenever practical, make it possible to identify why a company failed.

For example:

```text
Company A
PASS: ROE
PASS: ROCE
FAIL: D/E
PASS: Growth
```

This can be implemented as optional debug/trace output rather than always returned in production.

This will make the screener much easier to verify and demonstrate.

---

# 42. PACKAGE STRUCTURE

Ensure the screener package is importable.

Potential structure:

```text
src/
    screener/
        __init__.py
        engine.py
        config.py       # only if useful/consistent with project
        exceptions.py   # only if useful
```

Do not create unnecessary files.

Follow the existing project's architecture.

---

# 43. DATABASE / DATAFRAME SAFETY

Do not modify source financial data while screening.

The screener should be read-only with respect to the source analytical dataset unless the architecture explicitly requires persistence.

Avoid:

```text
UPDATE source table
DELETE rows
```

The engine should produce a screening result, not mutate underlying financial data.

---

# 44. PERFORMANCE

The engine should process all relevant companies efficiently.

Avoid:

```text
for each company:
    run a new SQL query
```

when the dataset can reasonably be loaded once.

Prefer:

```text
load data once
→ normalize once
→ filter in memory
```

unless the project architecture specifically requires database-side filtering.

Do not prematurely optimize at the cost of readability.

---

# 45. DOCUMENTATION

Update relevant documentation, preferably the existing README/project docs.

Document:

* what Screener Engine does
* configuration file location
* supported operators
* 15 metric mapping
* missing-value behavior
* D/E financial exception
* ICR debt-free handling
* six preset screeners
* result-count requirement
* how to run screener tests
* how to add another preset

Include example commands using the project's actual command/test runner.

---

# 46. ACCEPTANCE CRITERIA — DAY 15

Day 15 is complete only when all of the following are true:

### Configuration

* `config/screener_config.yaml` exists
* all required screener settings are represented
* metric mappings are valid
* operators are validated
* exceptions are configurable

### Engine

* `src/screener/engine.py` exists
* generic filtering is implemented
* 15 metrics are supported
* multiple filters use the intended logical behavior
* missing values are handled
* invalid values are handled
* result duplicates are prevented
* results are deterministic

### Exceptions

* Financial-sector D/E exception works
* Debt-free ICR handling works
* zero-interest case does not crash
* missing-data behavior is explicit

### Tests

* operator tests pass
* configuration tests pass
* D/E exception tests pass
* ICR edge-case tests pass
* end-to-end screener test passes

---

# 47. ACCEPTANCE CRITERIA — DAY 16

Day 16 is complete only when:

### Presets

All six presets exist:

```text
quality_compounder
value_pick
growth_accelerator
dividend_champion
debt_free_blue_chip
turnaround_watch
```

### Implementation

* all presets use the common Screener Engine
* preset thresholds are configuration-driven
* no duplicated filtering engine exists for each preset
* each preset has tests
* each preset returns unique companies
* result count is validated

### Count

Each preset is verified against the project's intended dataset/fixture:

```text
5 <= result_count <= 50
```

Any violation is investigated instead of being hidden by automatic truncation or threshold relaxation.

---

# 48. DEFINITION OF DONE

The task is fully done when:

```text
Sprint 2 analytical outputs
        ↓
Screener config
        ↓
Generic filter engine
        ↓
Exception handling
        ↓
Six presets
        ↓
Automated tests
        ↓
Count validation
        ↓
Documentation
```

and the entire existing project test suite still passes.

---

# 49. REGRESSION SAFETY

Before declaring the task complete, run:

```text
all existing Sprint 1 tests
all existing Sprint 2 tests
all new Screener tests
```

The Screener implementation must NOT break:

* ETL
* database loading
* data-quality checks
* financial ratio calculations
* existing analytics

If a regression appears, identify whether it is caused by:

```text
import changes
schema changes
shared utility changes
data mutation
```

Fix the root cause rather than weakening tests.

---

# 50. CODING AGENT EXECUTION ORDER

Follow this exact order:

### Phase 1 — Repository understanding

1. Inspect project structure.
2. Read Sprint 1 and Sprint 2 implementation.
3. Identify data source for screener.
4. Identify exact 15 metrics.
5. Identify sector column and financial-sector values.
6. Identify debt and interest fields.
7. Identify existing testing framework.
8. Identify project command for running tests.

### Phase 2 — Configuration

9. Create `config/screener_config.yaml`.
10. Add metric mappings.
11. Add operators.
12. Add missing-value policy.
13. Add financial D/E exception.
14. Add ICR edge-case policy.
15. Add six preset definitions.
16. Add result-count constraints.

### Phase 3 — Engine

17. Implement config loading.
18. Implement config validation.
19. Implement metric resolution.
20. Implement generic operators.
21. Implement single-filter evaluation.
22. Implement multiple-filter evaluation.
23. Implement year/observation selection.
24. Implement Financial D/E exception.
25. Implement ICR debt-free handling.
26. Implement missing/invalid-value handling.
27. Implement result generation.
28. Implement deterministic sorting.
29. Implement result-count validation.
30. Add optional filter tracing/debugging.

### Phase 4 — Testing

31. Add configuration tests.
32. Add operator tests.
33. Add missing-value tests.
34. Add D/E exception tests.
35. Add ICR edge-case tests.
36. Add integration test.
37. Add preset tests.

### Phase 5 — Validation

38. Run the complete project test suite.
39. Run all six presets on the intended dataset.
40. Record result counts.
41. Investigate any count outside 5–50.
42. Verify no duplicate companies.
43. Verify deterministic output.
44. Verify Sprint 1–2 tests remain green.

### Phase 6 — Documentation

45. Document configuration.
46. Document exceptions.
47. Document preset usage.
48. Document how to create a new preset.
49. Document test commands.
50. Provide final implementation summary.

---

# 51. IMPORTANT CODING RULES

Follow these rules throughout implementation:

1. **Do not invent unavailable metrics.**
2. **Do not duplicate Sprint 2 financial formulas.**
3. **Do not hard-code preset thresholds inside Python.**
4. **Do not hard-code financial-sector exceptions when they can be configuration-driven.**
5. **Do not treat NULL as zero.**
6. **Do not silently ignore invalid configuration.**
7. **Do not automatically relax filters to achieve 5–50 results.**
8. **Do not arbitrarily truncate results to 50.**
9. **Do not mutate source financial data.**
10. **Do not break existing Sprint 1–2 functionality.**
11. **Prefer small, testable functions.**
12. **Use the project's existing coding style and dependencies.**
13. **Keep the engine independent from presentation/UI concerns.**
14. **Make behavior deterministic.**
15. **Document every non-obvious financial edge case.**

---

# 52. FINAL REPORT REQUIRED FROM THE CODING AGENT

At the end, return a concise implementation report containing:

```text
Files created
Files modified
15 metrics supported
Financial D/E exception behavior
ICR debt-free behavior
Six presets implemented
Test command(s)
Total tests passed
Preset result counts
Any assumptions made
Any unresolved issues
```

Also explicitly state:

```text
Sprint 3 Screener Engine: COMPLETE / NOT COMPLETE
```

Do not claim completion unless the acceptance criteria and tests have actually passed.
