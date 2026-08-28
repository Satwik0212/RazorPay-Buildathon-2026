import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Bot, LineChart, ShoppingBag, TrendingUp, AlertTriangle } from 'lucide-react';

export const Dashboard = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)]">Overview</h1>
        <p className="text-sm text-[var(--rzp-text-muted)]">Monitor your real transactions and AI simulated performance.</p>
      </div>

      <div className="bg-[var(--rzp-info-soft)] border border-[var(--rzp-info)] p-3 rounded-lg flex items-start text-sm text-[var(--rzp-info)]">
        <AlertTriangle className="h-5 w-5 mr-2 shrink-0" />
        <p>
          <strong>Notice:</strong> Business metrics aggregation is not yet available in the backend API. Showing placeholders for layout purposes. No fake metrics are generated.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {/* Real Data */}
        <MetricCard 
          title="GMV" 
          badge="REAL DATA"
          badgeColor="default"
          value="--" 
          icon={<TrendingUp className="h-5 w-5 text-[var(--rzp-success)]" />} 
        />
        <MetricCard 
          title="Orders" 
          badge="REAL DATA"
          badgeColor="default"
          value="--" 
          icon={<ShoppingBag className="h-5 w-5 text-[var(--rzp-primary)]" />} 
        />
        
        {/* Simulated Data */}
        <MetricCard 
          title="AI Match Rate" 
          badge="SIMULATED"
          badgeColor="ai"
          value="--" 
          icon={<Bot className="h-5 w-5 text-[var(--rzp-ai)]" />} 
        />
        <MetricCard 
          title="AI Conversion" 
          badge="SIMULATED"
          badgeColor="ai"
          value="--" 
          icon={<LineChart className="h-5 w-5 text-[var(--rzp-ai)]" />} 
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Recent Transactions</CardTitle>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-gray-600 px-2 py-1 rounded">Real Data</span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <ReceiptTextIcon className="h-12 w-12 text-gray-300 mb-4" />
              <p className="text-[var(--rzp-text-secondary)] font-medium">No recent transactions</p>
              <p className="text-sm text-[var(--rzp-text-muted)] mt-1">When customers purchase, orders will appear here.</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>AI Readiness</CardTitle>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)] px-2 py-1 rounded">Simulated</span>
            </div>
          </CardHeader>
          <CardContent>
             <div className="flex flex-col items-center justify-center py-6 text-center">
              <div className="w-24 h-24 rounded-full border-4 border-gray-200 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-gray-400">--</span>
              </div>
              <p className="text-sm font-medium">Not evaluated</p>
              <p className="text-xs text-[var(--rzp-text-muted)] mt-1">Run an optimization scan to get your score.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const MetricCard = ({ title, value, badge, badgeColor, icon }: any) => (
  <Card>
    <CardContent className="p-5">
      <div className="flex justify-between items-start mb-2">
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
          badgeColor === 'ai' ? 'bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)]' : 'bg-gray-100 text-gray-600'
        }`}>
          {badge}
        </span>
        <div className="p-1.5 bg-gray-50 rounded-lg">
          {icon}
        </div>
      </div>
      <div>
        <p className="text-sm font-medium text-[var(--rzp-text-muted)]">{title}</p>
        <p className="text-2xl font-bold text-[var(--rzp-text)] mt-1">{value}</p>
      </div>
    </CardContent>
  </Card>
);

const ReceiptTextIcon = (props: any) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" />
    <path d="M14 8H8" /><path d="M16 12H8" /><path d="M13 16H8" />
  </svg>
)
