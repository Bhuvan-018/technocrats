import React from 'react'
import Card from './Card'
import { Holding } from '../types/dashboard'

interface PortfolioSummaryProps {
  holdings: Holding[]
}

const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({ holdings }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const getPnLColor = (value: number) => {
    if (value > 0) return '#38a169'
    if (value < 0) return '#e53e3e'
    return '#718096'
  }

  return (
    <Card>
      <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
        Portfolio Summary
      </h2>

      {holdings.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px', color: '#718096' }}>
          No holdings found
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  Symbol
                </th>
                <th
                  style={{
                    textAlign: 'right',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  Quantity
                </th>
                <th
                  style={{
                    textAlign: 'right',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  Avg Price
                </th>
                <th
                  style={{
                    textAlign: 'right',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  Current Price
                </th>
                <th
                  style={{
                    textAlign: 'right',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  P&L
                </th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding) => (
                <tr
                  key={holding.symbol}
                  style={{ borderBottom: '1px solid #e2e8f0' }}
                >
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                    }}
                  >
                    {holding.symbol}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {holding.quantity}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {formatCurrency(holding.averagePrice)}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {formatCurrency(holding.currentPrice)}
                  </td>
                  <td
                    style={{
                      textAlign: 'right',
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: getPnLColor(holding.pnl),
                    }}
                  >
                    {formatCurrency(holding.pnl)} ({holding.pnlPercentage >= 0 ? '+' : ''}
                    {holding.pnlPercentage.toFixed(2)}%)
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

export default PortfolioSummary
