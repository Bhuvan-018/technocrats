/*
  # Create News Articles Table

  1. New Tables
    - `news_articles`
      - `id` (uuid, primary key) - Unique identifier for each article
      - `headline` (text) - Article headline
      - `summary` (text) - Short summary of the article
      - `impact` (text) - Market impact: 'positive', 'negative', or 'neutral'
      - `is_trending` (boolean) - Whether article is in trending section
      - `source` (text) - News source name
      - `related_stocks` (text array) - Stock tickers mentioned in article
      - `published_at` (timestamptz) - Publication timestamp
      - `created_at` (timestamptz) - Record creation timestamp

  2. Security
    - Enable RLS on `news_articles` table
    - Add policy for public read access (news is publicly viewable)
    - Add policy for authenticated users to insert articles (for admin/system)
*/

CREATE TABLE IF NOT EXISTS news_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  headline text NOT NULL,
  summary text NOT NULL,
  impact text NOT NULL CHECK (impact IN ('positive', 'negative', 'neutral')),
  is_trending boolean DEFAULT false,
  source text DEFAULT 'Market Wire',
  related_stocks text[] DEFAULT '{}',
  published_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view news articles"
  ON news_articles FOR SELECT
  USING (true);

CREATE POLICY "Authenticated users can insert news articles"
  ON news_articles FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update news articles"
  ON news_articles FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete news articles"
  ON news_articles FOR DELETE
  TO authenticated
  USING (true);

CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_trending ON news_articles(is_trending, published_at DESC);