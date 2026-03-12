import { useState } from 'react';
import { User, Shield, Bell, Lock, CreditCard } from 'lucide-react';
import { ProfileSection } from '../components/sections/ProfileSection';
import { SecuritySection } from '../components/sections/SecuritySection';
import { NotificationsSection } from '../components/sections/NotificationsSection';
import { PrivacySection } from '../components/sections/PrivacySection';
import { SubscriptionSection } from '../components/sections/SubscriptionSection';

type SettingsTab = 'profile' | 'security' | 'notifications' | 'privacy' | 'subscription';

const tabs = [
  { id: 'profile' as SettingsTab, label: 'Profile', icon: User },
  { id: 'security' as SettingsTab, label: 'Security', icon: Shield },
  { id: 'notifications' as SettingsTab, label: 'Notifications', icon: Bell },
  { id: 'privacy' as SettingsTab, label: 'Privacy', icon: Lock },
  { id: 'subscription' as SettingsTab, label: 'Subscription', icon: CreditCard },
];

export function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');

  const renderSection = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfileSection />;
      case 'security':
        return <SecuritySection />;
      case 'notifications':
        return <NotificationsSection />;
      case 'privacy':
        return <PrivacySection />;
      case 'subscription':
        return <SubscriptionSection />;
      default:
        return <ProfileSection />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Manage your account settings and preferences
          </p>
        </div>

        <div className="lg:grid lg:grid-cols-12 lg:gap-8">
          <aside className="lg:col-span-3">
            <nav className="space-y-1 bg-white rounded-xl shadow-sm border border-gray-200 p-2 sticky top-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </aside>

          <main className="mt-8 lg:mt-0 lg:col-span-9">
            <div className="space-y-6">{renderSection()}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
