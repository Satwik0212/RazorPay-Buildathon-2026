import React from 'react';
import { Sparkles, TrendingUp, Play } from 'lucide-react';
import { Button } from '../../ui/Button';
import type { Recommendation, Product } from '../../../types';
import { getRecommendationCategory } from './recommendationHelpers';

interface RecommendationSummaryBannerProps {
  recommendations: Recommendation[];
  products: Product[];
  onRunSimulation?: () => void;
}

export const RecommendationSummaryBanner: React.FC<RecommendationSummaryBannerProps> = ({
  recommendations,
  products,
  onRunSimulation
}) => {
  const totalRecs = recommendations.length;
  const proposedCount = recommendations.filter(r => r.status === 'PROPOSED').length;
  const appliedCount = recommendations.filter(r => r.status === 'APPLIED').length;
  const rejectedCount = recommendations.filter(r => r.status === 'REJECTED').length;

  const totalFrictionEvents = recommendations.reduce((sum, r) => {
    const count = Number(r.action_data?.friction_count) || 1;
    return sum + count;
  }, 0);

  const affectedProductIds = new Set(recommendations.map(r => r.product_id).filter(Boolean));
  const affectedProductCount = affectedProductIds.size;

  const activeRecs = recommendations.filter(r => r.status === 'PROPOSED');
  const avgImpact = activeRecs.length > 0
    ? (activeRecs.reduce((sum, r) => sum + (r.expected_simulated_impact || 0), 0) / activeRecs.length)
    : 0;

  const avgConfidence = recommendations.length > 0
    ? (recommendations.reduce((sum, r) => sum + (r.confidence || 0), 0) / recommendations.length)
    : 0;

  const categoryCounts: Record<string, number> = {};
  recommendations.forEach(r => {
    const { category } = getRecommendationCategory(r);
    categoryCounts[category] = (categoryCounts[category] || 0) + 1;
  });

  const scenarioCount = recommendations.length > 0 
    ? (Number(recommendations[0].action_data?.scenario_count) || 0) 
    : 0;

  return (
    <div className="bg-gradient-to-br from-[var(--rzp-surface)] via-white to-purple-50/30 rounded-xl border border-[var(--rzp-border)] p-6 shadow-sm space-y-5">
      {/* Top Headline */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)] border border-[var(--rzp-ai)]">
              <Sparkles className="h-3 w-3 mr-1" /> Agentic Intelligence
            </span>
            <span className="text-xs text-[var(--rzp-text-muted)] font-medium">
              Evidence-Backed Catalogue Diagnostics
            </span>
          </div>

          <h2 className="text-xl font-bold text-[var(--rzp-text)] tracking-tight mt-1">
            {totalRecs > 0 ? (
              <>
                {scenarioCount > 0 ? (
                  <>
                    <span className="text-[var(--rzp-danger)] underline decoration-red-300 font-extrabold">
                      {totalFrictionEvents} friction events detected
                    </span>{' '}
                    across {scenarioCount} buyer scenarios, affecting {affectedProductCount} candidate {affectedProductCount === 1 ? 'product' : 'products'}.
                  </>
                ) : (
                  <>
                    AI buyers encountered{' '}
                    <span className="text-[var(--rzp-danger)] underline decoration-red-300 font-extrabold">
                      {totalFrictionEvents} friction-related drop-offs
                    </span>{' '}
                    across {affectedProductCount} catalogue {affectedProductCount === 1 ? 'product' : 'products'}.
                  </>
                )}
              </>
            ) : (
              'Catalogue Optimization & Actionable Intelligence'
            )}
          </h2>
          <p className="text-xs text-[var(--rzp-text-secondary)] max-w-3xl">
            {totalRecs > 0
              ? `${proposedCount} aggregated recommendations are currently proposed to eliminate buyer constraint rejections.`
              : 'Run synthetic buyer simulations to diagnose catalog drop-offs and generate evidence-backed recommendations.'}
          </p>
        </div>

        {onRunSimulation && (
          <div className="shrink-0">
            <Button
              variant="ai"
              size="sm"
              onClick={onRunSimulation}
              className="whitespace-nowrap shadow-sm font-semibold"
            >
              <Play className="h-3.5 w-3.5 mr-1.5" /> Re-run Simulation
            </Button>
          </div>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[var(--rzp-border)]">
        {/* Total Friction Signals */}
        <div className="p-3.5 rounded-lg bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border)]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block">
            Total Friction Events
          </span>
          <div className="text-2xl font-black text-[var(--rzp-danger)] mt-0.5">
            {totalFrictionEvents}
          </div>
          <span className="text-[11px] text-[var(--rzp-text-secondary)]">
            Recorded across {scenarioCount > 0 ? `${scenarioCount} scenarios` : 'simulation'}
          </span>
        </div>

        {/* Proposed Interventions */}
        <div className="p-3.5 rounded-lg bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border)]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block">
            Aggregated Recommendations
          </span>
          <div className="text-2xl font-black text-[var(--rzp-primary)] mt-0.5">
            {proposedCount} <span className="text-xs font-normal text-gray-500">/ {totalRecs}</span>
          </div>
          <div className="flex items-center space-x-1.5 text-[10px] font-medium text-[var(--rzp-text-muted)]">
            <span className="text-[var(--rzp-success)] font-semibold">{appliedCount} applied</span>
            <span>•</span>
            <span className="text-gray-500">{rejectedCount} rejected</span>
          </div>
        </div>
      </div>

      {/* Category Breakdown Chips */}
      {Object.keys(categoryCounts).length > 0 && (
        <div className="pt-1 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-[11px] font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider mr-1">
            Friction Breakdown:
          </span>
          {Object.entries(categoryCounts).map(([cat, count]) => (
            <span
              key={cat}
              className="inline-flex items-center px-2.5 py-1 rounded-full font-medium bg-white border border-[var(--rzp-border)] text-[var(--rzp-text-secondary)] text-[11px] shadow-2xs"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--rzp-primary)] mr-1.5"></span>
              {cat}: <strong className="ml-1 text-[var(--rzp-text)]">{count}</strong>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
