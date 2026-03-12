import { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';
import { SettingsSection } from '../SettingsSection';
import { Toggle } from '../Toggle';

export function SecuritySection() {
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setTwoFactorEnabled(false);
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  const handlePasswordReset = () => {
    alert('Password reset email sent!');
  };

  return (
    <SettingsSection
      title="Security"
      description="Manage your account security settings"
      icon={Shield}
      onSave={handleSave}
      isSaving={isSaving}
    >
      <div className="py-4">
        <button
          onClick={handlePasswordReset}
          className="w-full sm:w-auto px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
        >
          Reset Password
        </button>
        <p className="text-sm text-gray-500 mt-2">
          We'll send a password reset link to your email
        </p>
      </div>
      <Toggle
        enabled={twoFactorEnabled}
        onChange={setTwoFactorEnabled}
        label="Two-Factor Authentication"
        description="Add an extra layer of security to your account"
      />
    </SettingsSection>
  );
}
