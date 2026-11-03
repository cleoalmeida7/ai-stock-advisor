# Evaluation Methodology (Planning Stage)

## Core constraint: no point-in-time fundamentals

Free data sources such as yfinance do not generally provide complete point-in-time histories of fundamental values as they were publicly known on each historical date (reporting period vs. publication date vs. retrieval date are easily conflated). This constraint must be preserved throughout the project and is why the evaluation approach is split in two:

### 1. Historical backtesting — price-based components only

Momentum, volatility, drawdown, and historical-return calculations can be backtested using time-valid historical price data, because the input (price history) genuinely was knowable at each historical date.

**This project must never claim that a fundamentals-based score has been historically validated using today's fundamentals applied retroactively.** Doing so would be look-ahead bias and would misrepresent the system's actual evidence.

### 2. Prospective evaluation — the full pipeline

Starting once the full analysis pipeline is operational (target: Week 6), every analysis run is logged with:

- Analysis timestamp and data-as-of timestamp.
- Full input snapshot and data source.
- Scoring engine version.
- Metric values and their individual contributions.
- AI-generated output (if any).
- Relevant benchmark observations.
- Subsequent price/portfolio outcomes, recorded later.

Evaluation of these logged runs must account for: look-ahead bias, survivorship bias, transaction costs, slippage, corporate actions, benchmark choice, missing observations, sample size, and market regime. Results must not be cherry-picked by period or security.

## Status

No analysis runs have been logged yet; this document will be revised with concrete methodology details as the evaluation engine (Week 9-10 target) is built.
