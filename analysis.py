from typing import Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv
from io import BytesIO
import base64

# Load environment variables
load_dotenv()


def analyse_risk(stock_data: Dict[str, Any], target_selling_price: float, stop_loss: float, user_volume: float) -> Dict[str, Any]:
    """
    Analyse risk for a given stock based on target selling price, stop loss, and user's buying volume.

    Args:
        stock_data: Stock data from Alpha Vantage API
        target_selling_price: Target price to sell the stock
        stop_loss: Stop loss price to limit losses
        user_volume: Number of shares the user is buying (affects liquidity risk)

    Returns:
        Dictionary containing risk analysis results and plot
    """
    try:
        # Extract time series data
        time_series = stock_data.get("Time Series (Daily)", {})
        if not time_series:
            return {"error": "No time series data available"}

        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index(ascending=True)  # Ensure chronological order

        # Get latest price and convert columns to float
        current_price = float(df['4. close'].iloc[-1])
        closes = df['4. close'].astype(float)
        volumes = df['5. volume'].astype(float)

        # Calculate daily returns
        daily_returns = closes.pct_change().dropna()

        # 1. Volatility Risk (Annualized)
        volatility = daily_returns.std() * np.sqrt(252)
        norm_volatility = min(volatility / 0.5, 1.0)  # Cap at 50% annual vol

        # 2. Drawdown Risk
        drawdown = (current_price - stop_loss) / current_price
        norm_drawdown = min(drawdown / 0.3, 1.0)  # Cap at 30% drawdown

        # 3. Liquidity Risk (Volume vs Historical + User Volume Impact)
        avg_volume = volumes.mean()
        recent_volume = volumes[-20:].mean()

        # Calculate base liquidity risk
        liquidity_risk = 1 - (recent_volume / avg_volume)

        # Adjust for user volume if provided
        if user_volume is not None:
            # Calculate what percentage of recent volume the user's order represents
            user_volume_pct = user_volume / recent_volume
            # Increase liquidity risk if user's volume is significant (>5% of recent volume)
            if user_volume_pct > 0.05:
                # Scale risk up proportionally
                liquidity_risk *= (1 + user_volume_pct)

        norm_liquidity = min(liquidity_risk / 0.7, 1.0)  # Cap at 70% below avg

        # 4. Bearish Pressure (RSI < 30 frequency)
        delta = closes.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()

        # Calculate RS and RSI (with NaN handling)
        avg_loss_safe = np.where(avg_loss == 0, np.nan, avg_loss)
        rs = avg_gain / avg_loss_safe
        rsi = 100 - (100 / (1 + rs))

        # Calculate bearish frequency safely
        if isinstance(rsi, pd.Series):
            bearish_freq = (rsi < 30).mean()
        else:
            bearish_freq = 0.0

        norm_bearish = min(bearish_freq / 0.3, 1.0)  # Cap at 30% frequency

        # Create radar plot
        fig = plt.figure(figsize=(10, 6))

        categories = ['Volatility', 'Drawdown', 'Liquidity', 'Bearishness']
        values = [norm_volatility, norm_drawdown, norm_liquidity, norm_bearish]

        # Repeat first value to close the circle
        values += values[:1]
        angles = np.linspace(0, 2*np.pi, len(categories),
                             endpoint=False).tolist()
        angles += angles[:1]

        ax = fig.add_subplot(111, polar=True)
        ax.plot(angles, values, linewidth=2,
                linestyle='solid', label='Risk Components')
        ax.fill(angles, values, alpha=0.25)

        # Draw axis lines
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'])

        # Title and annotations
        symbol = stock_data.get("Meta Data", {}).get("2. Symbol", "Unknown")
        title = f'Risk Profile for {symbol}\nCurrent: ${current_price:.2f} | Target: ${target_selling_price:.2f} | Stop: ${stop_loss:.2f}'
        if user_volume:
            title += f'\nUser Volume: {user_volume:,} shares ({user_volume/recent_volume:.1%} of recent volume)'
        plt.title(title, pad=20)

        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return {
            "symbol": symbol,
            "current_price": current_price,
            "target_selling_price": target_selling_price,
            "stop_loss": stop_loss,
            "user_volume": user_volume,
            "recent_avg_volume": recent_volume,
            "volume_impact": user_volume/recent_volume if user_volume else None,
            "risk_analysis": {
                "volatility": float(volatility),
                "drawdown_risk": float(drawdown),
                "liquidity_risk": float(liquidity_risk),
                "bearish_frequency": float(bearish_freq),
                "risk_level": "HIGH" if (norm_volatility + norm_drawdown + norm_liquidity + norm_bearish) / 4 > 0.7
                              else "MEDIUM" if (norm_volatility + norm_drawdown + norm_liquidity + norm_bearish) / 4 > 0.4
                              else "LOW"
            },
            "plot": img_base64
        }

    except Exception as e:
        print(f"Error in risk analysis: {str(e)}")
        return {"error": f"Error in risk analysis: {str(e)}"}


