# Stock Market Analyzer

A FastAPI server for analyzing stock market data using the Alpha Vantage API with comprehensive risk and reward analysis.

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory with your Alpha Vantage API key:

   ```
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

   Get your free API key from: https://www.alphavantage.co/support/#api-key

3. **Run the server:**

   ```bash
   python main.py
   ```

   Or using uvicorn directly:

   ```bash
   uvicorn main:app --reload
   ```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check

- **GET** `/health` - Check if the API is running and if the API key is configured

### Stock Data

- **GET** `/stock/{symbol}` - Get daily stock data for a given symbol
  - Parameters:
    - `symbol` (required): Stock symbol (e.g., AAPL, MSFT)
    - `function` (optional): Alpha Vantage function (default: TIME_SERIES_DAILY)

### Stock Search

- **GET** `/search/{keywords}` - Search for stocks by keywords
  - Parameters:
    - `keywords` (required): Search keywords

### Risk Analysis

- **GET** `/plot/risk/{symbol}` - Generate risk analysis with radar chart visualization
  - Parameters:
    - `symbol` (required): Stock symbol (e.g., AAPL, MSFT)
    - `target_selling_price` (required): Target price to sell the stock
    - `stop_loss` (required): Stop loss price to limit losses
    - `user_volume` (required): Number of shares the user is buying

### Comprehensive Risk/Reward Analysis

- **GET** `/plot/risk-reward/{symbol}` - Generate comprehensive risk/reward analysis with ratings
  - Parameters:
    - `symbol` (required): Stock symbol (e.g., AAPL, MSFT)
    - `target_price` (required): Target selling price
    - `stop_loss` (required): Stop loss price
    - `user_volume` (required): Number of shares the user is buying
    - `holding_period_days` (optional): Investment horizon in days (default: 30)
    - `risk_free_rate` (optional): Annual risk-free rate (default: 0.04 = 4%)

## API Documentation

Once the server is running, you can access:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Example Usage

```bash
# Get stock data for Apple
curl "http://localhost:8000/stock/AAPL"

# Search for stocks containing "apple"
curl "http://localhost:8000/search/apple"

# Check health status
curl "http://localhost:8000/health"

# Risk analysis for Apple
curl "http://localhost:8000/plot/risk/AAPL?target_selling_price=205&user_volume=50&stop_loss=198"

# Comprehensive risk/reward analysis for Apple
curl "http://localhost:8000/plot/risk-reward/AAPL?target_price=205&stop_loss=198&user_volume=50&holding_period_days=30&risk_free_rate=0.04"
```

## Features

### Risk Analysis

- **Volatility Risk**: Annualized volatility calculation
- **Drawdown Risk**: Potential loss from current price to stop loss
- **Liquidity Risk**: Volume analysis and user volume impact
- **Bearish Pressure**: RSI-based bearish frequency analysis
- **Visual Radar Chart**: Interactive risk profile visualization

### Risk/Reward Analysis

- **Sharpe Ratio**: Risk-adjusted return calculation
- **Risk/Reward Ratio**: Probability-adjusted risk/reward metrics
- **Success Probability**: Monte Carlo simulation for trade success
- **Star Rating System**: Overall trade quality assessment
- **Comprehensive HTML Reports**: Detailed analysis with visualizations

## Environment Variables

| Variable                | Description                | Required |
| ----------------------- | -------------------------- | -------- |
| `ALPHA_VANTAGE_API_KEY` | Your Alpha Vantage API key | Yes      |

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Chart generation
- **NumPy**: Numerical computations
- **Requests**: HTTP client
- **Python-dotenv**: Environment variable management

## Notes

- The free Alpha Vantage API has rate limits (5 API calls per minute, 500 per day)
- For production use, consider upgrading to a paid plan
- Configure CORS settings properly for production deployments
- Risk analysis includes Monte Carlo simulations for probability calculations
- All endpoints return HTML responses for better visualization in tools like Postman
