from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import requests
from dotenv import load_dotenv
from typing import Optional
from analysis import analyse_risk, calculate_risk_reward

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Stock Market Analyzer",
    description="A FastAPI server for analyzing stock market data using Alpha Vantage API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment variable
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Stock Market Analyzer API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "api_key_configured": bool(ALPHA_VANTAGE_API_KEY)}


@app.get("/stock/{symbol}")
async def get_stock_data(symbol: str, function: str = "TIME_SERIES_DAILY"):
    """
    Get stock data for a given symbol

    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        function: Alpha Vantage function (default: TIME_SERIES_DAILY)
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY environment variable."
        )

    try:
        params = {
            "function": function,
            "symbol": symbol.upper(),
            "apikey": ALPHA_VANTAGE_API_KEY
        }

        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise HTTPException(status_code=400, detail=data["Error Message"])

        if "Note" in data:
            raise HTTPException(
                status_code=429, detail="API rate limit exceeded")

        return data

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/search/{keywords}")
async def search_stocks(keywords: str):
    """
    Search for stocks by keywords

    Args:
        keywords: Search keywords
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY environment variable."
        )

    try:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": ALPHA_VANTAGE_API_KEY
        }

        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if "Error Message" in data:
            raise HTTPException(status_code=400, detail=data["Error Message"])

        if "Note" in data:
            raise HTTPException(
                status_code=429, detail="API rate limit exceeded")

        return data

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching stocks: {str(e)}")


