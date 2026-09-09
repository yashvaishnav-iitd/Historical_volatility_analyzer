# Historical Volatility Estimators

A Python tool that pulls real daily stock data (via `yfinance`) and computes historical (realized) volatility four different ways — Close-to-Close, Parkinson, Garman-Klass, and Yang-Zhang — then plots how each estimator evolves over time on a rolling window.

## Why more than one estimator?

The simplest way to measure volatility (Close-to-Close) only uses closing prices, discarding the intraday high/low and the opening price entirely. That's wasted information. The other three estimators progressively use more of each day's OHLC (Open/High/Low/Close) data to converge faster and more precisely on the "true" volatility, using fewer days of history:

- **Close-to-Close** — the standard deviation of daily log returns, annualized. Simple, but noisy and only uses the close.
- **Parkinson** — uses the day's High and Low. More statistically efficient than Close-to-Close, but assumes no overnight gaps and no drift.
- **Garman-Klass** — uses Open, High, Low, and Close. More efficient again, but still assumes zero drift and doesn't separately handle overnight jumps.
- **Yang-Zhang** — combines an overnight (Close-to-Open) variance term, an Open-to-Close variance term, and a Rogers-Satchell drift-independent term. Handles overnight gaps explicitly and is considered the most robust of the four for real markets, where stocks often jump between yesterday's close and today's open (e.g. on overnight news).

## Files

| File | Purpose |
|---|---|
| `historical_vol.py` | Downloads data, computes all four estimators, and plots rolling volatility |

## How it works

### 1. Data download

```python
ticker = input("Enter ticker symbol (e.g. AAPL, MSFT, TSLA): ").strip().upper()
data = yf.download(ticker, period="1y")

if data.empty:
    raise ValueError(f"No data found for ticker '{ticker}' — check the symbol is correct.")

data.columns = data.columns.get_level_values(0)
```

The script works for **any ticker**, not just one hardcoded symbol — it prompts for a ticker at runtime. `yfinance` returns OHLC data with MultiIndex columns (e.g. `('Close', 'AAPL')`) even for a single ticker; the last line flattens them to plain column names (`Close`, `High`, `Low`, `Open`, `Volume`).

If the ticker is invalid or has no data, `yf.download` doesn't raise an error on its own — it silently returns an empty table, which would otherwise let `NaN` values propagate through every downstream calculation with no clear explanation. The `if data.empty` check catches this immediately with a clear error message instead.

### 2. The four estimators (`calculate_all_volatilities`)

All returns are computed as **log returns** (`ln(price_t / price_t-1)`), consistent with the Black-Scholes assumption that log-returns, not raw price changes, are normally distributed.

- **Close-to-Close:** `std(log_returns) * sqrt(252)`
- **Parkinson:** built from `(ln(High/Low))² / (4·ln2)` per day, averaged and annualized
- **Garman-Klass:** built from `0.5·(ln(H/L))² − (2·ln2−1)·(ln(C/O))²` per day
- **Yang-Zhang:** `overnight_variance + k·open_to_close_variance + (1−k)·rogers_satchell_variance`, where `k` is a weighting factor that depends on the sample size, and Rogers-Satchell (`ln(H/O)·ln(H/C) + ln(L/O)·ln(L/C)`) captures intraday range independent of any drift.

252 is used as the annualization factor throughout (the standard approximate number of trading days in a year).

The function supports two modes via an `Enum`:
- `Mode.VALS` — one number per estimator, computed over the entire downloaded period
- `Mode.PLOTS` — a rolling estimate (default 30-day window) for each estimator, producing a full time series suitable for plotting

### 3. Visualization (`plot_rolling_estimators`)

Plots all four rolling estimators on the same chart, so you can see where they agree, where they diverge, and how reactive each one is to short-term price swings.

## Verification

Formulas were validated against **synthetic OHLC data with a known, simulated true volatility** — something real market data can't provide, since the "true" volatility of a real stock is never actually known. Generating 2,000 days of data from a process with a known annualized volatility of 31.75% and running it through all four estimators recovered values within ~1–3 percentage points across the board, confirming the formulas (including the more error-prone Yang-Zhang and Rogers-Satchell terms) are implemented correctly.

The generalized (ticker-agnostic) version was separately verified by running the full pipeline against two synthetic datasets with different volatility levels (a low-vol and a high-vol case), confirming that output filenames, plot titles, and console output all correctly reflect whichever ticker is passed in, rather than being hardcoded to a single stock.

## Usage

```bash
pip install yfinance pandas numpy matplotlib scipy
python historical_vol.py
```

Running it prompts for a ticker symbol, then prints the four full-period volatility estimates and saves a rolling comparison plot named `{TICKER}_estimator_comparison.png`:

```
Enter ticker symbol (e.g. AAPL, MSFT, TSLA): msft

=== MSFT 1-Year Volatility Estimator Comparison ===
Close-to-Close : 0.2103 (21.03%)
Parkinson      : 0.1897 (18.97%)
Garman-Klass   : 0.1842 (18.42%)
Yang-Zhang     : 0.1961 (19.61%)
```

To use the functions directly rather than via the interactive prompt:

```python
from historical_vol import calculate_all_volatilities, plot_rolling_estimators, Mode
import yfinance as yf

ticker = "TSLA"
data = yf.download(ticker, period="1y")
data.columns = data.columns.get_level_values(0)

point_estimates = calculate_all_volatilities(data, mode=Mode.VALS)
print(point_estimates)

plot_rolling_estimators(data, ticker)
```

## Known gaps / TODO

- No comparison yet against actual implied volatility for the same stock/period — natural next step, bridging into an IV smile/skew project.
- `plt.show()` and `plt.savefig(...)` are both active — the plot is saved as `{TICKER}_estimator_comparison.png` and also displayed interactively. Comment out `plt.show()` if running this non-interactively (e.g. in a script or notebook pipeline).

## Background

Historical volatility is backward-looking — it tells you what a stock's price actually did, not what the market expects it to do next (that's implied volatility, computed from option prices instead of stock prices). Volatility trading desks compare the two: if realized volatility consistently comes in below what was implied when a position was entered, option sellers profit; if it comes in above, option buyers profit.
