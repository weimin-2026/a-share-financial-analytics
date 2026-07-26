# Project Report: A-Share Financial Analytics and Backtesting Platform

## Background

Financial markets produce a large amount of time-series data. A stock has an opening price, closing price, high price, low price, and trading volume for every trading day. These values can be organized, visualized, and used to test simple rules. However, a chart or a successful historical test does not prove that a strategy will work in the future. This project therefore combines technical work with clear risk explanations.

## Motivation

I wanted to build a project that connects Python programming with a real-world subject. Finance is interesting because it includes data collection, mathematics, visualization, decision rules, uncertainty, and ethics. The project is designed for learning and university application demonstrations. It is not a trading product, and it never asks for a brokerage password or sends a real order.

## Objectives

The first objective is to collect and clean public daily data for ten well-known A-share companies. The second is to explain moving averages and the Relative Strength Index through code and charts. The third is to create a basic backtest without look-ahead bias. The fourth is to demonstrate a simple time-ordered machine-learning workflow. The final objective is to provide a paper-trading simulation that makes the safety boundary visible.

## Technology Stack

Python is the main language. Streamlit provides the interactive website without requiring a separate JavaScript frontend. pandas and NumPy handle tables and calculations. Plotly creates interactive charts. AKShare provides access to public market data. scikit-learn supplies linear regression and the mean absolute error metric. pytest checks the core rules with fixed offline data, and Ruff checks formatting and code quality.

## Data Collection

The default stock pool contains ten A-share codes and Chinese company names. The data module requests daily history from AKShare with forward-adjusted prices. It renames Chinese source columns to stable English names, converts dates and numeric values, removes invalid rows and duplicate dates, and sorts the result in ascending order.

Data reliability is important. An online request can fail because of network restrictions, a changed source field, or a temporary server problem. The application therefore saves successful results as local CSV files. On a later failure it attempts to read the cache. If both sources fail, the page displays the real error. It does not silently invent prices. A failure for one company also does not have to stop all other companies from loading.

The latest-market module is treated differently from history. It is a public snapshot that may be delayed. The page displays the retrieval time and a delay warning. An unfinished current-day snapshot is not added to the backtest.

## Moving Average and RSI

A simple moving average is the arithmetic mean of recent closing prices. A short moving average reacts faster than a long moving average. The project defines a golden cross when the short average changes from below the long average to above it, and a death cross for the opposite change.

RSI compares average upward and downward price changes over a window. The implementation handles division by zero: a continuously rising window becomes 100, while a completely unchanged window becomes 50. Results are limited to the range from zero to one hundred. The common 30 and 70 levels are shown only as educational reference lines.

## Backtesting

The backtest is deliberately small and explainable. It is long-only, so it never shorts a stock or borrows money. A golden cross can open a position, and a death cross can close it. By default, a purchase uses fifty percent of available cash. The share quantity is rounded down to a multiple of one hundred. Both purchases and sales pay a simplified one-sided fee.

For every trading day, the program records cash, shares, and total equity. It also calculates total return, annualized return, maximum drawdown, trade count, final equity, and buy-and-hold return. The website plots the strategy and buy-and-hold curves together. This comparison helps prevent a misleading conclusion: a positive strategy return can still be worse than simply holding the stock.

## Avoiding Look-Ahead Bias

Look-ahead bias is one of the most important lessons in this project. A moving-average cross using day t's closing price is only known after that close. A realistic historical simulation cannot use the same day's close as if the signal had been known earlier. The code shifts the signal by one row and executes at the opening price of trading day t+1. Unit tests confirm the date relationship. This small delay makes the result less convenient but more honest.

## Trend Reference

The trend page uses linear regression, the simplest supervised-learning model in the project. The only feature is the sequential trading-day number, and the target is the closing price. Data is never randomly shuffled. The earlier eighty percent forms the training set, and the later twenty percent forms the test set. Mean absolute error reports the average size of the test error in price units.

The fitted line is extended for ten steps to demonstrate the idea of extrapolation. It is labeled as a trend reference rather than a forecast. Markets are affected by company results, policy, liquidity, news, and human behavior, so one straight line cannot reliably predict them.

## Paper Trading

The paper-trading account exists only in Streamlit session state. It stores simulated cash, positions, trades, and processed signal identifiers. An identifier combines the stock code, signal date, and side so the same signal is not processed twice. Every order contains `is_paper_trade=True`. There is no registration system, database, scheduler, brokerage connection, or real-order API.

## Limitations

The model simplifies real markets. It does not fully represent slippage, bid-ask spreads, price limits, suspension, liquidity impact, dividends, every tax, or survivorship bias. A fixed stock pool can introduce selection bias. The MA parameters were not proven to be optimal, and optimizing them repeatedly could create overfitting. The public data provider may change its interface. Streamlit Community Cloud may sleep or restrict network access.

## Risk Disclaimer

Historical performance does not guarantee future returns. The trading module is a paper-trading simulation only. The trend model is an educational reference rather than an investment forecast. The application does not provide recommendations, target prices, or promised returns.

## Learning Reflection

This project taught me that financial programming is not only about formulas. Data validation, error messages, reproducible tests, and honest assumptions are equally important. I learned why time order matters, how a small implementation choice can create look-ahead bias, and why a model metric must be explained with limitations. I also learned to separate page code from calculation functions so that important rules can be tested without a browser or network.

## Future Improvements

Future work could add corporate-action checks, trading-calendar validation, more detailed cost assumptions, portfolio-level analysis, and downloadable experiment settings. These improvements should remain explainable and should not turn the learning platform into a real trading system.
