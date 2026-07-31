# Cameron Cooke
# Copyright © 2026

"""
This program utilizes Geometric Brownian Motion (GBM) to generate possible price
paths for a portfolio. Using Monte Carlo simulation, the program generates
numerous potential price paths by applying GBM calculation a specified number of
iterations. The results are then displayed in a graphical format.
"""

# import needed libraries
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time

TRADING_DAYS = 252
SIMULATIONS = 100000

"""
Check if number of positions is valid and then run simulation on portfolio.
"""
def main():
    positions, shares = get_portfolio()
    if (len(positions) < 1):
        print("No positions given")
    else:
        historical_price_data, spy_10y_data, rf, betas = retrieve_historical_data(positions)
        mu, sig, portfolio_paths = monte_carlo_simulation(
            positions, 
            shares, 
            historical_price_data, 
            spy_10y_data, 
            rf, 
            betas
            )
        portfolio_display(mu, sig, rf, positions, shares, portfolio_paths)
    

"""
Prompt user for positions in portfolio and number of shares of each position.
"""
def get_portfolio():
    positions = []
    shares = []
    # prompt user for ticker
    ticker = input('What Equity\'s price would you like to simulate? '
                    'or \'quit\' to stop: ').upper()
    while (ticker != "QUIT"):
        # prompt user for number of shares of equity
        share_count = float(input('How many Shares of this equity? '))

        # add ticker to positions and number of shares to shares
        positions.append(ticker)
        shares.append(share_count)
        
        # re-prompt user for next ticker
        ticker = input('What Equity\'s price would you like to simulate? '
                    'or \'quit\' to stop: ').upper()
        
    return positions, shares

"""
Manually calculates beta of each position in portfolio. Beta is calculated as
a weighted average across four periods (5y, 3y, 2y, and 1y). The most recent
period is weighted heaviest to account for recent price movements and current
market regime, while the longest period is weighted least, although still included,
to capture long-term trend, historical strength, and drift. The resulting weighted
beta is then adjusted toward the market average of 1 to account for mean reversion,
following the standard Bloomberg approach.
"""
def beta_calculation(positions, spy_historical_data):
    # retrieve historical price data of the positions
    historical_price_data = yf.download(
        positions,
        period="5y",
        auto_adjust=True
    )["Close"]
    historical_price_data["SPY"] = spy_historical_data

    # seperate price data into time periods
    beta_5y_data = historical_price_data
    beta_3y_data = historical_price_data[-(TRADING_DAYS * 3):]
    beta_2y_data = historical_price_data[-(TRADING_DAYS * 2):]
    beta_1y_data = historical_price_data[-TRADING_DAYS:]
    periods = [beta_5y_data, beta_3y_data, beta_2y_data, beta_1y_data]

    period_betas = []
    for i in range(0, 4):
        corr_matrix = correlation_calculation(periods[i])
        sig = volatility_calculation(periods[i])
        cov_matrix = corr_matrix * np.outer(sig, sig)
        period_betas.append(cov_matrix[-1, :-1] / cov_matrix[-1, -1])

    # array of weightings for different betas
    beta_weights = [0.1, 0.2, 0.3, 0.4]

    weighted_period_betas = []
    for i in range(0, 4):
        weighted_period_betas.append(period_betas[i] * beta_weights[i])
    
    weighted_betas = np.sum(weighted_period_betas, axis=0)

    betas_with_mean_reversion = ((2 / 3) * weighted_betas) + ((1 / 3) * 1)

    return betas_with_mean_reversion

"""
Retrieve all data needed.
"""
def retrieve_historical_data(positions):
    # use yf.download instead of yf.Ticker (for a single ticker) or yf.Tickers 
    # (for multiple tickers) due to being more efficient (uses multi-threading)

    # retrieve price data for all tickers/positions at one time
    historical_price_data = yf.download(
        positions,
        period="1y",
        auto_adjust=True
    )["Close"][positions]

    # retrieve 10y data needed for spy, save first and last value to get change
    spy_historical_data = yf.download(
        "SPY",
        period="1y",
        auto_adjust=True
    )["Close"]
    spy_10y_data = [spy_historical_data.iloc[0], spy_historical_data.iloc[-1]]

    # retrieve most recent risk free rate based on 10 year treasury note close
    rf = (yf.download("^TNX", period="5d", auto_adjust=True)["Close"].iloc[-1]) / 100
    rf = float(rf.iloc[0])

    betas = beta_calculation(positions, spy_historical_data)

    return historical_price_data, spy_10y_data, rf, betas