def get_rating(sharpe: float, rr_ratio: float) -> str:
    """Determine overall trade quality"""
    if sharpe > 1.5 and rr_ratio > 2.0:
        return "⭐️⭐️⭐️⭐️⭐️ EXCELLENT"
    elif sharpe > 1.0 and rr_ratio > 1.5:
        return "⭐️⭐️⭐️⭐️ GOOD"
    elif sharpe > 0.5 and rr_ratio > 1.0:
        return "⭐️⭐️⭐️ FAIR"
    else:
        return "⭐️⭐️ WEAK"


def estimate_success_probability(
    stock_data: Dict[str, Any],
    entry_price: float,
    target_price: float,
    stop_loss: float,
    n_simulations: int = 1000,
    lookback_days: int = 60
) -> float:
    """
    Estimate probability of hitting target before stop loss
    using Monte Carlo simulation based on recent price movements
    """
    # Extract closing prices from stock data
    time_series = stock_data.get("Time Series (Daily)", {})
    if not time_series:
        return 0.5  # Default if insufficient data

    # Convert to DataFrame and extract closing prices
    df = pd.DataFrame.from_dict(time_series, orient='index')
    closes = df['4. close'].astype(float).sort_index(ascending=True)

    recent_returns = closes.pct_change().dropna()[-lookback_days:]

    if len(recent_returns) < 5:
        return 0.5  # Default if insufficient data

    hits_target = 0

    for _ in range(n_simulations):
        # Generate random walk using historical returns
        random_returns = np.random.choice(
            recent_returns, size=30)  # 30-day simulation
        price_path = entry_price * (1 + random_returns).cumprod()

        if price_path.max() >= target_price:
            hits_target += 1
        elif price_path.min() <= stop_loss:
            continue
        else:
            # Count as success if above entry price at end
            hits_target += 1 if price_path[-1] > entry_price else 0

    return hits_target / n_simulations


def calculate_risk_reward(
    stock_data: Dict[str, Any],
    target_price: float,
    stop_loss: float,
    user_volume: float,
    holding_period_days: int = 30,
    risk_free_rate: float = 0.04  # Fallback: 4%
) -> Dict[str, Any]:
    """
    Comprehensive risk/reward analysis combining both metrics.

    Args:
        stock_data: Alpha Vantage stock data
        target_price: Target selling price
        stop_loss: Stop loss price
        user_volume: Number of shares
        holding_period_days: Investment horizon
        risk_free_rate: Annual risk-free rate

    Returns:
        Combined analysis with Sharpe and Risk/Reward ratios
    """
    # Calculate risk metrics
    risk_result = analyse_risk(
        stock_data, target_price, stop_loss, user_volume)
    if "error" in risk_result:
        return risk_result

    # Extract needed values
    current_price = risk_result["current_price"]
    volatility = risk_result["risk_analysis"]["volatility"]

    # Calculate reward metrics
    potential_return_pct = (target_price / current_price - 1)
    annualized_return = potential_return_pct * (252 / holding_period_days)

    # Sharpe Ratio (using risk analysis volatility)
    sharpe_ratio = (annualized_return - risk_free_rate) / volatility

    # Risk/Reward Ratio (probability-adjusted)
    success_prob = estimate_success_probability(
        stock_data,
        current_price,
        target_price,
        stop_loss
    )
    risk_reward_ratio = (success_prob * potential_return_pct) / (
        (1 - success_prob) * abs((stop_loss / current_price - 1))
    )

    # Combine results
    return {
        **risk_result,
        "reward_analysis": {
            "sharpe_ratio": sharpe_ratio,
            "annualized_return_pct": annualized_return * 100,
            "risk_reward_ratio": risk_reward_ratio,
            "success_probability": success_prob,
            "rating": get_rating(sharpe_ratio, risk_reward_ratio)
        }
    }
