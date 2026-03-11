import { useEffect, useState } from 'react';
import { BrokerConnection } from './BrokerConnection';
import { OrderTicket } from './OrderTicket';
import { OrderResponse } from './OrderResponse';
import { OrderStatus } from './OrderStatus';
import {
  tradingApi,
  BrokerConfig,
  OrderRequest,
  OrderResponse as OrderResponseType,
  OrderStatus as OrderStatusType,
} from '../../api/trading';

export function TradePage() {
  const [brokerConfig, setBrokerConfig] = useState<BrokerConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [paperMode] = useState(false);
  const [orderResponse, setOrderResponse] = useState<OrderResponseType | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderStatus, setOrderStatus] = useState<OrderStatusType | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  useEffect(() => {
    loadBrokerConfig();
  }, []);

  const loadBrokerConfig = async () => {
    try {
      setConfigLoading(true);
      const config = await tradingApi.getBrokerConfig();
      setBrokerConfig(config);
    } catch (error) {
      console.error('Failed to load broker config:', error);
      setBrokerConfig(null);
    } finally {
      setConfigLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const result = await tradingApi.connectBroker();
      if (result.auth_url) {
        window.open(result.auth_url, '_blank');
      }
    } catch (error) {
      console.error('Failed to connect broker:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await tradingApi.logoutBroker();
      await loadBrokerConfig();
    } catch (error) {
      console.error('Failed to logout broker:', error);
    }
  };

  const handleSubmitOrder = async (
    order: OrderRequest & { side: 'BUY' | 'SELL' }
  ) => {
    try {
      setIsSubmitting(true);
      setOrderResponse(null);

      const response = await tradingApi.placeOrder(order);
      setOrderResponse(response);
    } catch (error) {
      console.error('Failed to place order:', error);
      setOrderResponse({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to place order',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOrderLookup = async (orderId: string) => {
    try {
      setStatusLoading(true);
      setStatusError(null);
      setOrderStatus(null);

      const status = await tradingApi.getOrderStatus(orderId);
      setOrderStatus(status);
    } catch (error) {
      console.error('Failed to fetch order status:', error);
      setStatusError(
        error instanceof Error ? error.message : 'Failed to fetch order status'
      );
    } finally {
      setStatusLoading(false);
    }
  };

  const isBrokerConnected = brokerConfig?.configured && brokerConfig?.has_access_token;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Trading Dashboard</h1>

        <div className="space-y-6">
          <BrokerConnection
            config={brokerConfig}
            loading={configLoading}
            onConnect={handleConnect}
            onLogout={handleLogout}
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <OrderTicket
              isBrokerConnected={isBrokerConnected || false}
              paperMode={paperMode}
              onSubmitOrder={handleSubmitOrder}
              isSubmitting={isSubmitting}
            />

            <div className="space-y-6">
              {orderResponse && (
                <OrderResponse
                  response={orderResponse}
                  onClose={() => setOrderResponse(null)}
                />
              )}

              <OrderStatus
                onLookup={handleOrderLookup}
                status={orderStatus}
                loading={statusLoading}
                error={statusError}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
