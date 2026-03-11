import React from 'react'
import Card from './Card'
import { Index, OilPrice } from '../types/dashboard'

interface MarketSnapshotProps {
  indices: Index[]
  oilPrice: OilPrice
}

const MarketSnapshot: React.FC<MarketSnapshotProps> = ({ indices, oilPrice }) => {
  const getChangeColor = (change: number) => {
    if (change > 0) return '#38a169'
    if (change < 0) return '#e53e3e'
    return '#718096'
  }

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
      }}
    >
      {indices.map((index) => (
        <Card key={index.name}>
          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '8px' }}>
            {index.name}
          </div>
          <div style={{ fontSize: '28px', fontWeight: '600', marginBottom: '4px' }}>
            {formatNumber(index.value)}
          </div>
          <div
            style={{
              fontSize: '14px',
              color: getChangeColor(index.change),
              fontWeight: '500',
            }}
          >
            {index.change >= 0 ? '+' : ''}
            {formatNumber(index.change)} ({index.changePercentage >= 0 ? '+' : ''}
            {formatNumber(index.changePercentage)}%)
          </div>
        </Card>
      ))}

      <Card>
        <div style={{ fontSize: '14px', color: '#718096', marginBottom: '8px' }}>
          Crude Oil
        </div>
        <div style={{ fontSize: '28px', fontWeight: '600', marginBottom: '4px' }}>
          ${formatNumber(oilPrice.price)}
        </div>
        <div
          style={{
            fontSize: '14px',
            color: getChangeColor(oilPrice.change),
            fontWeight: '500',
          }}
        >
          {oilPrice.change >= 0 ? '+' : ''}
          {formatNumber(oilPrice.change)} ({oilPrice.changePercentage >= 0 ? '+' : ''}
          {formatNumber(oilPrice.changePercentage)}%)
        </div>
      </Card>
    </div>
  )
}

export default MarketSnapshot
