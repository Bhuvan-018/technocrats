import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface NewsArticle {
  id: string;
  headline: string;
  summary: string;
  impact: 'positive' | 'negative' | 'neutral';
  is_trending: boolean;
  source: string;
  related_stocks: string[];
  published_at: string;
  created_at: string;
}
