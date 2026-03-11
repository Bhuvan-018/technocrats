import { useState } from 'react';
import { Check, Crown, Zap, Rocket } from 'lucide-react';
import { subscriptionAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const plans = [
  {
    id: 'monthly',
    name: 'Monthly',
    price: 199,
    duration: '30 days',
    icon: Zap,
    features: [
      'Real-time market data',
      'Basic AI predictions',
      'Portfolio tracking',
      'Watchlist management',
      'Email support',
    ],
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'quarterly',
    name: 'Quarterly',
    price: 500,
    duration: '3 months',
    icon: Crown,
    popular: true,
    features: [
      'Everything in Monthly',
      'Advanced AI predictions',
      'Trust metrics & explainability',
      'Backtest analysis',
      'Priority support',
      'News & fake news detection',
    ],
    color: 'from-green-500 to-emerald-500',
  },
  {
    id: 'halfyearly',
    name: 'Half-Yearly',
    price: 1000,
    duration: '6 months',
    icon: Rocket,
    features: [
      'Everything in Quarterly',
      'AI Chatbot assistance',
      'Custom alerts',
      'Export data',
      '24/7 Premium support',
      'Early access to new features',
    ],
    color: 'from-orange-500 to-red-500',
  },
];

export function Subscription() {
  const [loading, setLoading] = useState<string | null>(null);
  const { user } = useAuth();

  const handleSubscribe = async (planId: string) => {
    setLoading(planId);
    try {
      const order = await subscriptionAPI.createOrder(planId);
      console.log('Order created:', order);
      await subscriptionAPI.activate(planId);
      alert('Subscription activated successfully!');
    } catch (error) {
      console.error('Subscription failed:', error);
      alert('Failed to process subscription. Please try again.');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900">Choose Your Plan</h1>
        <p className="text-gray-600 mt-2 text-lg">
          Unlock advanced features and take your trading to the next level
        </p>
      </div>

      {user?.subscriptionTier && user.subscriptionTier !== 'Free Plan' && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6 text-center">
          <Crown className="w-12 h-12 mx-auto text-green-600 mb-3" />
          <h3 className="text-xl font-semibold text-gray-900 mb-1">
            Active Subscription
          </h3>
          <p className="text-gray-600">
            You're currently on the <span className="font-semibold">{user.subscriptionTier}</span>{' '}
            plan
          </p>
          {user.subscriptionExpiry && (
            <p className="text-sm text-gray-500 mt-2">
              Expires on {new Date(user.subscriptionExpiry).toLocaleDateString()}
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        {plans.map((plan) => {
          const Icon = plan.icon;
          return (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl shadow-lg border-2 transition-all hover:shadow-2xl ${
                plan.popular
                  ? 'border-green-500 transform scale-105'
                  : 'border-gray-200 hover:border-blue-500'
              }`}
            >
              {plan.popular && (
                <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white text-center py-2 rounded-t-xl font-semibold text-sm">
                  MOST POPULAR
                </div>
              )}

              <div className="p-8">
                <div
                  className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${plan.color} flex items-center justify-center mb-4 shadow-lg`}
                >
                  <Icon className="w-8 h-8 text-white" />
                </div>

                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-900">₹{plan.price}</span>
                  <span className="text-gray-600 ml-2">/ {plan.duration}</span>
                </div>

                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={loading === plan.id}
                  className={`w-full py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed ${
                    plan.popular
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600'
                      : `bg-gradient-to-r ${plan.color} text-white`
                  }`}
                >
                  {loading === plan.id ? 'Processing...' : 'Subscribe Now'}
                </button>

                <div className="mt-8 space-y-3">
                  {plan.features.map((feature, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="mt-1">
                        <Check className="w-5 h-5 text-green-500" />
                      </div>
                      <span className="text-gray-700 text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="max-w-4xl mx-auto bg-gray-50 rounded-xl p-8">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 text-center">
          Frequently Asked Questions
        </h3>
        <div className="space-y-4">
          {[
            {
              q: 'Can I cancel my subscription anytime?',
              a: 'Yes, you can cancel your subscription at any time. Your access will continue until the end of your billing period.',
            },
            {
              q: 'What payment methods do you accept?',
              a: 'We accept all major credit/debit cards, UPI, net banking, and popular digital wallets.',
            },
            {
              q: 'Is there a free trial available?',
              a: 'New users get limited access to basic features. Subscribe to unlock all premium features.',
            },
          ].map((faq, index) => (
            <div
              key={index}
              className="bg-white rounded-lg p-4 border border-gray-200"
            >
              <h4 className="font-semibold text-gray-900 mb-2">{faq.q}</h4>
              <p className="text-gray-600 text-sm">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