"""
Expected return is utilized in GBM to calculate the drift factor and is 
determined using the Capital Asset Pricing Model (CAPM) whose formula is:
mu = rf + ba * rp
Where:
mu = expected return
rf = risk free rate
ba = beta of equity
rp = equity risk premium
"""
def expected_return_calculation(spy_10y_data, rf, betas):
    ba = betas
    rm = ((spy_10y_data[1] / spy_10y_data[0]) ** (1 / 10)) - 1
    rp = (np.array(rm) - rf)
    mu = rf + (ba * rp)
    return mu

"""
Sigma is the standard deviation of the equity's returns and is utilized in GBM 
as the magnitude of the 'shocks'. Sigma is determined by taking the daily 
logarithmic returns of the equity. The formula for determining sigma is:
sig = daily_volatility * np.sqrt(252)
"""
def volatility_calculation(historical_price_data):
    logarithmic_returns = np.log(historical_price_data 
                                 / historical_price_data.shift(1))
    cleaned_returns = logarithmic_returns.dropna()
    daily_volatility = cleaned_returns.std()
    sig = daily_volatility * np.sqrt(TRADING_DAYS)
    return sig

"""
Correlation measures the degree to which two equities move in lock-step with one
another. Their correlation value can range from -1.0 (inversely correlated) to
1.0 (positively correlated). The correlation matrix is calculated by taking
logarithmic returns of each equity in the portfolio and computing the pairwise
correlation coefficients between all equity pairs.
"""
def correlation_calculation(historical_price_data):
    logarithmic_returns = np.log(historical_price_data 
                                 / historical_price_data.shift(1))
    cleaned_returns = logarithmic_returns.dropna()
    corr_matrix = np.array(cleaned_returns.corr())
    return corr_matrix

"""
This function calculates all needed inputs for GBM calculation.
"""
def gbm_inputs(historical_price_data, spy_10y_data, rf, betas):
    dt = 1 / TRADING_DAYS

    s = historical_price_data.iloc[-1, :]
    mu = np.asarray(expected_return_calculation(spy_10y_data, rf, betas))
    sig = np.asarray(volatility_calculation(historical_price_data))
    
    corr_matrix = correlation_calculation(historical_price_data)
    cov_matrix = np.outer(sig, sig) * corr_matrix
    l = np.linalg.cholesky(cov_matrix)
    return s, mu, sig, l, dt

"""
Geometric Brownian Motion (GBM) is calculated using the formula:
price = s * np.exp(((mu - (0.5 * (sig ** 2))) * dt) + (sig * np.sqrt(dt) * z))
Where: 
s = current price of equity
mu = expected return
sig = volatility
dt = time delta
correlated_z = correlated random shock
"""
def gbm_calculation(s, mu, sig, correlated_z, dt):
    # calculate possible future price(s)
    drift = (mu - (0.5 * (sig ** 2))) * dt
    diffusion = (sig * np.sqrt(dt) * correlated_z)
    next_prices = s * np.exp(drift + diffusion)

    return next_prices

"""
Monte Carlo Simulation performed running GBM calculation for each trading day
for a specified number of simulations. Each simulation uses the previous day's
price as the starting price. The price path generated for each equity is
adjusted to account for share counts and summed to get portfolio value for each 
simulated trading day.
"""
def monte_carlo_simulation(positions, shares, historical_price_data, spy_10y_data, rf, betas):
    s, mu, sig, l, dt = gbm_inputs(historical_price_data, spy_10y_data, rf, betas)
    price_paths = np.zeros((SIMULATIONS, TRADING_DAYS + 1, len(positions)))
    z = np.random.normal(size=(SIMULATIONS, TRADING_DAYS, len(positions)))
    correlated_z = z @ l.T
    price_paths[:, 0, :] = s

    for step in range(0, TRADING_DAYS):
        price_paths[:, step + 1, :] = gbm_calculation( 
            price_paths[:, step, :], 
            mu, 
            sig, 
            correlated_z[:, step, :], 
            dt
            )
        
    portfolio_paths = np.sum(price_paths * shares, axis=2)
    return mu, sig, portfolio_paths

