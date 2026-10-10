#!/usr/bin/env python3
"""Real estate pro forma model with levered return metrics.

Canonical runnable implementation of the RealEstateProForma model documented in
references/financial-metrics.md. Builds a year-by-year cash flow projection
(GPR -> vacancy -> EGI -> OpEx -> NOI -> debt service -> net cash flow), models
the exit sale, and computes IRR, equity multiple, NPV, cap rate, CoC, and DSCR.

Conventions:
- Expenses: the Year-1 OpEx base equals Year-1 EGI times ``opex_ratio``; from
  Year 2 on it escalates at ``expense_growth`` only (it is not re-derived from
  grown revenue).
- Debt: monthly amortization, as lenders quote it. Annual debt service is 12
  monthly payments; balances are after year x 12 payments. ltv 0 means an
  all-cash purchase.
- Cash invested at Year 0: down payment + closing_costs + upfront_capex (both
  optional, default 0). Closing costs typically run 2-5% of price; leaving
  them out overstates every return.

Example invocation (the plugin's MCP venv has numpy and numpy-financial):
    PY=${CLAUDE_PLUGIN_ROOT}/mcp-servers/real-estate-data/.venv/bin/python
    $PY pro_forma.py --sample-input > inputs.json
    $PY pro_forma.py --input inputs.json --table
    $PY pro_forma.py --input inputs.json --output results.json

Requirements: numpy, numpy-financial
"""

import argparse
import json
import sys

import numpy_financial as npf

SAMPLE_INPUT = {
    "property": {
        "purchase_price": 5000000,
        "units": 50,
        "annual_rent_per_unit": 12000,
        "other_income_pct": 0.03,
        "vacancy_rate": 0.05,
        "opex_ratio": 0.40,
        "closing_costs": 100000,
        "upfront_capex": 0,
    },
    "loan": {
        "ltv": 0.75,
        "interest_rate": 0.05,
        "amortization_years": 30,
    },
    "assumptions": {
        "holding_period": 10,
        "rent_growth": 0.03,
        "expense_growth": 0.025,
        "capex_pct": 0.05,
        "exit_cap_rate": 0.065,
        "selling_costs_pct": 0.03,
    },
}


