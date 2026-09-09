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
data = yf.download("AAPL", period="1y")
data.columns = data.columns.get_level_values(0)
```

`yfinance` returns OHLC data with MultiIndex columns (e.g. `('Close', 'AAPL')`) even for a single ticker; this flattens them to plain column names (`Close`, `High`, `Low`, `Open`, `Volume`).

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

## Usage

```bash
pip install yfinance pandas numpy matplotlib scipy
python historical_vol.py
```

```python
from historical_vol import calculate_all_volatilities, Mode
import yfinance as yf

data = yf.download("AAPL", period="1y")
data.columns = data.columns.get_level_values(0)

point_estimates = calculate_all_volatilities(data, mode=Mode.VALS)
print(point_estimates)
```

## Known gaps / TODO

- `black_scholes_call` is defined in this file but not currently used anywhere — either wire it in (e.g. to compare realized vs. implied volatility) or remove it.
- The `results` dict from `Mode.VALS` should be printed or logged in `__main__` — currently computed but discarded.
- No comparison yet against actual implied volatility for the same stock/period — natural next step, bridging into an IV smile/skew project.
- `plt.show()` is used for interactive display; `plt.savefig(...)` is present but commented out — decide whether you want a saved PNG artifact (useful for a CV/GitHub README) in addition to, or instead of, the interactive window.

## Background

Historical volatility is backward-looking — it tells you what a stock's price actually did, not what the market expects it to do next (that's implied volatility, computed from option prices instead of stock prices). Volatility trading desks compare the two: if realized volatility consistently comes in below what was implied when a position was entered, option sellers profit; if it comes in above, option buyers profit.
