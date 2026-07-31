# GBM Portfolio Simulator

Monte Carlo portfolio simulator using Geometric Brownian Motion with correlated random shocks and live market data for generating potential future portfolio values and modeling risk.

---

## Project Synopsis

This program simulates potential future values of an equity portfolio using Geometric Brownian Motion and Monte Carlo simulation. Live market data is pulled from Yahoo Finance via the yfinance library and used to compute expected returns, historical volatility, and correlations between asset pairs. The simulation generates 10,000 price paths for the portfolio and outputs a graphical display of the data along with relevant metrics including VaR, Sharpe ratio, Sortino ratio, and probability of loss.

---

## Technical Approach

### Monte Carlo Simulation

#### What is Monte Carlo Simulation?

Monte Carlo simulation is a way to model the probability of different outcomes for a process whose outcome cannot be easily predicted due to the inclusion of random variables. Monte Carlo simulation is used to understand the impact of risk and uncertainty and in investing can be used to model the range of future prices of an asset. 

#### Monte Carlo Simulation Used in This Project

In this project, Monte Carlo simulation is being used to estimate thousands of possible future values of an equity portfolio. The underlying process modeled in this program is Geometric Brownian Motion. Utilizing a Monte Carlo simulation allows investors to better grasp the range of possible outcomes and their relative likelihood. This also allows for the estimation of the probability of loss, and quantifying downside risk via metrics like Value at Risk.

### Geometric Brownian Motion

#### What is Geometric Brownian Motion?

Geometric Brownian Motion (GBM) is a stochastic process used to model the evolution of an asset's price. The process originated from Brownian Motion, a concept from physics that was observed through the random movement of pollen particles in water. The "Geometric" extension came later to modify the process for the modeling of asset prices, ensuring they stay positive and grow multiplicatively. GBM assumes that asset prices follow a log-normal distribution, and therefore logarithmic returns are normally distributed. GBM is the foundation of many financial models including Black-Scholes option pricing.

#### Geometric Brownian Motion as a Concept

Geometric Brownian Motion is best understood through analogy. Consider a leaf floating down a river. Its movement is determined by two forces, the current of the river which pushes the leaf in a general direction (drift), and the deviations caused by branches, rocks, other objects in the water, and wind (random shocks). The prices of equities behave in the same manner. Expected return acts as the drift, providing a constant directional pull, while market randomness introduces volatility at each time step. GBM captures these two forces and uses them to realistically simulate asset price behavior.

Geometric Brownian Motion models price evolution with this formula:

$$S_{t+1} = S_t \cdot \exp\left(\left(\mu - \frac{1}{2}\sigma^2\right)\Delta t + \sigma\sqrt{\Delta t} \cdot Z_t\right)$$

Where:
- $S_t$ = current price of equity
- $\mu$ = expected return
- $\sigma$ = volatility
- $\Delta t$ = time step
- $Z_t$ = random shock from a normal distribution

#### Geometric Brownian Motion Used in This Project

Here, Geometric Brownian Motion is applied at each time step for every equity in the portfolio to simulate what the price would be the next day. The current price of the equity is the starting point from which the model then applies the GBM formula 252 times, once per trading day, to generate a price path for each equity with a one year time horizon. The individual paths are then aggregated based on position size in the portfolio to create the path of the portfolio value. This process is repeated for each Monte Carlo simulation to produce thousands of possible price paths for the portfolio, capturing a range of possible outcomes.

### Expected Return Using the Capital Asset Pricing Model (CAPM)

#### What is the Capital Asset Pricing Model?

The Capital Asset Pricing Model (CAPM) is a financial model used to estimate the expected return of an investment based on its riskiness relative to the overall market. This is done by measuring the asset's systematic risk. Systematic risk is the market risk that cannot be diversified away, quantified by the asset's beta coefficient. 

CAPM estimates expected return with this formula:

$$\mu = R_f + \beta \cdot (R_m - R_f)$$

Where:
- $\mu$ = Expected return of the investment
- $R_f$ = Risk free rate
- $\beta$ = Beta
- $R_m$ = Expected return of the market
- $(R_m - R_f)$ = Equity Risk Premium

#### CAPM Used in This Project

In the context of this project, CAPM is used to determine the expected return for each equity within the portfolio. These expected returns serve as the drift factor inputs for the GBM calculation to determine the price of the equities at the next time step. For the risk free rate, the current yield of the 10 year treasury note (^TNX) is used. To determine the expected return of the market, the 10 year compound annual growth rate (CAGR) is used. Due to the 10 year CAGR not being adjusted for inflation, all growth estimates are nominal and not real returns.

### Historical Volatility Using Log Returns

#### Why Use Log Returns?

Volatility is measured as the standard deviation of daily returns, which is then annualized. Instead of simple daily returns, this project utilizes log returns for two reasons: 

- The issues created by the multiplicative nature of equity returns
- The asymmetric and skewed nature of simple returns

Equity returns are inherently multiplicative because they compound over time. For example, if a stock gains 10% on day one and falls 10% on day two, the equity does not return to its initial price from day zero. Taking the natural log of these returns converts them from being multiplicative to additive. This means the log return of day one plus the log return of day two gives the log return for the two day period and makes calculations cleaner. 

Simple returns are asymmetric and skewed in nature due to stock prices being unable to fall below zero, capping losses at -100%, although gains can be theoretically infinite. Transforming the returns logarithmically eliminates the skew and maps the returns symmetrically so the data fits a normal distribution.

#### Volatility Used in This Project

