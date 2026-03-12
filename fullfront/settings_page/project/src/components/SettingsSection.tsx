import { Video as LucideIcon } from 'lucide-react';
import { ReactNode } from 'react';

interface SettingsSectionProps {
  title: string;
  description: string;
  icon: LucideIcon;
  children: ReactNode;
  onSave?: () => void;
  isSaving?: boolean;
}

export function SettingsSection({
  title,
  description,
  icon: Icon,
  children,
  onSave,
  isSaving = false,
}: SettingsSectionProps) {
  return (
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
      <div className="px-6 py-2 divide-y divide-gray-200">{children}</div>
      {onSave && (
        <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 flex justify-end">
          <button
            onClick={onSave}
            disabled={isSaving}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      )}
    </div>
  );
}
