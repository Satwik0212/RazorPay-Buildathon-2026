import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Loader2, ReceiptText, AlertTriangle } from 'lucide-react';
import { auditApi } from '../../api/audit';

export const Transactions = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const res = await auditApi.getAuditTimeline();
        setLogs(res.data.items || []);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load audit logs.');
      } finally {
        setLoading(false);
      }
    };
    fetchAudit();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
          <ReceiptText className="h-6 w-6 mr-2 text-[var(--rzp-primary)]" /> Transactions & Audit
        </h1>
        <p className="text-sm text-[var(--rzp-text-muted)]">Real production events across your checkout lifecycle.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)]" />
        </div>
      ) : error ? (
        <div className="p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-sm flex items-center">
          <AlertTriangle className="mr-2 h-5 w-5" />
          {error}
        </div>
      ) : logs.length === 0 ? (
        <Card className="border-dashed bg-gray-50/50">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <ReceiptText className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-[var(--rzp-text)]">No transaction data available yet</h3>
            <p className="text-sm text-[var(--rzp-text-muted)] max-w-md mt-2">
              Run a real buyer flow to generate commerce events.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Audit Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {logs.map((log: any, idx: number) => (
                <div key={idx} className="flex flex-col border-b last:border-0 pb-4 last:pb-0">
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-[var(--rzp-text)]">{log.event_type}</span>
                    <span className="text-xs text-[var(--rzp-text-muted)]">{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                  <span className="text-sm text-[var(--rzp-text-secondary)] font-mono text-xs mt-1 bg-gray-50 p-2 rounded">
                    {JSON.stringify(log.event_data)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
