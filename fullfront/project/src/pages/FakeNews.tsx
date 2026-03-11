import { ShieldAlert } from 'lucide-react';

export function FakeNews() {
  return (
    <div className="p-6">
      <div className="text-center py-20">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-red-100 to-orange-100 rounded-2xl mb-6">
          <ShieldAlert className="w-10 h-10 text-red-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-3">Fake News Detector</h1>
        <p className="text-gray-600 max-w-md mx-auto mb-8">
          Identify and filter out misleading market information with AI-powered analysis.
        </p>
        <div className="inline-block px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm font-medium">
          Coming Soon
        </div>
      </div>
    </div>
  );
}
