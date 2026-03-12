import { useState, useEffect } from 'react';
import { Lock } from 'lucide-react';
import { SettingsSection } from '../SettingsSection';
import { Toggle } from '../Toggle';

interface PrivacySettings {
  analytics: boolean;
  marketing: boolean;
}

export function PrivacySection() {
  const [privacy, setPrivacy] = useState<PrivacySettings>({
    analytics: false,
    marketing: false,
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setPrivacy({
      analytics: false,
      marketing: false,
    });
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  return (
    <SettingsSection
      title="Privacy"
      description="Manage your data sharing preferences"
      icon={Lock}
      onSave={handleSave}
      isSaving={isSaving}
    >
      <Toggle
        enabled={privacy.analytics}
        onChange={(value) => setPrivacy({ ...privacy, analytics: value })}
        label="Analytics Data"
        description="Help us improve by sharing usage analytics"
      />
      <Toggle
        enabled={privacy.marketing}
        onChange={(value) => setPrivacy({ ...privacy, marketing: value })}
        label="Marketing Communications"
        description="Receive personalized offers and updates"
      />
    </SettingsSection>
  );
}
