import React from 'react';
import { Card, CardContent } from '../../components/ui/Card';
import { Settings as SettingsIcon, AlertCircle } from 'lucide-react';

export const Settings = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
          <SettingsIcon className="h-6 w-6 mr-2 text-[var(--rzp-primary)]" /> Settings
        </h1>
        <p className="text-sm text-[var(--rzp-text-muted)]">Manage your merchant profile and policies.</p>
      </div>

      <Card className="border-dashed bg-gray-50/50">
        <CardContent className="flex flex-col items-center justify-center py-20 text-center">
          <AlertCircle className="h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-[var(--rzp-text)]">Settings are managed via API</h3>
          <p className="text-sm text-[var(--rzp-text-muted)] max-w-md mt-2">
            Dynamic merchant settings configuration is currently pending backend rollout. 
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