"""
This function calculates the weighting of each position in the portfolio. The
weight of each position is determined by calculating the total value of that
position (price * shares) and then dividing by the total value of the portfolio.
"""
def portfolio_weighting_calculation(positions, shares, portfolio_paths):
    portfolio_value = portfolio_paths[0, 0]
    prices = np.array([])
    for index in range(0, len(positions)):
        prices = np.append(prices, 
                        yf.Ticker(positions[index]).history(period="1d")["Close"].iloc[-1])
    weights = (prices * shares) / portfolio_value
    return weights

"""
This function calculates the sharpe value of the portfolio. The sharpe value is
calculated by determining the sharpe of each equity position using:
sharpe = ((mu - rf) / sig)
where:
mu = expected return
rf = risk free rate
sig = volatility
The sharpe of each equity is then multiplied by its respective equity's weight
in the portfolio. The weighted sharpes are then summmed to get the portfolio sharpe.
"""
def sharpe_calculation(mu, sig, rf):
    sharpe = ((mu - rf) / sig)
    return sharpe

"""
This function calculates the downside deviation of returns. Downside deviation
of returns is the standard deviation of negative returns. Negative here defined 
as any return less than the daily risk free rate (rf / 252), therefore having a 
negative equity risk premium. This is done by taking all days where the log 
returns are less than the daily risk free returns and calculating their standard 
deviation.
"""
def downside_deviation_calculation(clean_returns, rf):
    rfDaily = rf/252
    downside_returns = (clean_returns - rfDaily).where(clean_returns < rfDaily, 0)
    downside_volatility = downside_returns.std()
    annualized_downside = downside_volatility * np.sqrt(TRADING_DAYS)
    return annualized_downside

"""
This function calculates the sortino value of the portfolio. The sortino value is
calculated by determining the sortino of each equity position using:
sortino = ((mu - rf) / downside_deviation)
where:
mu = expected return
rf = risk free rate
downside_deviation = standard deviation of negative returns
The sortino of each equity is then multiplied by its respective equity's weight
in the portfolio. The weighted sortinos are then summmed to get the portfolio sortino.
"""
def sortino_calculation(mu, clean_returns, rf):
    downside_deviations = downside_deviation_calculation(clean_returns, rf)
    sortino = (mu - rf) / downside_deviations
    return sortino

"""
This function calculates important metrics to be included in the final output. 
Here Value at Risk (VaR) and probability of loss are calculated. VaR (95%) 
represents the minimum loss expected in the worst 5% of simulated outcomes. 
Probability of loss is the percentage of simulations that resulted in a final 
portfolio value which was below the starting portfolio value, indicating an 
overall loss after the simulation.
"""
def portfolio_metrics(mu, sig, rf, positions, shares, portfolio_paths):
    portfolio_value_before_simulation = portfolio_paths[0, 0]
    final_prices = portfolio_paths[:, -1]
    mean_portfolio_path = pd.Series(np.mean(portfolio_paths, axis=0))
    mean_portfolio_value_after_simulation = mean_portfolio_path.iloc[-1]
    median_portfolio_value_after_simulation = np.median(final_prices)
    percent_change = ((mean_portfolio_value_after_simulation 
                      / portfolio_value_before_simulation) - 1) * 100
    logarithmic_returns = np.log(mean_portfolio_path / mean_portfolio_path.shift(1))
    cleaned_returns = logarithmic_returns.dropna()
    annualized_portfolio_return = cleaned_returns.mean() * TRADING_DAYS
    portfolio_volatility = cleaned_returns.std() * np.sqrt(TRADING_DAYS)
    value_at_risk = np.percentile(final_prices, 5)
    probability_of_loss = np.mean(final_prices < portfolio_value_before_simulation) * 100
    portfolio_sharpe = sharpe_calculation(annualized_portfolio_return, portfolio_volatility, rf)
    portfolio_sortino = sortino_calculation(annualized_portfolio_return, cleaned_returns, rf)
    return {
        'value_before': portfolio_value_before_simulation,
        'mean_value': mean_portfolio_value_after_simulation,
        'median_value': median_portfolio_value_after_simulation,
        'percent_change': percent_change,
        'volatility': portfolio_volatility,
        'return': annualized_portfolio_return,
        'value_at_risk': value_at_risk,
        'probability_of_loss': probability_of_loss,
        'sharpe': portfolio_sharpe,
        'sortino': portfolio_sortino
    }

