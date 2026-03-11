import { Settings as SettingsIcon } from 'lucide-react';

export function Settings() {
  return (
    <div className="p-6">
      <div className="text-center py-20">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl mb-6">
          <SettingsIcon className="w-10 h-10 text-purple-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-3">Settings</h1>
        <p className="text-gray-600 max-w-md mx-auto mb-8">
          Manage your account preferences, notifications, and security settings.
        </p>
        <div className="inline-block px-4 py-2 bg-purple-50 text-purple-700 rounded-lg text-sm font-medium">
          Coming Soon
        </div>
      </div>
    </div>
  );
}
