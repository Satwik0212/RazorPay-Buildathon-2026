import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import {
  Loader2,
  ReceiptText,
  AlertTriangle,
  CheckCircle2,
  FileCheck2,
  ArrowRight,
  ShieldCheck,
  Package,
  Layers,
  Sparkles
} from 'lucide-react';
import { auditApi } from '../../api/audit';

export const Transactions = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');

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

  const filteredLogs = logs.filter(log => {
    if (filterType === 'ALL') return true;
    if (filterType === 'RECOMMENDATIONS') return log.event_type === 'RECOMMENDATION_APPLIED';
    if (filterType === 'ORDERS') return log.event_type?.includes('ORDER') || log.event_type?.includes('PAYMENT');
    return true;
  });

  const recAppliedCount = logs.filter(l => l.event_type === 'RECOMMENDATION_APPLIED').length;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center tracking-tight">
            <ReceiptText className="h-6 w-6 mr-2 text-[var(--rzp-primary)]" /> Transactions & Audit Timeline
          </h1>
          <p className="text-sm text-[var(--rzp-text-muted)] mt-1">
            Immutable audit record of production commerce events and applied AI catalogue mutations.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Link to="/optimization?step=action">
            <Button variant="outline" size="sm" className="text-xs font-semibold">
              <Sparkles className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-ai)]" /> Back to Optimizations
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Filter Tabs */}
      <div className="flex items-center space-x-2 p-1 bg-gray-100/80 rounded-lg border border-gray-200 w-fit text-xs font-semibold">
        <button
          type="button"
          onClick={() => setFilterType('ALL')}
          className={`px-3 py-1.5 rounded-md transition-all ${
            filterType === 'ALL'
              ? 'bg-white text-[var(--rzp-text)] shadow-xs font-bold'
              : 'text-[var(--rzp-text-muted)] hover:text-[var(--rzp-text)]'
          }`}
        >
          All Events ({logs.length})
        </button>
        <button
          type="button"
          onClick={() => setFilterType('RECOMMENDATIONS')}
          className={`px-3 py-1.5 rounded-md transition-all ${
            filterType === 'RECOMMENDATIONS'
              ? 'bg-purple-100 text-purple-900 border border-purple-200 shadow-xs font-bold'
              : 'text-[var(--rzp-text-muted)] hover:text-purple-700'
          }`}
        >
          Catalogue Mutations ({recAppliedCount})
        </button>
        <button
          type="button"
          onClick={() => setFilterType('ORDERS')}
          className={`px-3 py-1.5 rounded-md transition-all ${
            filterType === 'ORDERS'
              ? 'bg-blue-100 text-blue-900 border border-blue-200 shadow-xs font-bold'
              : 'text-[var(--rzp-text-muted)] hover:text-blue-700'
          }`}
        >
          Orders & Payments ({logs.length - recAppliedCount})
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-[var(--rzp-border)]">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)] mb-2" />
          <p className="text-xs font-semibold text-[var(--rzp-text-muted)]">Loading audit timeline...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-sm flex items-center border border-red-200">
          <AlertTriangle className="mr-2 h-5 w-5 shrink-0" />
          {error}
        </div>
      ) : filteredLogs.length === 0 ? (
        <Card className="border-dashed bg-gray-50/50">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <ReceiptText className="h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-base font-semibold text-[var(--rzp-text)]">No audit events found</h3>
            <p className="text-xs text-[var(--rzp-text-muted)] max-w-md mt-1">
              Apply a recommendation or run buyer checkout to generate immutable audit events.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredLogs.map((log: any, idx: number) => {
            const isRecApplied = log.event_type === 'RECOMMENDATION_APPLIED';
            const eventData = log.event_data || {};

            return (
              <Card key={log.id || idx} className={`border transition-all hover:shadow-xs ${
                isRecApplied ? 'border-purple-200 bg-purple-50/15' : 'border-[var(--rzp-border)]'
              }`}>
                <CardContent className="p-5 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
                    <div className="flex items-center space-x-2.5">
                      {isRecApplied ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-900 border border-purple-300">
                          <FileCheck2 className="h-3.5 w-3.5 mr-1 text-purple-700" /> RECOMMENDATION_APPLIED
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200">
                          <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-blue-600" /> {log.event_type}
                        </span>
                      )}

                      {eventData.action_performed && (
                        <span className="text-xs font-mono font-semibold text-gray-700 bg-gray-100 px-2 py-0.5 rounded">
                          {eventData.action_performed}
                        </span>
                      )}

                      {eventData.result === 'SUCCESS' && (
                        <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                          SUCCESS
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-[var(--rzp-text-muted)] font-mono">
                      {new Date(log.created_at).toLocaleString()}
                    </div>
                  </div>

                  {/* Detail Content */}
                  {isRecApplied ? (
                    <div className="space-y-2 text-xs">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-white p-3 rounded-lg border border-purple-100">
                        <div>
                          <span className="text-[10px] font-semibold text-gray-400 uppercase block">Entity Target</span>
                          <span className="font-mono text-xs font-medium text-gray-800 truncate block">
                            Product: {log.entity_id ? `${log.entity_id.slice(0, 12)}...` : 'Catalogue Product'}
                          </span>
                        </div>

                        <div>
                          <span className="text-[10px] font-semibold text-gray-400 uppercase block">State Before Mutation</span>
                          <span className="font-mono text-xs text-red-600 bg-red-50 px-1.5 py-0.5 rounded border border-red-100 inline-block">
                            {JSON.stringify(eventData.before_state || {})}
                          </span>
                        </div>

                        <div>
                          <span className="text-[10px] font-semibold text-gray-400 uppercase block">State After Mutation</span>
                          <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 inline-block">
                            {JSON.stringify(eventData.after_state || {})}
                          </span>
                        </div>
                      </div>

                      {eventData.recommendation_id && (
                        <div className="flex items-center justify-between text-[11px] text-gray-500 pt-1">
                          <span className="font-mono">Recommendation ID: {eventData.recommendation_id.slice(0, 12)}...</span>
                          <Link to="/optimization?step=action" className="text-[var(--rzp-primary)] font-semibold hover:underline flex items-center">
                            View Recommendation <ArrowRight className="h-3 w-3 ml-0.5" />
                          </Link>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs font-mono bg-gray-50 p-3 rounded border border-gray-200 text-gray-700 overflow-x-auto">
                      {JSON.stringify(eventData, null, 2)}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
