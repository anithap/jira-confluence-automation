import argparse
import math


def main():
    parser = argparse.ArgumentParser(
        description="Calculate compound interest."
    )
    parser.add_argument("principal", type=float, help="starting principal")
    parser.add_argument(
        "annual_rate",
        type=float,
        help="annual interest rate as a percentage (for example, 7.34)",
    )
    parser.add_argument(
        "compounds_per_year",
        type=int,
        help="number of compounding periods per year",
    )
    parser.add_argument("years", type=float, help="total investment time in years")
    args = parser.parse_args()

    if not math.isfinite(args.principal) or args.principal < 0:
        parser.error("principal must be a finite, non-negative number")
    if not math.isfinite(args.annual_rate):
        parser.error("annual_rate must be a finite number")
    if args.compounds_per_year <= 0:
        parser.error("compounds_per_year must be a positive integer")
    if not math.isfinite(args.years) or args.years < 0:
        parser.error("years must be a finite, non-negative number")

    periodic_rate = args.annual_rate / 100 / args.compounds_per_year
    if periodic_rate <= -1:
        parser.error("annual_rate results in a periodic rate of -100% or less")

    try:
        amount = args.principal * (1 + periodic_rate) ** (
            args.compounds_per_year * args.years
        )
    except OverflowError:
        parser.error("the calculated amount is too large")

    interest = amount - args.principal
    print(f"Final amount: {amount:.2f}")
    print(f"Interest earned: {interest:.2f}")


if __name__ == "__main__":
    main()
