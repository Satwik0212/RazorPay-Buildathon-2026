import React from 'react';
import { Card, CardContent } from '../../components/ui/Card';
import { LineChart, BarChart } from 'lucide-react';

export const Analytics = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
          <LineChart className="h-6 w-6 mr-2 text-[var(--rzp-primary)]" /> Analytics
        </h1>
        <p className="text-sm text-[var(--rzp-text-muted)]">Deep dive into your buyer drop-offs and friction points.</p>
      </div>

      <Card className="border-dashed bg-gray-50/50">
        <CardContent className="flex flex-col items-center justify-center py-20 text-center">
          <BarChart className="h-12 w-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-semibold text-[var(--rzp-text)]">Analytics unavailable</h3>
          <p className="text-sm text-[var(--rzp-text-muted)] max-w-md mt-2">
            Detailed analytics will become available after sufficient real or simulated data exists.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
