import React from 'react'
import Card from './Card'
import { BrokerConfig } from '../types/dashboard'

interface BrokerStatusProps {
  config: BrokerConfig
}

const BrokerStatus: React.FC<BrokerStatusProps> = ({ config }) => {
  return (
    <Card>
      <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
        Broker Status
      </h2>

      {config.connected ? (
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}
          >
            <div
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#38a169',
              }}
            />
            <span style={{ fontSize: '16px', fontWeight: '500', color: '#38a169' }}>
              Broker Connected
            </span>
          </div>

          <div style={{ fontSize: '14px', color: '#718096', marginBottom: '8px' }}>
            <strong>Broker:</strong> {config.broker}
          </div>

          {config.accountId && (
            <div style={{ fontSize: '14px', color: '#718096', marginBottom: '8px' }}>
              <strong>Account ID:</strong> {config.accountId}
            </div>
          )}

          {config.lastSync && (
            <div style={{ fontSize: '14px', color: '#718096' }}>
              <strong>Last Sync:</strong>{' '}
              {new Date(config.lastSync).toLocaleString('en-IN')}
            </div>
          )}
        </div>
      ) : (
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px',
            }}
          >
            <div
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#e53e3e',
              }}
            />
            <span style={{ fontSize: '16px', fontWeight: '500', color: '#e53e3e' }}>
              No Broker Connected
            </span>
          </div>

          <button
            style={{
              backgroundColor: '#3182ce',
              color: '#ffffff',
              padding: '12px 24px',
              borderRadius: '6px',
              border: 'none',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
            onMouseOver={(e) =>
              (e.currentTarget.style.backgroundColor = '#2c5aa0')
            }
            onMouseOut={(e) =>
              (e.currentTarget.style.backgroundColor = '#3182ce')
            }
          >
            Connect Paytm Money
          </button>
        </div>
      )}
    </Card>
  )
}

export default BrokerStatus
