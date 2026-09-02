import React, { useState } from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  TrendingUp, 
  Package, 
  TestTube, 
  ArrowRight, 
  Clock, 
  RotateCcw,
  Check
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardFooter } from '../../ui/Card';
import { Button } from '../../ui/Button';
import type { Recommendation, Product } from '../../../types';
import { 
  getRecommendationCategory, 
  getRecommendationSeverity, 
  getTargetPersonas 
} from './recommendationHelpers';

interface RecommendationCardProps {
  recommendation: Recommendation;
  product?: Product;
  onStatusChange: (id: string, status: string) => Promise<void>;
  onTestWithWhatIf: (rec: Recommendation) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  product,
  onStatusChange,
  onTestWithWhatIf
}) => {
  const [updating, setUpdating] = useState(false);

  const { category, colorClass, bgClass, borderClass } = getRecommendationCategory(recommendation);
  const { severity, label: severityLabel, badgeClass: severityBadgeClass } = getRecommendationSeverity(recommendation, product);
  const targetPersonas = getTargetPersonas(recommendation);

  const isApplied = recommendation.status === 'APPLIED';
  const isRejected = recommendation.status === 'REJECTED';
  const isProposed = recommendation.status === 'PROPOSED';

  const frictionCount = Number(recommendation.action_data?.friction_count) || 1;

  const handleStatusUpdate = async (newStatus: string) => {
    setUpdating(true);
    try {
      await onStatusChange(recommendation.id, newStatus);
    } finally {
      setUpdating(false);
    }
  };

  const formatPrice = (priceMinor: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(priceMinor / 100);
  };

  return (
    <Card
      className={`flex flex-col justify-between border-l-4 transition-all hover:shadow-md ${
        isApplied
          ? 'border-l-[var(--rzp-success)] bg-green-50/10'
          : isRejected
          ? 'border-l-gray-400 bg-gray-50/30 opacity-75'
          : severity === 'CRITICAL'
          ? 'border-l-[var(--rzp-danger)]'
          : severity === 'HIGH'
          ? 'border-l-[var(--rzp-warning)]'
          : 'border-l-[var(--rzp-ai)]'
      }`}
    >
      <CardHeader className="pb-3 pt-4 px-5">
        {/* Top Badges Row */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${bgClass} ${colorClass} ${borderClass}`}>
              {category}
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${severityBadgeClass}`}>
              {severityLabel}
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            {isApplied && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold text-[var(--rzp-success)] bg-[var(--rzp-success-soft)] border border-[var(--rzp-success)]">
                <CheckCircle2 className="h-3 w-3 mr-1" /> Applied to Catalogue
              </span>
            )}
            {isRejected && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold text-gray-600 bg-gray-100 border border-gray-300">
                <XCircle className="h-3 w-3 mr-1" /> Rejected
              </span>
            )}
            {isProposed && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold text-[var(--rzp-warning)] bg-[var(--rzp-warning-soft)] border border-[var(--rzp-warning)]">
                <Clock className="h-3 w-3 mr-1" /> Action Required
              </span>
            )}
          </div>
        </div>

        {/* Title */}
        <h3 className="text-base font-bold text-[var(--rzp-text)] tracking-tight mt-2.5">
          {recommendation.title}
        </h3>
      </CardHeader>

      <CardContent className="px-5 py-2 space-y-4 text-xs">
        {/* Section 1: Problem & Impact Summary ("Why it matters") */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 bg-[var(--rzp-surface-subtle)] p-3 rounded-lg border border-[var(--rzp-border)]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block">
              Relative Severity
            </span>
            <div className="text-base font-extrabold text-[var(--rzp-text)] flex items-center mt-0.5">
              <TrendingUp className={`h-4 w-4 mr-1 inline ${severity === 'CRITICAL' ? 'text-red-600' : severity === 'HIGH' ? 'text-amber-600' : 'text-blue-600'}`} />
              <span className={severity === 'CRITICAL' ? 'text-red-600' : severity === 'HIGH' ? 'text-amber-600' : 'text-blue-600'}>
                {severityLabel}
              </span>
            </div>
            <p className="text-[11px] text-[var(--rzp-text-secondary)] mt-0.5">
              Aggregated merchant impact
            </p>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block">
              Empirical Evidence
            </span>
            <div className="text-base font-extrabold text-[var(--rzp-text)] flex items-center mt-0.5">
              <Sparkles className="h-4 w-4 mr-1 text-[var(--rzp-ai)] inline" />
              {frictionCount} Drop-offs
            </div>
            <p className="text-[11px] text-[var(--rzp-text-secondary)] mt-0.5">
              {recommendation.action_data?.total_overall_frictions 
                ? `${((frictionCount / recommendation.action_data.total_overall_frictions) * 100).toFixed(1)}% of observed friction`
                : 'Recorded in latest simulation'}
            </p>
          </div>
        </div>

        {/* Section 2: Affected Product */}
        <div className="border border-[var(--rzp-border)] rounded-lg p-3 bg-white space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] flex items-center">
              <Package className="h-3.5 w-3.5 mr-1 text-[var(--rzp-primary)]" /> Affected Catalogue Item
            </span>
            {product && (
              <span className="text-[10px] font-medium text-gray-500 font-mono">
                ID: {product.id.slice(0, 8)}...
              </span>
            )}
          </div>

          {product ? (
            <div className="space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-sm text-[var(--rzp-text)] line-clamp-1">
                  {product.name}
                </span>
                <span className="font-bold text-xs text-[var(--rzp-primary)] shrink-0 font-mono">
                  {formatPrice(product.price)}
                </span>
              </div>
              
              <div className="flex flex-wrap items-center gap-3 text-[11px] text-[var(--rzp-text-secondary)]">
                <span>Category: <strong className="text-[var(--rzp-text)]">{product.category}</strong></span>
                <span>•</span>
                <span>
                  Inventory:{' '}
                  <strong className={product.inventory && product.inventory.available_quantity > 0 ? 'text-[var(--rzp-success)]' : 'text-[var(--rzp-danger)] font-bold'}>
                    {product.inventory ? `${product.inventory.available_quantity} in stock` : '0 in stock'}
                  </strong>
                </span>
                {product.metadata?.delivery_days && (
                  <>
                    <span>•</span>
                    <span>Delivery: <strong>{product.metadata.delivery_days} days</strong></span>
                  </>
                )}
                {product.metadata?.return_days && (
                  <>
                    <span>•</span>
                    <span>Return: <strong>{product.metadata.return_days} days</strong></span>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="text-xs text-gray-500 italic">
              Product details linked via ID: {recommendation.product_id || 'Catalogue wide'}
            </div>
          )}
        </div>

        {/* Section 3: Affected Buyer Persona / Scenarios */}
        <div className="space-y-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block">
            Affected Buyer Persona Segments
          </span>
          <div className="space-y-1">
            {targetPersonas.map((persona, pIdx) => (
              <div
                key={pIdx}
                className="flex items-center justify-between p-2 rounded-md bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border)] text-[11px]"
              >
                <div className="flex items-center space-x-2 min-w-0">
                  <span className="text-sm">{persona.icon}</span>
                  <span className="font-semibold text-[var(--rzp-text)] truncate">
                    {persona.name}
                  </span>
                </div>
                <span className="text-[10px] text-[var(--rzp-text-muted)] text-right shrink-0 ml-2">
                  {persona.description}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: Recommended Action & State Transition */}
        <div className="p-3 bg-purple-50/60 border border-purple-200 rounded-lg space-y-2">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-ai)] block">
              Recommended Operational Action
            </span>
            <p className="text-xs font-semibold text-[var(--rzp-text)]">
              {recommendation.action_data?.suggested_change || recommendation.title}
            </p>
          </div>
          
          {(recommendation.action_data?.before_state_description || recommendation.action_data?.after_state_description) && (
            <div className="pt-2 mt-1 border-t border-purple-100 flex items-center justify-between text-[11px] font-medium">
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-gray-500 mb-0.5">Before</span>
                <span className="text-gray-600 px-2 py-0.5 bg-white border border-gray-200 rounded text-center">
                  {recommendation.action_data.before_state_description || "Current state"}
                </span>
              </div>
              <div className="flex-1 flex items-center justify-center text-purple-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-gray-500 mb-0.5">Proposed</span>
                <span className="text-[var(--rzp-primary)] px-2 py-0.5 bg-white border border-purple-200 rounded text-center font-bold">
                  {recommendation.action_data.after_state_description || "Updated state"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Section 5: Relevant Simulation Evidence */}
        <div className="p-2.5 bg-gray-50 rounded-md border border-gray-200 text-[11px] text-[var(--rzp-text-secondary)] space-y-1">
          <span className="font-semibold text-[var(--rzp-text)] block text-[10px] uppercase tracking-wider">
            Empirical Simulation Evidence:
          </span>
          <p className="italic text-gray-700 leading-relaxed">
            "{recommendation.reason}"
          </p>
        </div>
      </CardContent>

      {/* Card Action Footer */}
      <CardFooter className="px-5 py-3 border-t border-[var(--rzp-border)] bg-[var(--rzp-surface-subtle)] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 mt-2">
        <div className="flex items-center space-x-2">
          {isProposed ? (
            <>
              <Button
                variant="primary"
                size="sm"
                isLoading={updating}
                onClick={() => handleStatusUpdate('APPLIED')}
                className="text-xs font-semibold shadow-2xs"
              >
                <Check className="h-3.5 w-3.5 mr-1" /> Accept & Apply
              </Button>
              <Button
                variant="outline"
                size="sm"
                isLoading={updating}
                onClick={() => handleStatusUpdate('REJECTED')}
                className="text-xs text-gray-600 hover:text-red-700 hover:border-red-200 hover:bg-red-50"
              >
                <XCircle className="h-3.5 w-3.5 mr-1" /> Reject
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              isLoading={updating}
              onClick={() => handleStatusUpdate('PROPOSED')}
              className="text-xs text-gray-600 hover:bg-gray-100"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" /> Reset to Proposed
            </Button>
          )}
        </div>

        <Button
          variant="ai"
          size="sm"
          onClick={() => onTestWithWhatIf(recommendation)}
          className="text-xs font-semibold whitespace-nowrap"
        >
          <TestTube className="h-3.5 w-3.5 mr-1.5" /> Test in What-If <ArrowRight className="h-3 w-3 ml-1" />
        </Button>
      </CardFooter>
    </Card>
  );
};
