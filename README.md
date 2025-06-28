# Stock Market Analyzer

A FastAPI server for analyzing stock market data using the Alpha Vantage API.

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
```

## Environment Variables

| Variable                | Description                | Required |
| ----------------------- | -------------------------- | -------- |
| `ALPHA_VANTAGE_API_KEY` | Your Alpha Vantage API key | Yes      |

## Notes

- The free Alpha Vantage API has rate limits (5 API calls per minute, 500 per day)
- For production use, consider upgrading to a paid plan
- Configure CORS settings properly for production deployments
