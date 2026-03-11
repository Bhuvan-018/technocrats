import { CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import { BrokerConfig } from '../../api/trading';

interface BrokerConnectionProps {
  config: BrokerConfig | null;
  loading: boolean;
  onConnect: () => void;
  onLogout: () => void;
}

export function BrokerConnection({
  config,
  loading,
  onConnect,
  onLogout,
}: BrokerConnectionProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Broker Connection</h2>
        <p className="text-gray-600">Loading broker configuration...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Broker Connection</h2>
        <p className="text-red-600">Failed to load broker configuration</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Broker Connection</h2>

      {!config.configured && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <XCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-900 mb-2">
                Broker Not Configured
              </h3>
              {config.missing_env_keys && config.missing_env_keys.length > 0 && (
                <div>
                  <p className="text-red-800 text-sm mb-2">
                    Missing environment keys:
                  </p>
                  <ul className="list-disc list-inside text-red-700 text-sm">
                    {config.missing_env_keys.map((key) => (
                      <li key={key}>{key}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {config.configured && !config.has_access_token && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start">
              <XCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-yellow-900 mb-1">
                  Broker Not Connected
                </h3>
                <p className="text-yellow-800 text-sm">
                  Connect your Paytm Money account to start trading
                </p>
              </div>
            </div>
            <button
              onClick={onConnect}
              className="ml-4 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              Connect Paytm
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {config.configured && config.has_access_token && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-green-900 mb-1">
                  Broker Connected
                </h3>
                <p className="text-green-800 text-sm">
                  Your Paytm Money account is connected and ready to trade
                </p>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
