# Compound Interest Instructions

## When to use

Use `tools/compound_interest.py` when the user asks to calculate compound
interest or the final balance for a principal, annual interest rate,
compounding frequency, and duration. Do not use it for simple-interest
calculations.

## Invocation

Run the script from the workspace root with four positional arguments:

```powershell
python tools\compound_interest.py <principal> <annual_rate_percent> <compounds_per_year> <years>
```

- `principal`: starting amount; must be non-negative.
- `annual_rate_percent`: annual rate as a percentage, such as `7.34` for 7.34%.
- `compounds_per_year`: positive integer, such as `12` for monthly compounding.
- `years`: duration in years; fractions are accepted. Convert months to a
  fraction of a year (for example, 8 years and 7 months is `8 + 7/12`).

If the rate is supplied as a decimal fraction, convert it to a percentage
before passing it (for example, `0.0734` becomes `7.34`). If the user omitted
any required input, request it rather than guessing.

## Presenting results

Report both values printed by the script: **Final amount** and **Interest
earned**, rounded to two decimal places. Include the principal, annual rate,
compounding frequency, and duration used so the result can be checked. Use a
currency symbol only when the user specifies the currency; otherwise retain
the script's plain numeric output. If the script reports an invalid input or
calculation error, explain it and ask for corrected inputs instead of
presenting a result.
