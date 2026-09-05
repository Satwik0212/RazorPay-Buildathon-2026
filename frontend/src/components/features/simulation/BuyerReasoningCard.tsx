import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldCheck,
  Scale,
  Award,
  Layers,
  ArrowRight,
  Info
} from 'lucide-react';
import type { SimulationResultItem, Product } from '../../../types';
import {
  formatPrice,
  type IntentSummary,
  type PersonaMeta,
  type ScoreComponent,
  type PositiveSignal,
  type FrictionSignal
} from './simulationLogHelpers';
import { Link } from 'react-router-dom';

interface BuyerReasoningCardProps {
  item: SimulationResultItem;
  productsMap: Record<string, Product>;
  intentSummary: IntentSummary;
  personaMeta: PersonaMeta;
  scoreComponents: ScoreComponent[];
  positiveSignals: PositiveSignal[];
  frictionSignals: FrictionSignal[];
}

/**
 * Generate high-contrast text meter representation: e.g. ████████░░ (8/10)
 */
const renderAsciiMeter = (score: number, totalBlocks: number = 10): string => {
  const filled = Math.min(Math.max(Math.round(score * totalBlocks), 0), totalBlocks);
  const empty = totalBlocks - filled;
  return '█'.repeat(filled) + '░'.repeat(empty);
};