"""
This function generates the graphical display of the portfolio and outputs
portfolio metrics to the terminal.
"""
def portfolio_display(mu, sig, rf, positions, shares, portfolio_paths):
    # calculate metrics to be displayed
    metrics = portfolio_metrics(mu, sig, rf, positions, shares, portfolio_paths)
    
    # output metrics to terminal
    print('\nPortfolio Results')
    print('----------------------------------')
    print('Starting Value: $%.2f' % (metrics['value_before']))
    print('Average Projected Value: $%.2f' % (metrics['mean_value']))
    print('Median Projected Value: $%.2f' % (metrics['median_value']))
    print('Percent Change: ' + 
          ('+%.2f%%' if metrics['percent_change'] > 0 else '-%.2f%%') 
          % (metrics['percent_change']))
    print('VaR (95%%): $%.2f (loss: $%.2f, %.2f%% downside)' 
          % (metrics['value_at_risk'], 
            (metrics['value_before'] - metrics['value_at_risk']),
            (((metrics['value_before'] - metrics['value_at_risk']) 
                / metrics['value_before']) * 100)))
    print('Probability of Loss: %.2f%%' % (metrics['probability_of_loss']))
    print('Sharpe Ratio: %.2f' % (metrics['sharpe']))
    print('Sortino Ratio: %.2f' % (metrics['sortino']))
    print('----------------------------------')

    # set up display for plotting side by side
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # left plot showing simulation of prices
    q1TimeSeries = np.zeros((1, TRADING_DAYS + 1))
    meanTimeSeries = np.zeros((1, TRADING_DAYS + 1))
    q3TimeSeries = np.zeros((1, TRADING_DAYS + 1))
    for step in range(0, TRADING_DAYS + 1):
        q1TimeSeries[0, step] = np.percentile(portfolio_paths[:, step], 25)
        meanTimeSeries[0, step] = np.mean(portfolio_paths[:, step])
        q3TimeSeries[0, step] = np.percentile(portfolio_paths[:, step], 75)
    for iteration in range(0, SIMULATIONS):
        axs[0].plot(portfolio_paths[iteration], alpha=0.5)
    axs[0].plot(q1TimeSeries[0], alpha=0.75, linestyle="dashed", 
                color="black", label="Q1")
    axs[0].plot(meanTimeSeries[0], alpha=0.75, 
                color="black", label="Mean")
    axs[0].plot(q3TimeSeries[0], alpha=0.75, linestyle="dashed", 
                color="black", label="Q3")
    axs[0].set_title("GBM Simulated Portfolio Price Paths")
    axs[0].set_xlabel("Time Step (Trading Day)")
    axs[0].set_ylabel("Portfolio Value ($)")

    axs[0].legend()

    # right plot showing distribution of prices
    final_prices = portfolio_paths[:, -1]
    sns.histplot(final_prices, ax=axs[1], bins = 100, 
                 kde=True, edgecolor = "black")
    axs[1].set_title("Distribution of Final Portfolio Values")
    axs[1].set_xlabel("Final Portfolio Value ($)")
    axs[1].set_ylabel("Frequency")
    axs[1].axvline(portfolio_paths[0, 0], color="#001F5B", 
                   linestyle="dashed", linewidth=1.5, 
                   label="Initial Portfolio Value")
    axs[1].axvline(metrics['value_at_risk'], color="black", 
                   linewidth=1.5, label="VaR (5%%) Loss: $%.2f" 
                   % ((metrics['value_before'] - metrics['value_at_risk'])))

    axs[1].legend()

    end = time.time()
    print("Runtime: %.2f seconds" % (end - start))
    
    plt.tight_layout()
    plt.show()

start = time.time()
if __name__=="__main__":
    main()
    
