"""
Small analytical demo on top of InfluxDB 3 Core, showing the kind of
analysis the database enables. Produces two figures in outputs/figures/.

Run from the project root:
    python src/analysis.py
"""

from pathlib import Path

import matplotlib.pyplot as plt

from queries import get_client, query_all_joined

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def plot_series_overview(wide):
    """all 3 series and each normalized to 100 at the first observation for easy comparison of growth rates"""
    normalized = wide.divide(wide.iloc[0]).multiply(100)

    plt.figure(figsize=(10, 5))
    for col in normalized.columns:
        plt.plot(normalized.index, normalized[col], label=col)
    plt.title("FRED Series Indexed to 100 at 2000-01-01")
    plt.xlabel("Date")
    plt.ylabel("Index (Jan 2000 = 100)")
    plt.legend()
    plt.tight_layout()
    out = FIGURES_DIR / "01_series_overview.png"
    plt.savefig(out, dpi=150)
    plt.close()



def plot_case_shiller_with_ma(wide):
    """Case-Shiller w a 12 month moving average."""
    cs = wide["case_shiller"].dropna()
    ma = cs.rolling(12).mean()

    plt.figure(figsize=(10, 5))
    plt.plot(cs.index, cs, label="Case-Shiller", alpha=0.7)
    plt.plot(ma.index, ma, label="12-month moving average", linewidth=2)
    plt.title("Case-Shiller National Home Price Index")
    plt.xlabel("Date")
    plt.ylabel("Index value")
    plt.legend()
    plt.tight_layout()
    out = FIGURES_DIR / "02_example_analysis.png"
    plt.savefig(out, dpi=150)
    plt.close()



def main():
    with get_client() as client:
        wide = query_all_joined(client)

    print(f"pulled wide frame shape = {wide.shape}")
    plot_series_overview(wide)
    plot_case_shiller_with_ma(wide)


if __name__ == "__main__":
    main()