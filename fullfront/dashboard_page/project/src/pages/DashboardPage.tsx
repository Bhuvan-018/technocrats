import React, { useEffect, useState } from 'react'
import { dashboardService } from '../services/dashboardService'
import {
  DashboardData,
  MarketStatus,
  Index,
  OilPrice,
  BrokerConfig,
  Order,
  Transaction,
} from '../types/dashboard'
import AccountSummary from '../components/AccountSummary'
import MarketSnapshot from '../components/MarketSnapshot'
import PortfolioSummary from '../components/PortfolioSummary'
import RecentOrders from '../components/RecentOrders'
import RecentTransactions from '../components/RecentTransactions'
import BrokerStatus from '../components/BrokerStatus'
import Loader from '../components/Loader'
import ErrorMessage from '../components/ErrorMessage'

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null)
  const [indices, setIndices] = useState<Index[]>([])
  const [oilPrice, setOilPrice] = useState<OilPrice | null>(null)
  const [brokerConfig, setBrokerConfig] = useState<BrokerConfig | null>(null)
  const [recentOrders, setRecentOrders] = useState<Order[]>([])
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([])

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [
        dashboard,
        market,
        indicesData,
        oil,
        broker,
        orders,
        transactions,
      ] = await Promise.all([
        dashboardService.getDashboard().catch(() => null),
        dashboardService.getMarketStatus().catch(() => null),
        dashboardService.getIndices().catch(() => []),
        dashboardService.getOilPrice().catch(() => null),
        dashboardService.getBrokerConfig().catch(() => null),
        dashboardService.getRecentOrders().catch(() => []),
        dashboardService.getRecentTransactions().catch(() => []),
      ])

      setDashboardData(dashboard)
      setMarketStatus(market)
      setIndices(indicesData)
      setOilPrice(oil)
      setBrokerConfig(broker)
      setRecentOrders(orders)
      setRecentTransactions(transactions)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Loader />
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f7fa' }}>
      <header
        style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          padding: '16px 24px',
        }}
      >
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <h1 style={{ fontSize: '24px', fontWeight: '600' }}>Trading Dashboard</h1>
          {marketStatus && (
            <div style={{ fontSize: '14px', color: '#718096', marginTop: '4px' }}>
              Market Status:{' '}
              <span
                style={{
                  fontWeight: '500',
                  color: marketStatus.status === 'open' ? '#38a169' : '#e53e3e',
                }}
              >
                {marketStatus.status.toUpperCase()}
              </span>
            </div>
          )}
        </div>
      </header>

      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        {error && <ErrorMessage message={error} />}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {dashboardData && (
            <AccountSummary
              totalPortfolioValue={dashboardData.totalPortfolioValue}
              todayPnL={dashboardData.todayPnL}
              totalPnL={dashboardData.totalPnL}
              holdingsCount={dashboardData.holdingsCount}
              openOrdersCount={dashboardData.openOrdersCount}
            />
          )}

          {indices.length > 0 && oilPrice && (
            <div>
              <h2
                style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  marginBottom: '16px',
                }}
              >
                Market Snapshot
              </h2>
              <MarketSnapshot indices={indices} oilPrice={oilPrice} />
            </div>
          )}

          {dashboardData && dashboardData.holdings.length > 0 && (
            <PortfolioSummary holdings={dashboardData.holdings} />
          )}

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
              gap: '24px',
            }}
          >
            {recentOrders.length > 0 && <RecentOrders orders={recentOrders} />}
            {recentTransactions.length > 0 && (
              <RecentTransactions transactions={recentTransactions} />
            )}
          </div>

          {brokerConfig && <BrokerStatus config={brokerConfig} />}
        </div>
      </main>
    </div>
  )
}

export default DashboardPage