class RealEstateProForma:
    """Complete real estate pro forma model.

    Parameters
    ----------
    property_params : dict
        purchase_price, other_income_pct, vacancy_rate, opex_ratio, and either
        (units and annual_rent_per_unit) or annual_gross_rent. Optional:
        closing_costs and upfront_capex (dollars paid at acquisition).
    loan_params : dict
        ltv, interest_rate (annual), amortization_years.
    assumptions : dict
        holding_period, rent_growth, expense_growth, capex_pct,
        exit_cap_rate, selling_costs_pct.
    """

    def __init__(self, property_params, loan_params, assumptions):
        self.property_params = property_params
        self.loan_params = loan_params
        self.assumptions = assumptions

        self.loan_amount = property_params["purchase_price"] * loan_params["ltv"]
        self.down_payment = property_params["purchase_price"] - self.loan_amount
        self.closing_costs = property_params.get("closing_costs", 0) or 0
        self.upfront_capex = property_params.get("upfront_capex", 0) or 0
        # Total cash in at Year 0, the base for CoC, IRR and equity multiple.
        self.equity_investment = self.down_payment + self.closing_costs + self.upfront_capex

        if "annual_gross_rent" in property_params:
            self.base_rent = property_params["annual_gross_rent"]
        else:
            self.base_rent = (
                property_params["annual_rent_per_unit"] * property_params["units"]
            )

        self.rows = []  # one dict per year, 0..holding_period
        self.build_pro_forma()

    # ------------------------------------------------------------------ core

    def _monthly_payment(self):
        """Monthly P&I as npf returns it (a negative outflow)."""
        if self.loan_amount <= 0:
            return 0.0
        return npf.pmt(
            self.loan_params["interest_rate"] / 12,
            self.loan_params["amortization_years"] * 12,
            self.loan_amount,
        )

    def annual_debt_service(self):
        """Annual P&I: 12 monthly payments (positive number)."""
        return -12 * self._monthly_payment()

    def calculate_loan_balance(self, year):
        """Remaining loan balance after `year` x 12 monthly payments."""
        if self.loan_amount <= 0:
            return 0.0
        return -npf.fv(
            self.loan_params["interest_rate"] / 12,
            year * 12,
            self._monthly_payment(),
            self.loan_amount,
        )

    def build_pro_forma(self):
        years = self.assumptions["holding_period"]
        debt_service = self.annual_debt_service()

        # Year-1 OpEx base: opex_ratio applies to Year-1 EGI only, then the
        # base grows at expense_growth — independent of rent growth
        egi_year1 = (
            self.base_rent
            * (1 + self.property_params["other_income_pct"])
            * (1 - self.property_params["vacancy_rate"])
        )
        opex_base = egi_year1 * self.property_params["opex_ratio"]

        # Year 0: acquisition
        self.rows = [{"year": 0, "total_cash_flow": -self.equity_investment}]

        for year in range(1, years + 1):
            growth_factor = (1 + self.assumptions["rent_growth"]) ** (year - 1)
            gross_potential_rent = self.base_rent * growth_factor
            other_income = gross_potential_rent * self.property_params["other_income_pct"]
            potential_gross_income = gross_potential_rent + other_income
            vacancy = potential_gross_income * self.property_params["vacancy_rate"]
            effective_gross_income = potential_gross_income - vacancy

            operating_expenses = opex_base * (
                (1 + self.assumptions["expense_growth"]) ** (year - 1)
            )
            noi = effective_gross_income - operating_expenses

            cash_flow_before_capex = noi - debt_service
            capex_reserves = effective_gross_income * self.assumptions["capex_pct"]
            net_cash_flow = cash_flow_before_capex - capex_reserves

            self.rows.append(
                {
                    "year": year,
                    "gross_potential_rent": gross_potential_rent,
                    "other_income": other_income,
                    "potential_gross_income": potential_gross_income,
                    "vacancy_credit_loss": vacancy,
                    "effective_gross_income": effective_gross_income,
                    "operating_expenses": operating_expenses,
                    "net_operating_income": noi,
                    "debt_service": debt_service,
                    "cash_flow_before_capex": cash_flow_before_capex,
                    "capex_reserves": capex_reserves,
                    "net_cash_flow": net_cash_flow,
                    "remaining_loan_balance": self.calculate_loan_balance(year),
                    "total_cash_flow": net_cash_flow,
                }
            )

        # Exit/sale in final year
        final = self.rows[years]
        exit_value = final["net_operating_income"] / self.assumptions["exit_cap_rate"]
        selling_costs = exit_value * self.assumptions["selling_costs_pct"]
        remaining_balance = final["remaining_loan_balance"]
        net_sale_proceeds = exit_value - selling_costs - remaining_balance

        final["property_sale_value"] = exit_value
        final["selling_costs"] = selling_costs
        final["net_sale_proceeds"] = net_sale_proceeds
        final["total_cash_flow"] = final["net_cash_flow"] + net_sale_proceeds

    # --------------------------------------------------------------- outputs

    def cash_flows(self):
        """Equity cash flow vector: index 0 = acquisition, 1..N = annual."""
        return [row["total_cash_flow"] for row in self.rows]

    def calculate_metrics(self):
        cash_flows = self.cash_flows()
        irr = npf.irr(cash_flows)
        total_distributions = sum(cash_flows[1:])
        equity_multiple = total_distributions / abs(cash_flows[0])

        year1 = self.rows[1]
        return {
            "purchase_price": self.property_params["purchase_price"],
            "equity_investment": self.equity_investment,
            "down_payment": self.down_payment,
            "closing_costs": self.closing_costs,
            "upfront_capex": self.upfront_capex,
            "loan_amount": self.loan_amount,
            "ltv": self.loan_params["ltv"],
            "purchase_cap_rate": year1["net_operating_income"]
            / self.property_params["purchase_price"],
            "year_1_noi": year1["net_operating_income"],
            "year_1_cash_flow": year1["net_cash_flow"],
            "year_1_cash_on_cash": year1["net_cash_flow"] / self.equity_investment,
            "year_1_dscr": (year1["net_operating_income"] / year1["debt_service"]
                            if year1["debt_service"] else None),
            "irr": float(irr),
            "equity_multiple": equity_multiple,
            "npv_8": float(npf.npv(0.08, cash_flows)),
            "npv_10": float(npf.npv(0.10, cash_flows)),
            "npv_12": float(npf.npv(0.12, cash_flows)),
            "exit_cap_rate": self.assumptions["exit_cap_rate"],
        }

    def to_dict(self):
        return {
            "inputs": {
                "property": self.property_params,
                "loan": self.loan_params,
                "assumptions": self.assumptions,
            },
            "metrics": self.calculate_metrics(),
            "pro_forma": self.rows,
        }

    def display_summary(self, out=sys.stdout):
        m = self.calculate_metrics()
        w = out.write
        w("=" * 78 + "\n")
        w("REAL ESTATE PRO FORMA SUMMARY\n")
        w("=" * 78 + "\n\n")
        w(f"Purchase Price:           ${m['purchase_price']:>15,.0f}\n")
        w(f"Loan Amount (LTV {m['ltv']:.1%}):  ${m['loan_amount']:>15,.0f}\n")
        w(f"Cash Invested:            ${m['equity_investment']:>15,.0f}\n")
        w(f"  down payment {m['down_payment']:,.0f} + closing {m['closing_costs']:,.0f}"
          f" + upfront capex {m['upfront_capex']:,.0f}\n\n")
        w(f"Purchase Cap Rate:        {m['purchase_cap_rate']:>15.2%}\n")
        w(f"Year 1 Cash-on-Cash:      {m['year_1_cash_on_cash']:>15.2%}\n")
        if m["year_1_dscr"] is None:
            w(f"Year 1 DSCR:              {'n/a (no loan)':>15}\n\n")
        else:
            w(f"Year 1 DSCR:              {m['year_1_dscr']:>15.2f}x\n\n")
        w(f"Levered IRR:              {m['irr']:>15.2%}\n")
        w(f"Equity Multiple:          {m['equity_multiple']:>15.2f}x\n\n")
        w(f"NPV @ 8%:                 ${m['npv_8']:>15,.0f}\n")
        w(f"NPV @ 10%:                ${m['npv_10']:>15,.0f}\n")
        w(f"NPV @ 12%:                ${m['npv_12']:>15,.0f}\n\n")

        w("YEAR-BY-YEAR CASH FLOWS\n")
        w("-" * 78 + "\n")
        header = (
            f"{'Yr':>3} {'EGI':>13} {'OpEx':>12} {'NOI':>13} "
            f"{'Debt Svc':>12} {'Net CF':>12} {'Total CF':>13}\n"
        )
        w(header)
        for row in self.rows:
            if row["year"] == 0:
                w(f"{0:>3} {'':>13} {'':>12} {'':>13} {'':>12} {'':>12} "
                  f"{row['total_cash_flow']:>13,.0f}\n")
                continue
            w(
                f"{row['year']:>3} {row['effective_gross_income']:>13,.0f} "
                f"{row['operating_expenses']:>12,.0f} "
                f"{row['net_operating_income']:>13,.0f} "
                f"{row['debt_service']:>12,.0f} {row['net_cash_flow']:>12,.0f} "
                f"{row['total_cash_flow']:>13,.0f}\n"
            )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Real estate pro forma model (JSON in / JSON or table out)."
    )
    parser.add_argument(
        "--input",
        help="Path to JSON input file with property/loan/assumptions keys "
        "(use '-' for stdin)",
    )
    parser.add_argument("--output", help="Write full results JSON to this path")
    parser.add_argument(
        "--table",
        action="store_true",
        help="Print a human-readable summary table instead of JSON",
    )
    parser.add_argument(
        "--sample-input",
        action="store_true",
        help="Print a sample input JSON document and exit",
    )
    args = parser.parse_args(argv)

    if args.sample_input:
        json.dump(SAMPLE_INPUT, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not args.input:
        parser.error("--input is required (or use --sample-input)")

    if args.input == "-":
        params = json.load(sys.stdin)
    else:
        with open(args.input) as f:
            params = json.load(f)

    model = RealEstateProForma(
        params["property"], params["loan"], params["assumptions"]
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(model.to_dict(), f, indent=2)
        sys.stderr.write(f"Wrote results to {args.output}\n")

    if args.table:
        model.display_summary()
    elif not args.output:
        json.dump(model.to_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
