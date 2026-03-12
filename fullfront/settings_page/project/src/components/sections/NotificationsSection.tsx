import { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { SettingsSection } from '../SettingsSection';
import { Toggle } from '../Toggle';

interface NotificationSettings {
  email: boolean;
  sms: boolean;
  push: boolean;
}

export function NotificationsSection() {
  const [notifications, setNotifications] = useState<NotificationSettings>({
    email: true,
    sms: false,
    push: true,
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setNotifications({
      email: true,
      sms: false,
      push: true,
    });
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  return (
    <SettingsSection
      title="Notifications"
      description="Control how you receive updates"
      icon={Bell}
      onSave={handleSave}
      isSaving={isSaving}
    >
      <Toggle
        enabled={notifications.email}
        onChange={(value) => setNotifications({ ...notifications, email: value })}
        label="Email Notifications"
        description="Receive updates and alerts via email"
      />
      <Toggle
        enabled={notifications.sms}
        onChange={(value) => setNotifications({ ...notifications, sms: value })}
        label="SMS Notifications"
        description="Get important alerts via text message"
      />
      <Toggle
        enabled={notifications.push}
        onChange={(value) => setNotifications({ ...notifications, push: value })}
        label="Push Notifications"
        description="Receive notifications in your browser"
      />
    </SettingsSection>
  );
}
