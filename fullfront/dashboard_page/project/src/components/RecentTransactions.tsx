import React from 'react'
import Card from './Card'
import { Transaction } from '../types/dashboard'

interface RecentTransactionsProps {
  transactions: Transaction[]
}

const RecentTransactions: React.FC<RecentTransactionsProps> = ({ transactions }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(value)
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getTypeColor = (type: string) => {
    const typeColors: Record<string, string> = {
      buy: '#3182ce',
      sell: '#e53e3e',
      dividend: '#38a169',
      deposit: '#38a169',
      withdrawal: '#e53e3e',
    }
    return typeColors[type.toLowerCase()] || '#718096'
  }

  return (
    <Card>
      <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
        Recent Transactions
      </h2>

      {transactions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px', color: '#718096' }}>
          No recent transactions
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
                  Time
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  Type
                </th>
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
                  Price
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
                  Amount
                </th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      color: '#718096',
                    }}
                  >
                    {formatDate(transaction.timestamp)}
                  </td>
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: getTypeColor(transaction.type),
                    }}
                  >
                    {transaction.type.toUpperCase()}
                  </td>
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                    }}
                  >
                    {transaction.symbol || '-'}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {transaction.quantity || '-'}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {transaction.price ? formatCurrency(transaction.price) : '-'}
                  </td>
                  <td
                    style={{
                      textAlign: 'right',
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                    }}
                  >
                    {formatCurrency(transaction.amount)}
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

export default RecentTransactions