@app.get("/plot/risk/{symbol}", response_class=HTMLResponse)
async def plot_risk_analysis(symbol: str, target_selling_price: float, stop_loss: float, user_volume: float):
    """
    Analyse risk for a given stock with target selling price and stop loss

    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        target_selling_price: Target price to sell the stock
        stop_loss: Stop loss price to limit losses
        user_volume: Number of shares the user is buying
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY environment variable."
        )

    try:
        # Get stock data first
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol.upper(),
            "apikey": ALPHA_VANTAGE_API_KEY
        }

        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise HTTPException(status_code=400, detail=data["Error Message"])

        if "Note" in data:
            raise HTTPException(
                status_code=429, detail="API rate limit exceeded")

        # Perform risk analysis
        risk_analysis = analyse_risk(
            data, target_selling_price, stop_loss, user_volume)

        if "error" in risk_analysis:
            return f"""
            <html>
                <body>
                    <h1>Error</h1>
                    <p>{risk_analysis['error']}</p>
                </body>
            </html>
            """

        # Create HTML response with the plot
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Risk Analysis for {risk_analysis['symbol']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .plot {{ text-align: center; margin: 20px 0; }}
                .plot img {{ max-width: 100%; height: auto; }}
                .data {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .data h3 {{ margin-top: 0; }}
                .data table {{ width: 100%; border-collapse: collapse; }}
                .data td, .data th {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                .risk-level {{ font-weight: bold; padding: 5px 10px; border-radius: 4px; }}
                .risk-high {{ background: #ffebee; color: #c62828; }}
                .risk-medium {{ background: #fff3e0; color: #ef6c00; }}
                .risk-low {{ background: #e8f5e8; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Risk Analysis for {risk_analysis['symbol']}</h1>
                
                <div class="data">
                    <h3>Trade Parameters</h3>
                    <table>
                        <tr><td>Current Price:</td><td>${risk_analysis['current_price']:.2f}</td></tr>
                        <tr><td>Target Selling Price:</td><td>${risk_analysis['target_selling_price']:.2f}</td></tr>
                        <tr><td>Stop Loss:</td><td>${risk_analysis['stop_loss']:.2f}</td></tr>
                        <tr><td>User Volume:</td><td>{risk_analysis['user_volume']:,} shares</td></tr>
                        <tr><td>Recent Average Volume:</td><td>{risk_analysis['recent_avg_volume']:,.0f} shares</td></tr>
                        <tr><td>Volume Impact:</td><td>{risk_analysis['volume_impact']:.1%}</td></tr>
                    </table>
                </div>
                
                <div class="data">
                    <h3>Risk Analysis</h3>
                    <table>
                        <tr><td>Volatility:</td><td>{risk_analysis['risk_analysis']['volatility']:.2%}</td></tr>
                        <tr><td>Drawdown Risk:</td><td>{risk_analysis['risk_analysis']['drawdown_risk']:.2%}</td></tr>
                        <tr><td>Liquidity Risk:</td><td>{risk_analysis['risk_analysis']['liquidity_risk']:.2%}</td></tr>
                        <tr><td>Bearish Frequency:</td><td>{risk_analysis['risk_analysis']['bearish_frequency']:.2%}</td></tr>
                        <tr><td>Overall Risk Level:</td><td><span class="risk-level risk-{risk_analysis['risk_analysis']['risk_level'].lower()}">{risk_analysis['risk_analysis']['risk_level']}</span></td></tr>
                    </table>
                </div>
                
                <div class="plot">
                    <h3>Risk Profile Radar Chart</h3>
                    <img src="data:image/png;base64,{risk_analysis['plot']}" alt="Risk Profile Chart">
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/plot/risk-reward/{symbol}", response_class=HTMLResponse)
async def plot_risk_reward_analysis(
    symbol: str,
    target_price: float,
    stop_loss: float,
    user_volume: float,
    holding_period_days: int = 30,
    risk_free_rate: float = 0.04
):
    """
    Comprehensive risk/reward analysis for a given stock

    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        target_price: Target selling price
        stop_loss: Stop loss price
        user_volume: Number of shares the user is buying
        holding_period_days: Investment horizon in days (default: 30)
        risk_free_rate: Annual risk-free rate (default: 0.04 = 4%)
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY environment variable."
        )

    try:
        # Get stock data first
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol.upper(),
            "apikey": ALPHA_VANTAGE_API_KEY
        }

        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            raise HTTPException(status_code=400, detail=data["Error Message"])

        if "Note" in data:
            raise HTTPException(
                status_code=429, detail="API rate limit exceeded")

        # Perform comprehensive risk/reward analysis
        analysis_result = calculate_risk_reward(
            data, target_price, stop_loss, user_volume, holding_period_days, risk_free_rate
        )

        if "error" in analysis_result:
            return f"""
            <html>
                <body>
                    <h1>Error</h1>
                    <p>{analysis_result['error']}</p>
                </body>
            </html>
            """

        # Create HTML response with the comprehensive analysis
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Risk/Reward Analysis for {analysis_result['symbol']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .plot {{ text-align: center; margin: 20px 0; }}
                .plot img {{ max-width: 100%; height: auto; }}
                .data {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .data h3 {{ margin-top: 0; }}
                .data table {{ width: 100%; border-collapse: collapse; }}
                .data td, .data th {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                .risk-level {{ font-weight: bold; padding: 5px 10px; border-radius: 4px; }}
                .risk-high {{ background: #ffebee; color: #c62828; }}
                .risk-medium {{ background: #fff3e0; color: #ef6c00; }}
                .risk-low {{ background: #e8f5e8; color: #2e7d32; }}
                .rating {{ font-size: 18px; font-weight: bold; padding: 10px; border-radius: 8px; text-align: center; margin: 10px 0; }}
                .rating-excellent {{ background: #e8f5e8; color: #2e7d32; }}
                .rating-good {{ background: #e3f2fd; color: #1565c0; }}
                .rating-fair {{ background: #fff3e0; color: #ef6c00; }}
                .rating-weak {{ background: #ffebee; color: #c62828; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Risk/Reward Analysis for {analysis_result['symbol']}</h1>
                
                <div class="data">
                    <h3>Trade Parameters</h3>
                    <table>
                        <tr><td>Current Price:</td><td>${analysis_result['current_price']:.2f}</td></tr>
                        <tr><td>Target Price:</td><td>${target_price:.2f}</td></tr>
                        <tr><td>Stop Loss:</td><td>${stop_loss:.2f}</td></tr>
                        <tr><td>User Volume:</td><td>{user_volume:,} shares</td></tr>
                        <tr><td>Holding Period:</td><td>{holding_period_days} days</td></tr>
                        <tr><td>Risk-Free Rate:</td><td>{risk_free_rate:.1%}</td></tr>
                        <tr><td>Recent Average Volume:</td><td>{analysis_result['recent_avg_volume']:,.0f} shares</td></tr>
                        <tr><td>Volume Impact:</td><td>{analysis_result['volume_impact']:.1%}</td></tr>
                    </table>
                </div>
                
                <div class="data">
                    <h3>Risk Analysis</h3>
                    <table>
                        <tr><td>Volatility:</td><td>{analysis_result['risk_analysis']['volatility']:.2%}</td></tr>
                        <tr><td>Drawdown Risk:</td><td>{analysis_result['risk_analysis']['drawdown_risk']:.2%}</td></tr>
                        <tr><td>Liquidity Risk:</td><td>{analysis_result['risk_analysis']['liquidity_risk']:.2%}</td></tr>
                        <tr><td>Bearish Frequency:</td><td>{analysis_result['risk_analysis']['bearish_frequency']:.2%}</td></tr>
                        <tr><td>Overall Risk Level:</td><td><span class="risk-level risk-{analysis_result['risk_analysis']['risk_level'].lower()}">{analysis_result['risk_analysis']['risk_level']}</span></td></tr>
                    </table>
                </div>
                
                <div class="data">
                    <h3>Reward Analysis</h3>
                    <table>
                        <tr><td>Sharpe Ratio:</td><td>{analysis_result['reward_analysis']['sharpe_ratio']:.3f}</td></tr>
                        <tr><td>Annualized Return:</td><td>{analysis_result['reward_analysis']['annualized_return_pct']:.2f}%</td></tr>
                        <tr><td>Risk/Reward Ratio:</td><td>{analysis_result['reward_analysis']['risk_reward_ratio']:.3f}</td></tr>
                        <tr><td>Success Probability:</td><td>{analysis_result['reward_analysis']['success_probability']:.1%}</td></tr>
                    </table>
                </div>
                
                <div class="rating rating-{analysis_result['reward_analysis']['rating'].split()[0].lower()}">
                    {analysis_result['reward_analysis']['rating']}
                </div>
                
                <div class="plot">
                    <h3>Risk Profile Radar Chart</h3>
                    <img src="data:image/png;base64,{analysis_result['plot']}" alt="Risk Profile Chart">
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
