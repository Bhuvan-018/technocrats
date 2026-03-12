import { type Dispatch, type ReactNode, type SetStateAction, useEffect, useState } from 'react';
import {
  AlertCircle,
  Bell,
  Check,
  CreditCard,
  Lock,
  Shield,
  User,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { settingsAPI, subscriptionAPI } from '../services/api';

type SettingsTab = 'profile' | 'security' | 'notifications' | 'privacy' | 'subscription';

const tabs: Array<{ id: SettingsTab; label: string; icon: LucideIcon }> = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'privacy', label: 'Privacy', icon: Lock },
  { id: 'subscription', label: 'Subscription', icon: CreditCard },
];

type ImpactMessage = { type: 'success' | 'info' | 'error'; text: string } | null;

export function Settings() {
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [message, setMessage] = useState<ImpactMessage>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);

  const [fullName, setFullName] = useState('John Doe');
  const [email, setEmail] = useState('john.doe@example.com');
  const [phone, setPhone] = useState('+1 (555) 123-4567');

  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  const [notifEmail, setNotifEmail] = useState(true);
  const [notifSms, setNotifSms] = useState(false);
  const [notifPush, setNotifPush] = useState(true);

  const [shareAnalytics, setShareAnalytics] = useState(false);
  const [marketingComms, setMarketingComms] = useState(false);

  const [plan, setPlan] = useState('pro');
  const [billing, setBilling] = useState('monthly');

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingSecurity, setSavingSecurity] = useState(false);
  const [savingNotifications, setSavingNotifications] = useState(false);
  const [savingPrivacy, setSavingPrivacy] = useState(false);
  const [savingSubscription, setSavingSubscription] = useState(false);

  useEffect(() => {
    const prefs = settingsAPI.loadPreferences();
    setNotifEmail(prefs.notifications.email);
    setNotifSms(prefs.notifications.sms);
    setNotifPush(prefs.notifications.push);
    setShareAnalytics(prefs.privacy.analytics);
    setMarketingComms(prefs.privacy.marketing);
    setTwoFactorEnabled(prefs.security.twoFactorEnabled);
    setPlan(prefs.subscription.plan);
    setBilling(prefs.subscription.billing);

    if (user) {
      setFullName(user.name || '');
      setEmail(user.email || '');
    }

    const hydrate = async () => {
      try {
        const profile = await settingsAPI.getProfile();
        if (profile) {
          const nextName = String(profile.name || profile.full_name || fullName);
          const nextEmail = String(profile.email || email);
          setFullName(nextName);
          setEmail(nextEmail);
          setPhone(String(profile.phone || phone));
          updateUser({ name: nextName, email: nextEmail });
        }

        const sub = await settingsAPI.getSubscription();
        if (sub?.tier) {
          updateUser({ subscriptionTier: String(sub.tier) });
          const tier = String(sub.tier).toLowerCase();
          if (tier === 'free' || tier === 'pro' || tier === 'enterprise') {
            setPlan(tier);
          }
        }
      } catch {
        // Keep local state values if profile APIs are unavailable.
      } finally {
        setLoadingProfile(false);
      }
    };

    hydrate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const savePrefs = async (overrides?: Partial<ReturnType<typeof settingsAPI.loadPreferences>>) => {
    const payload = {
      notifications: { email: notifEmail, sms: notifSms, push: notifPush },
      privacy: { analytics: shareAnalytics, marketing: marketingComms },
      security: { twoFactorEnabled },
      subscription: { plan, billing },
      ...overrides,
    };
    await settingsAPI.savePreferences(payload);
  };

  const showSaved = (text = 'Settings saved successfully.') => setMessage({ type: 'success', text });

  const sectionCard = (
    title: string,
    description: string,
    Icon: LucideIcon,
    content: ReactNode,
    onSave?: () => Promise<void>,
    isSaving = false
  ) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Icon className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <p className="text-sm text-gray-600 mt-0.5">{description}</p>
          </div>
        </div>
      </div>
      <div className="px-6 py-2 divide-y divide-gray-200">{content}</div>
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 flex justify-end">
        <button
          onClick={onSave}
          disabled={!onSave || isSaving}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );

  const renderSection = () => {
    switch (activeTab) {
      case 'profile':
        return sectionCard(
          'Profile',
          'Manage your personal information',
          User,
          <>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-900 mb-2">Full Name</label>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-900 mb-2">Email Address</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-900 mb-2">Phone Number</label>
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            </div>
          </>,
          async () => {
            setSavingProfile(true);
            try {
              const current = user || { id: '', email: '', name: '' };
              updateUser({ ...current, name: fullName, email });
              localStorage.setItem('user_profile', JSON.stringify({ full_name: fullName, email, phone }));
              showSaved('Profile updated.');
            } catch (e) {
              setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Failed to save profile.' });
            } finally {
              setSavingProfile(false);
            }
          },
          savingProfile
        );

      case 'security':
        return sectionCard(
          'Security',
          'Manage your account security settings',
          Shield,
          <>
            <div className="py-4">
              <button
                onClick={() => setMessage({ type: 'info', text: 'Password reset endpoint is not available yet. Connect /api/auth/password-reset when backend adds it.' })}
                className="w-full sm:w-auto px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Reset Password
              </button>
              <p className="text-sm text-gray-500 mt-2">A password reset link will be sent to your email.</p>
            </div>
            <div className="flex items-center justify-between py-4">
              <div>
                <p className="text-sm font-medium text-gray-900">Two-Factor Authentication</p>
                <p className="text-sm text-gray-500 mt-0.5">Add an extra layer of security to your account.</p>
              </div>
              <button
                type="button"
                onClick={() => setTwoFactorEnabled((v) => !v)}
                className={`relative inline-flex h-6 w-11 rounded-full border-2 border-transparent transition-colors ${twoFactorEnabled ? 'bg-blue-600' : 'bg-gray-200'}`}
                role="switch"
                aria-checked={twoFactorEnabled}
              >
                <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${twoFactorEnabled ? 'translate-x-5' : 'translate-x-0'}`} />
              </button>
            </div>
          </>,
          async () => {
            setSavingSecurity(true);
            try {
              await savePrefs();
              showSaved('Security preferences updated.');
            } catch (e) {
              setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Failed to save security settings.' });
            } finally {
              setSavingSecurity(false);
            }
          },
          savingSecurity
        );

      case 'notifications':
        return sectionCard(
          'Notifications',
          'Control how you receive updates',
          Bell,
          <>
            {[
              ['Email Notifications', 'Receive updates and alerts via email', notifEmail, setNotifEmail],
              ['SMS Notifications', 'Get important alerts via text message', notifSms, setNotifSms],
              ['Push Notifications', 'Receive notifications in your browser', notifPush, setNotifPush],
            ].map(([label, desc, value, setter]) => (
              <div className="flex items-center justify-between py-4" key={String(label)}>
                <div>
                  <p className="text-sm font-medium text-gray-900">{String(label)}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{String(desc)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => (setter as Dispatch<SetStateAction<boolean>>)((v) => !v)}
                  className={`relative inline-flex h-6 w-11 rounded-full border-2 border-transparent transition-colors ${value ? 'bg-blue-600' : 'bg-gray-200'}`}
                  role="switch"
                  aria-checked={Boolean(value)}
                >
                  <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${value ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>
            ))}
          </>,
          async () => {
            setSavingNotifications(true);
            try {
              await savePrefs();
              showSaved('Notification preferences saved.');
            } catch (e) {
              setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Failed to save notification settings.' });
            } finally {
              setSavingNotifications(false);
            }
          },
          savingNotifications
        );

      case 'privacy':
        return sectionCard(
          'Privacy',
          'Manage your data sharing preferences',
          Lock,
          <>
            {[
              ['Analytics Data', 'Help us improve by sharing usage analytics', shareAnalytics, setShareAnalytics],
              ['Marketing Communications', 'Receive personalized offers and updates', marketingComms, setMarketingComms],
            ].map(([label, desc, value, setter]) => (
              <div className="flex items-center justify-between py-4" key={String(label)}>
                <div>
                  <p className="text-sm font-medium text-gray-900">{String(label)}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{String(desc)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => (setter as Dispatch<SetStateAction<boolean>>)((v) => !v)}
                  className={`relative inline-flex h-6 w-11 rounded-full border-2 border-transparent transition-colors ${value ? 'bg-blue-600' : 'bg-gray-200'}`}
                  role="switch"
                  aria-checked={Boolean(value)}
                >
                  <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${value ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>
            ))}
          </>,
          async () => {
            setSavingPrivacy(true);
            try {
              await savePrefs();
              showSaved('Privacy preferences saved.');
            } catch (e) {
              setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Failed to save privacy settings.' });
            } finally {
              setSavingPrivacy(false);
            }
          },
          savingPrivacy
        );

      case 'subscription':
        return sectionCard(
          'Subscription',
          'Manage your plan and billing',
          CreditCard,
          <>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-900 mb-2">Plan Type</label>
              <select value={plan} onChange={(e) => setPlan(e.target.value)} className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="free">Free Plan</option>
                <option value="pro">Pro Plan - $29/mo</option>
                <option value="enterprise">Enterprise Plan - $99/mo</option>
              </select>
            </div>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-900 mb-2">Billing Cycle</label>
              <select value={billing} onChange={(e) => setBilling(e.target.value)} className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly (Save 20%)</option>
              </select>
            </div>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-900 mb-3">Payment Method</label>
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-gray-50 gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">Visa ending in 4242</p>
                  <p className="text-xs text-gray-500">Next billing: April 12, 2026</p>
                </div>
                <button
                  onClick={() => setMessage({ type: 'info', text: 'Payment update flow can be connected to subscription API.' })}
                  className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                >
                  Update
                </button>
              </div>
            </div>
          </>,
          async () => {
            setSavingSubscription(true);
            try {
              await subscriptionAPI.activate(plan);
              await savePrefs({ subscription: { plan, billing } });
              updateUser({ subscriptionTier: plan });
              showSaved(`Subscription updated to ${plan.toUpperCase()}.`);
            } catch (e) {
              setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Failed to update subscription.' });
            } finally {
              setSavingSubscription(false);
            }
          },
          savingSubscription
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account settings and preferences</p>
      </div>

      {message && (
        <div
          className={`rounded-lg border p-3 text-sm flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : message.type === 'error'
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-blue-50 border-blue-200 text-blue-800'
          }`}
        >
          {message.type === 'error' ? <AlertCircle className="w-4 h-4" /> : <Check className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {loadingProfile && (
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-600">Loading settings...</div>
      )}

      <div className="xl:grid xl:grid-cols-12 xl:gap-8">
        <aside className="xl:col-span-3">
          <nav className="space-y-1 bg-white rounded-xl shadow-sm border border-gray-200 p-2 sticky top-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="mt-6 xl:mt-0 xl:col-span-9">{renderSection()}</main>
      </div>
    </div>
  );
}
