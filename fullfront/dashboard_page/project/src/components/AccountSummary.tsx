import React from 'react'
import Card from './Card'

interface AccountSummaryProps {
  totalPortfolioValue: number
  todayPnL: number
  totalPnL: number
  holdingsCount: number
  openOrdersCount: number
}

const AccountSummary: React.FC<AccountSummaryProps> = ({
  totalPortfolioValue,
  todayPnL,
  totalPnL,
  holdingsCount,
  openOrdersCount,
}) => {
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
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '24px',
        }}
      >
        <div>
          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>
            Total Portfolio Value
          </div>
          <div style={{ fontSize: '24px', fontWeight: '600' }}>
            {formatCurrency(totalPortfolioValue)}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>
            Today's P&L
          </div>
          <div
            style={{
              fontSize: '24px',
              fontWeight: '600',
              color: getPnLColor(todayPnL),
            }}
          >
            {formatCurrency(todayPnL)}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>
            Total P&L
          </div>
          <div
            style={{
              fontSize: '24px',
              fontWeight: '600',
              color: getPnLColor(totalPnL),
            }}
          >
            {formatCurrency(totalPnL)}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>
            Holdings
          </div>
          <div style={{ fontSize: '24px', fontWeight: '600' }}>{holdingsCount}</div>
        </div>

        <div>
          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>
            Open Orders
          </div>
          <div style={{ fontSize: '24px', fontWeight: '600' }}>{openOrdersCount}</div>
        </div>
      </div>
    </Card>
  )
}

export default AccountSummary
