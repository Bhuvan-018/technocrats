/*
  # Stock Market Prediction System Schema

  ## Overview
  Creates tables for storing stock companies and historical price data for the prediction dashboard.

  ## New Tables
  
  ### `companies`
  - `ticker` (text, primary key) - Stock ticker symbol (e.g., "RELIANCE", "TCS")
  - `name` (text) - Full company name
  - `created_at` (timestamptz) - Record creation timestamp
  
  ### `historical_prices`
  - `id` (uuid, primary key) - Unique identifier
  - `ticker` (text) - Foreign key to companies
  - `timestamp` (timestamptz) - Price timestamp in IST
  - `open` (numeric) - Opening price
  - `high` (numeric) - High price
  - `low` (numeric) - Low price
  - `close` (numeric) - Closing price
  - `volume` (bigint) - Trading volume
  - `created_at` (timestamptz) - Record creation timestamp
  
  ### `prediction_analytics`
  - `id` (uuid, primary key) - Unique identifier
  - `ticker` (text) - Foreign key to companies
  - `date` (date) - Prediction date
  - `predicted_close` (numeric) - Predicted closing price
  - `actual_close` (numeric) - Actual closing price (null until known)
  - `error` (numeric) - Prediction error (null until actual known)
  - `horizon` (text) - Time horizon (10m, 30m, 1h)
  - `created_at` (timestamptz) - Record creation timestamp

  ## Security
  - All tables have RLS enabled
  - Public read access for all tables (dashboard is public-facing)
  - No write access through policies (data managed server-side)

  ## Indexes
  - Index on historical_prices(ticker, timestamp) for fast queries
  - Index on prediction_analytics(ticker, date) for analytics queries
*/

-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
  ticker text PRIMARY KEY,
  name text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Create historical prices table
CREATE TABLE IF NOT EXISTS historical_prices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker text NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
  timestamp timestamptz NOT NULL,
  open numeric(10, 2) NOT NULL,
  high numeric(10, 2) NOT NULL,
  low numeric(10, 2) NOT NULL,
  close numeric(10, 2) NOT NULL,
  volume bigint NOT NULL DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- Create prediction analytics table
CREATE TABLE IF NOT EXISTS prediction_analytics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker text NOT NULL REFERENCES companies(ticker) ON DELETE CASCADE,
  date date NOT NULL,
  predicted_close numeric(10, 2) NOT NULL,
  actual_close numeric(10, 2),
  error numeric(10, 2),
  horizon text NOT NULL CHECK (horizon IN ('10m', '30m', '1h')),
  created_at timestamptz DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_historical_prices_ticker_timestamp 
  ON historical_prices(ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_prediction_analytics_ticker_date 
  ON prediction_analytics(ticker, date DESC);

-- Enable RLS
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_analytics ENABLE ROW LEVEL SECURITY;

-- Public read access policies
CREATE POLICY "Public read access to companies"
  ON companies FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Public read access to historical prices"
  ON historical_prices FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Public read access to prediction analytics"
  ON prediction_analytics FOR SELECT
  TO anon
  USING (true);

-- Insert sample companies
INSERT INTO companies (ticker, name) VALUES
  ('RELIANCE', 'Reliance Industries Limited'),
  ('TCS', 'Tata Consultancy Services'),
  ('HDFCBANK', 'HDFC Bank Limited'),
  ('INFY', 'Infosys Limited'),
  ('HINDUNILVR', 'Hindustan Unilever Limited'),
  ('ICICIBANK', 'ICICI Bank Limited'),
  ('BHARTIARTL', 'Bharti Airtel Limited'),
  ('ITC', 'ITC Limited'),
  ('SBIN', 'State Bank of India'),
  ('LT', 'Larsen & Toubro Limited')
ON CONFLICT (ticker) DO NOTHING;