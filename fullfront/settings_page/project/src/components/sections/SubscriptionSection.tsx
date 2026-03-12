import { useState, useEffect } from 'react';
import { CreditCard } from 'lucide-react';
import { SettingsSection } from '../SettingsSection';
import { Select } from '../Select';

interface SubscriptionData {
  plan: string;
  billing: string;
  paymentMethod: string;
  cardLast4: string;
  nextBilling: string;
}

export function SubscriptionSection() {
  const [subscription, setSubscription] = useState<SubscriptionData>({
    plan: 'pro',
    billing: 'monthly',
    paymentMethod: 'Visa',
    cardLast4: '4242',
    nextBilling: 'April 12, 2026',
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setSubscription({
      plan: 'pro',
      billing: 'monthly',
      paymentMethod: 'Visa',
      cardLast4: '4242',
      nextBilling: 'April 12, 2026',
    });
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  const handleUpdatePayment = () => {
    alert('Payment method update coming soon!');
  };

  return (
    <SettingsSection
      title="Subscription"
      description="Manage your plan and billing"
      icon={CreditCard}
      onSave={handleSave}
      isSaving={isSaving}
    >
      <Select
        label="Plan Type"
        value={subscription.plan}
        onChange={(value) => setSubscription({ ...subscription, plan: value })}
        options={[
          { value: 'free', label: 'Free Plan' },
          { value: 'pro', label: 'Pro Plan - $29/mo' },
          { value: 'enterprise', label: 'Enterprise Plan - $99/mo' },
        ]}
      />
      <Select
        label="Billing Cycle"
        value={subscription.billing}
        onChange={(value) => setSubscription({ ...subscription, billing: value })}
        options={[
          { value: 'monthly', label: 'Monthly' },
          { value: 'yearly', label: 'Yearly (Save 20%)' },
        ]}
      />
      <div className="py-4">
        <label className="block text-sm font-medium text-gray-900 mb-3">
          Payment Method
        </label>
        <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-12 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">
              {subscription.paymentMethod.toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {subscription.paymentMethod} ending in {subscription.cardLast4}
              </p>
              <p className="text-xs text-gray-500">
                Next billing: {subscription.nextBilling}
              </p>
            </div>
          </div>
          <button
            onClick={handleUpdatePayment}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            Update
          </button>
        </div>
      </div>
    </SettingsSection>
  );
}