export const BuyerReasoningCard: React.FC<BuyerReasoningCardProps> = ({
  item,
  productsMap,
  intentSummary,
  personaMeta,
  scoreComponents,
  positiveSignals,
  frictionSignals,
}) => {
  const [showFormulaDetails, setShowFormulaDetails] = useState(false);

  const isMatched = Boolean(item.constraints_satisfied && item.selected_product_id);
  const selectedProduct = item.selected_product_id ? productsMap[item.selected_product_id] : null;
  const winnerRanking =
    (item.rankings || []).find((r) => r.product_id === item.selected_product_id) ||
    (item.rankings || [])[0];

  const productName =
    selectedProduct?.name ||
    item.selected_product_name ||
    winnerRanking?.product_name ||
    (item.selected_product_id ? `Product (${item.selected_product_id.slice(0, 8)})` : 'Selected Product');

  const productPrice =
    selectedProduct?.price ??
    item.selected_product_price ??
    winnerRanking?.price;

  const productCategory =
    selectedProduct?.category ||
    item.selected_product_category ||
    winnerRanking?.category ||
    intentSummary.category ||
    'Catalogue Item';

  const totalEvaluated = item.total_products_evaluated ?? (item.rankings || []).length;
  const totalDisqualified = item.total_disqualified ?? (item.rankings || []).filter(r => r.passed === false).length;

  // Rejection frictions
  const hardFrictions = frictionSignals.filter(f => f.type === 'HARD_BLOCKER');

  // Dominant friction code from item
  const primaryFrictionCode =
    (item.frictions && item.frictions.length > 0 && item.frictions[0].reason) ||
    (hardFrictions.length > 0 ? hardFrictions[0].reason : 'NO_MATCHING_PRODUCTS');

  return (
    <div className={`rounded-xl border shadow-sm overflow-hidden transition-all duration-200 ${
      isMatched
        ? 'border-emerald-200 bg-gradient-to-b from-emerald-50/30 via-white to-white'
        : 'border-rose-200 bg-gradient-to-b from-rose-50/40 via-white to-white'
    }`}>
      {/* ── CARD HEADER BANNER: 5-SECOND SUMMARY ── */}
      <div className={`px-5 py-4 border-b flex flex-col md:flex-row md:items-center justify-between gap-3 ${
        isMatched ? 'border-emerald-100 bg-emerald-50/60' : 'border-rose-100 bg-rose-50/70'
      }`}>
        {/* Title & Badge */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 border ${
              isMatched
                ? 'bg-emerald-100/80 text-emerald-800 border-emerald-300'
                : 'bg-rose-100/90 text-rose-900 border-rose-300'
            }`}>
              {isMatched ? (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  WHY THIS BUYER CHOSE THIS PRODUCT
                </>
              ) : (
                <>
                  <XCircle className="h-3.5 w-3.5 text-rose-600" />
                  WHY THIS BUYER WALKED AWAY (DISQUALIFIED)
                </>
              )}
            </span>

            <span className={`px-2 py-0.5 rounded text-xs font-semibold border flex items-center gap-1 ${personaMeta.badgeBg} ${personaMeta.badgeText} ${personaMeta.badgeBorder}`}>
              <span>{personaMeta.icon}</span>
              <span>{personaMeta.displayName}</span>
            </span>

            <span className="text-xs text-gray-500 font-medium">
              ({personaMeta.variantLabel})
            </span>
          </div>

          <p className="text-xs text-gray-600 font-medium">
            {isMatched ? (
              <>
                Simulated buyer preferences & weights deterministically selected{' '}
                <strong className="text-gray-900">{productName}</strong> as Rank #1 of{' '}
                <strong className="text-emerald-700">{totalEvaluated.toLocaleString()}</strong> active catalogue candidates.
              </>
            ) : (
              <>
                All <strong className="text-rose-700">{totalEvaluated.toLocaleString()}</strong> evaluated catalogue products were disqualified by hard gatekeeper constraints.
              </>
            )}
          </p>
        </div>

        {/* Overall Score / Outcome Pill */}
        <div className="flex items-center gap-3 self-start md:self-auto shrink-0">
          {isMatched ? (
            <div className="text-right bg-white px-3.5 py-2 rounded-lg border border-emerald-200 shadow-xs">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
                Composite Match
              </span>
              <span className="text-xl font-mono font-black text-emerald-700 leading-tight">
                {(item.score * 100).toFixed(1)}%
              </span>
            </div>
          ) : (
            <div className="text-right bg-white px-3 py-1.5 rounded-lg border border-rose-200 shadow-xs">
              <span className="text-[10px] font-bold text-rose-500 uppercase tracking-wider block">
                Disqualification Gate
              </span>
              <span className="text-xs font-mono font-bold text-rose-700 px-2 py-0.5 bg-rose-50 rounded inline-block mt-0.5 border border-rose-200">
                {primaryFrictionCode}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="p-5 space-y-6">
        {/* ── CASE 1: MATCHED WINNER EXPLAINABILITY ── */}
        {isMatched && (
          <>
            {/* Winner Product Overview Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-3.5 bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border)] rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-base shadow-xs shrink-0">
                  #1
                </div>
                <div>
                  <h4 className="font-bold text-sm text-[var(--rzp-text)] leading-snug">
                    {productName}
                  </h4>
                  <div className="flex items-center gap-2 text-xs text-[var(--rzp-text-muted)] mt-0.5 flex-wrap">
                    <span className="font-medium text-gray-700 bg-white px-2 py-0.5 rounded border border-gray-200">
                      {productCategory}
                    </span>
                    {productPrice !== undefined && productPrice !== null && (
                      <span className="font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {formatPrice(productPrice)}
                      </span>
                    )}
                    {intentSummary.maxBudget && (
                      <span>
                        Budget Ceiling: <strong>{formatPrice(intentSummary.maxBudget)}</strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-gray-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
                <span>Passed all hard budget, inventory & deadline gates</span>
              </div>
            </div>

            {/* Visual Dimension Meter Bars */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-[var(--rzp-text)] uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="h-3.5 w-3.5 text-[var(--rzp-primary)]" />
                    Deterministic Dimension Breakdown
                  </h4>
                  <p className="text-[11px] text-gray-500">
                    Normalized scores [0.0 – 1.0] weighted by this buyer's priorities.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowFormulaDetails(!showFormulaDetails)}
                  className="text-[11px] text-[var(--rzp-primary)] hover:underline font-semibold flex items-center gap-0.5 cursor-pointer"
                >
                  <Info className="h-3 w-3" />
                  {showFormulaDetails ? 'Hide details' : 'How this is computed'}
                </button>
              </div>

              {/* Formula explanation note (collapsible) */}
              {showFormulaDetails && (
                <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-lg text-xs text-blue-900 space-y-1">
                  <p className="font-bold flex items-center gap-1">
                    <Sparkles className="h-3.5 w-3.5 text-blue-600" /> Grounded Scoring Algorithm
                  </p>
                  <p className="text-[11px] text-blue-800">
                    Overall Score = ∑ (Component Score × Dimension Weight) / Total Weight.
                    Scores are computed directly from catalogue specifications, delivery timeline, pricing headroom, and warranty coverage with float64 precision.
                  </p>
                </div>
              )}

              {/* The Meter Bars Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {scoreComponents.map((c) => {
                  const percentage = Math.round(c.score * 100);
                  const weightPct = Math.round(c.weight * 100);
                  const asciiMeter = renderAsciiMeter(c.score, 10);

                  // Color coding based on strength
                  let meterColor = 'bg-emerald-600';
                  let badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                  if (c.score < 0.40) {
                    meterColor = 'bg-rose-500';
                    badgeBg = 'bg-rose-50 text-rose-800 border-rose-200';
                  } else if (c.score < 0.70) {
                    meterColor = 'bg-amber-500';
                    badgeBg = 'bg-amber-50 text-amber-800 border-amber-200';
                  }

                  return (
                    <div
                      key={c.key}
                      className="p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors shadow-2xs space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-xs text-gray-800">{c.label}</span>
                          {weightPct > 0 && (
                            <span className="text-[10px] font-semibold text-gray-500 bg-gray-100 px-1.5 py-0.2 rounded">
                              Weight: {weightPct}%
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-[11px] text-gray-400 hidden sm:inline select-none">
                            {asciiMeter}
                          </span>
                          <span className={`text-xs font-mono font-bold px-1.5 py-0.2 rounded border ${badgeBg}`}>
                            {percentage}%
                          </span>
                        </div>
                      </div>

                      {/* Visual Meter Bar */}
                      <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${meterColor}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>

                      {/* Grounded Evidence String */}
                      <p className="text-[11px] text-gray-500 font-medium truncate" title={c.evidence}>
                        {c.evidence}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Strongest Positive Factors (Why It Won) */}
            {positiveSignals.length > 0 && (
              <div className="space-y-2.5 pt-2 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                    <Award className="h-3.5 w-3.5 text-emerald-600" />
                    Strongest Positive Factors (Decision Drivers)
                  </h4>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {positiveSignals.length} verified signals
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {positiveSignals.map((sig, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-emerald-50/40 border border-emerald-200/80 rounded-lg flex items-start gap-2.5"
                    >
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <div className="space-y-0.5">
                        <span className="text-xs font-bold text-emerald-950 block">
                          {sig.title}
                        </span>
                        <p className="text-[11px] text-emerald-800 leading-relaxed">
                          {sig.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* ── CASE 2: REJECTED / DISQUALIFIED BUYER EXPLAINABILITY ── */}
        {!isMatched && (
          <div className="space-y-4">
            {/* Primary Root Cause Callout */}
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg space-y-2">
              <div className="flex items-start gap-2.5">
                <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-rose-900">
                    Hard Disqualification: {primaryFrictionCode}
                  </h4>
                  <p className="text-xs text-rose-800 leading-relaxed">
                    {item.explanation ||
                      `The buyer persona rejected all ${totalEvaluated} candidate catalogue items because mandatory purchasing constraints were not met.`}
                  </p>
                </div>
              </div>

              {/* Key constraint summary */}
              <div className="pt-2 border-t border-rose-200/60 flex flex-wrap gap-2 text-xs">
                {intentSummary.maxBudget && (
                  <span className="px-2 py-0.5 bg-white text-rose-800 rounded border border-rose-200 font-medium">
                    Budget Constraint: <strong>≤ {formatPrice(intentSummary.maxBudget)}</strong>
                  </span>
                )}
                {intentSummary.deliveryDeadlineDays && (
                  <span className="px-2 py-0.5 bg-white text-rose-800 rounded border border-rose-200 font-medium">
                    Delivery Deadline: <strong>≤ {intentSummary.deliveryDeadlineDays} days</strong>
                  </span>
                )}
                {intentSummary.requirements.length > 0 && (
                  <span className="px-2 py-0.5 bg-white text-rose-800 rounded border border-rose-200 font-medium">
                    Required Features: <strong>{intentSummary.requirements.join(', ')}</strong>
                  </span>
                )}
              </div>
            </div>

            {/* Canonical Friction Breakdown */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1.5">
                <XCircle className="h-3.5 w-3.5 text-rose-600" />
                Detected Hard Blocking Frictions
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {hardFrictions.length > 0 ? (
                  hardFrictions.map((f, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white border border-rose-200 rounded-lg space-y-1 shadow-2xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                          {f.reason}
                        </span>
                        <span className="text-[10px] font-bold text-rose-600 bg-rose-100 px-1.5 py-0.2 rounded uppercase">
                          Hard Gate
                        </span>
                      </div>
                      <h5 className="font-bold text-xs text-gray-900">{f.title}</h5>
                      <p className="text-[11px] text-gray-600 leading-snug">{f.description}</p>
                    </div>
                  ))
                ) : (
                  <div className="p-3 bg-white border border-gray-200 rounded-lg text-xs text-gray-500 italic">
                    Candidate items failed baseline eligibility gates.
                  </div>
                )}
              </div>
            </div>

            {/* Candidate Funnel Toll */}
            <div className="p-3.5 bg-gray-50 border border-gray-200 rounded-lg flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-indigo-600 shrink-0" />
                <span className="text-gray-700">
                  <strong>{totalDisqualified.toLocaleString()}</strong> of <strong>{totalEvaluated.toLocaleString()}</strong> active catalogue products failed gatekeeper checks.
                </span>
              </div>
              <Link to="/optimization?step=action">
                <span className="font-semibold text-[var(--rzp-primary)] hover:underline flex items-center gap-1 cursor-pointer">
                  View Actionable Fixes in Step 4 <ArrowRight className="h-3 w-3" />
                </span>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