Here, volatility serves as the magnitude of the random shocks when determining the price of the equity at the next time step. To compute this, daily historical closing prices over the last year are taken and the daily log returns are calculated. The standard deviation of those returns is then taken and annualized to determine the volatility of the equity.

### Correlated Random Shocks

#### Why is Correlating Random Shocks Necessary?

When simulating a multi-asset portfolio, the relationships between assets needs to be accounted for. For example, AAPL and NVDA are more likely to move together than AAPL and XOM. Ignoring correlations between equities, consequently treating their random shocks as independent, improperly estimates price paths and creates illusions of diversification when not present in the portfolio. Adding equity correlations to the random shocks used in GBM takes 3 main steps:

- Calculating the correlations between asset pairs
- Converting correlation matrix to covariance matrix
- Applying Cholesky decomposition to generate correlated random shocks

Correlation is the measure of the degree to which two assets move in relation to one another. The correlation matrix is created by computing daily log returns for each equity and calculating the correlation coefficient of each asset pair. These correlation values can range from -1.0 (inversely correlated) to 1.0 (positively correlated).

The covariance matrix is then generated by capturing how much two assets move together by accounting for their individual volatilities and their correlation. An equity with high volatility that is highly correlated to another equity will have a large covariance with that equity, whereas uncorrelated equities will have a covariance near zero. The covariance matrix is simply the correlation matrix scaled by the volatilities of each asset pair.

The final step then uses Cholesky decomposition which takes the covariance matrix and produces a lower triangular matrix of weights. These weights are then applied to an array of independent random shocks through matrix multiplication. Assets with high covariance end up with shocks that tend to move in the same direction as the equities they are correlated with, while assets that have low covariance are assigned shocks that are largely independent from the others. Through this process an array of correlated random shocks is generated that mirrors how the assets in the portfolio move together.

---

## Graphical Output and Metrics

Upon execution, the program generates a two-part breakdown of the simulation results:

- A visual display detailing portfolio price paths and distribution of final portfolio values
- A summary of relevant portfolio metrics displayed in the console

### Example Output

Portfolio specified for results:
- Tickers: NVDA, WMT, NEE, LLY, JPM
- Shares: [1, 1, 1, 1, 1]
- Simulation horizon: 252 trading days
- Number of simulations: 10,000

![Portfolio Simulation Output](https://github.com/camerone-cooke/GBM-Portfolio-Simulator/blob/main/GBM_Portfolio_Simulator_Output.png)

Output to console:
- Starting Value: $1795.53
- Average Projected Value: $1962.11
- Median Projected Value: $1949.62
- Percent Change: +9.28%
- VaR (95%): $1708.19 (Loss: $87.34, 4.68% Downside)
- Probability of Loss: 16.13%
- Sharpe Ratio: 0.30
- Sortino Ratio: 0.42

### Understanding Output

Graphical Output:
- Left plot: A time-series chart exhibiting all 10,000 projected portfolio trajectories over the 252 day horizon. The price paths that exemplify the Mean, 1st Quartile, and 3rd Quartile are also shown in black.
- Right plot: A histogram bucketing the frequency of the final portfolio values. The initial portfolio value displayed as a blue dotted line and the VaR displayed as a solid black line.

Output to console:
- Value at Risk (VaR): The minimum expected loss at a specified confidence level (95%)
- Probability of Loss: The proportion of the 10,000 simulated paths that ended at a final value lower than the initial value, indicating the likelihood of a loss
- Sharpe Ratio: Measures the portfolio's risk-adjusted return by calculating excess return per unit of risk
- Sortino Ratio: Measures the portfolio's risk-adjusted return relative to specifically harmful risk by calculating excess return per unit of downside risk

---

## Key Features

- Historical Data: Live market data is fetched dynamically via the yfinance library, automating data collection for simulation.
- Cholesky Decomposition: Cholesky decomposition is applied to a historical covariance matrix, mirroring the influence of asset pair correlations by influencing random shocks.
- Risk Assessment: Portfolio risk is assessed by calculating Value at Risk, Probability of Loss, and risk-adjusted return ratios (Sharpe and Sortino).

---

## Tech Stack & Libraries

- Language: Python 3.12.5
- Libraries
  * `yfinance` - For dynamically fetching historical market data and asset information
  * `numpy` - For operations on multi-dimension arrays to generate random walks
  * `pandas` - For aligning time series data on multiple assets
  * `matplotlib` & `seaborn` - For data visualization of price paths and final portfolio value histogram
 
---

## How to Run

Install Dependencies:
```bash
pip install yfinance numpy pandas matplotlib seaborn time
```

Run Script:
```bash
# For Mac or Linux
python3 GBM_Simulation.py

# For Windows
python GBM_Simulation.py
```

Enter Equity Positions:
```text
What Equity's price would you like to simulate? or 'quit' to stop: AAPL
How many Shares of this equity? 5
What Equity's price would you like to simulate? or 'quit' to stop: MSFT
How many Shares of this equity? 9
What Equity's price would you like to simulate? or 'quit' to stop: NVDA
How many Shares of this equity? 2
What Equity's price would you like to simulate? or 'quit' to stop: quit
```

---

## Skills Demonstrated

This project demonstrates:
- Quantitative Development: Translated an advanced mathematical model into Python
- Stochastic Modeling: Utilized Geometric Brownian Motion to determine potential values of a multi-asset portfolio
- Monte Carlo Simulation: Executed 10,000 iterations to generate range of possible portfolio price paths
- Correlation Application: Used matrix decomposition to mirror the influence of asset pair correlations
- Risk Analysis: Evaluated risk by calculating Value at Risk (VaR), Probability of Loss, and risk-adjusted return ratios (Sharpe and Sortino)




