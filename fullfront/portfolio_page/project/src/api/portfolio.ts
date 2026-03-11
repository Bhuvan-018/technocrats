import { PortfolioData } from '../types/portfolio';
import { getAccessToken, refreshAccessToken } from '../utils/auth';

export const fetchPortfolio = async (): Promise<PortfolioData> => {
  const accessToken = getAccessToken();

  if (!accessToken) {
    throw new Error('No access token available');
  }

  const makeRequest = async (token: string): Promise<Response> => {
    return fetch('/trade/portfolio', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
  };

  let response = await makeRequest(accessToken);

  if (response.status === 401) {
    const newToken = await refreshAccessToken();

    if (!newToken) {
      throw new Error('Failed to refresh token');
    }

    response = await makeRequest(newToken);
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch portfolio: ${response.statusText}`);
  }

  return response.json();
};
