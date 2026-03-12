import { useState, useEffect } from 'react';
import { User } from 'lucide-react';
import { SettingsSection } from '../SettingsSection';
import { Input } from '../Input';

interface ProfileData {
  full_name: string;
  email: string;
  phone: string;
}

export function ProfileSection() {
  const [profile, setProfile] = useState<ProfileData>({
    full_name: '',
    email: '',
    phone: '',
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setProfile({
      full_name: 'John Doe',
      email: 'john.doe@example.com',
      phone: '+1 (555) 123-4567',
    });
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
  };

  return (
    <SettingsSection
      title="Profile"
      description="Manage your personal information"
      icon={User}
      onSave={handleSave}
      isSaving={isSaving}
    >
      <Input
        label="Full Name"
        value={profile.full_name}
        onChange={(value) => setProfile({ ...profile, full_name: value })}
        placeholder="Enter your full name"
      />
      <Input
        label="Email Address"
        type="email"
        value={profile.email}
        onChange={(value) => setProfile({ ...profile, email: value })}
        placeholder="your.email@example.com"
      />
      <Input
        label="Phone Number"
        type="tel"
        value={profile.phone}
        onChange={(value) => setProfile({ ...profile, phone: value })}
        placeholder="+1 (555) 000-0000"
      />
    </SettingsSection>
  );
}
