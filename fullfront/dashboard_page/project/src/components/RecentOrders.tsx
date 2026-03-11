import React from 'react'
import Card from './Card'
import { Order } from '../types/dashboard'

interface RecentOrdersProps {
  orders: Order[]
}

const RecentOrders: React.FC<RecentOrdersProps> = ({ orders }) => {
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

  const getStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      completed: '#38a169',
      pending: '#d69e2e',
      cancelled: '#e53e3e',
      rejected: '#e53e3e',
    }
    return statusColors[status.toLowerCase()] || '#718096'
  }

  const getSideColor = (side: string) => {
    return side.toLowerCase() === 'buy' ? '#3182ce' : '#e53e3e'
  }

  return (
    <Card>
      <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
        Recent Orders
      </h2>

      {orders.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px', color: '#718096' }}>
          No recent orders
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
                  Symbol
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
                  Side
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
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#718096',
                  }}
                >
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      color: '#718096',
                    }}
                  >
                    {formatDate(order.timestamp)}
                  </td>
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                    }}
                  >
                    {order.symbol}
                  </td>
                  <td style={{ padding: '12px 8px', fontSize: '14px' }}>
                    {order.type}
                  </td>
                  <td
                    style={{
                      padding: '12px 8px',
                      fontSize: '14px',
                      fontWeight: '500',
                      color: getSideColor(order.side),
                    }}
                  >
                    {order.side.toUpperCase()}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {order.quantity}
                  </td>
                  <td style={{ textAlign: 'right', padding: '12px 8px', fontSize: '14px' }}>
                    {formatCurrency(order.price)}
                  </td>
                  <td style={{ padding: '12px 8px', fontSize: '14px' }}>
                    <span
                      style={{
                        color: getStatusColor(order.status),
                        fontWeight: '500',
                      }}
                    >
                      {order.status}
                    </span>
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

export default RecentOrders
