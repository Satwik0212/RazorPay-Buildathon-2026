import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Target,
  ShieldCheck,
  Filter,
  Trophy,
  BarChart3,
  Check,
  AlertTriangle,
  Info,
  Layers,
  Package,
  Clock,
  Tag
} from 'lucide-react';
import type { SimulationResultItem, Product } from '../../../types';
import {
  formatPrice,
  getPersonaMeta,
  extractIntentSummary,
  evaluateHardConstraints,
  calculateScoreComponents,
  getPositiveSignals,
  getFrictionSignals,
} from './simulationLogHelpers';
import { FrictionExplorer } from './FrictionExplorer';
import { BuyerReasoningCard } from './BuyerReasoningCard';

interface ScenarioDecisionLogProps {
  item: SimulationResultItem;
  index?: number;
  productsMap: Record<string, Product>;
  isExpandedDefault?: boolean;
}

export const ScenarioDecisionLog: React.FC<ScenarioDecisionLogProps> = ({
  item,
  index = 0,
  productsMap,
  isExpandedDefault = false,
}) => {
  const [expanded, setExpanded] = useState(isExpandedDefault);
  const [showForensicDetails, setShowForensicDetails] = useState(false);

  const personaMeta = getPersonaMeta(item.persona_name);
  const intentSummary = extractIntentSummary(item);
  const selectedProduct = item.selected_product_id ? productsMap[item.selected_product_id] : null;
  const winnerRanking =
    (item.rankings || []).find((r) => r.product_id === item.selected_product_id) ||
    (item.rankings || [])[0];
  const winnerName =
    selectedProduct?.name ||
    winnerRanking?.product_name ||
    (item.selected_product_id ? `Product (${item.selected_product_id.slice(0, 8)})` : 'Selected Product');

  const hardConstraints = evaluateHardConstraints(item, intentSummary, selectedProduct);
  const scoreComponents = calculateScoreComponents(item, intentSummary, selectedProduct);
  const positiveSignals = getPositiveSignals(item, intentSummary, selectedProduct);
  const frictionSignals = getFrictionSignals(item, intentSummary);

  const isMatched = Boolean(item.constraints_satisfied && item.selected_product_id);

  // Filter rankings into passed and disqualified
  const passedRankings = (item.rankings || []).filter((r) => r.passed !== false);
  const disqualifiedRankings = (item.rankings || []).filter((r) => r.passed === false);

  return (
    <div
      className={`border rounded-xl transition-all duration-200 shadow-sm ${
        isMatched
          ? 'border-[var(--rzp-border)] bg-white hover:border-gray-300'
          : 'border-red-200 bg-red-50/15 hover:border-red-300'
      }`}
    >
      {/* Header Bar */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-4 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-3 select-none"
      >
        {/* Left: Persona & Outcome */}
        <div className="flex items-center space-x-3 flex-wrap gap-y-2">
          <span className="text-xs font-mono font-bold text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
            #{index !== undefined ? index + 1 : 1}
          </span>

          <span
            className={`px-2.5 py-1 rounded-md text-xs font-semibold border flex items-center gap-1.5 ${personaMeta.badgeBg} ${personaMeta.badgeText} ${personaMeta.badgeBorder}`}
          >
            <span>{personaMeta.icon}</span>
            <span>{personaMeta.displayName}</span>
          </span>

          <span className="text-xs text-[var(--rzp-text-muted)] font-medium bg-gray-50 border border-gray-200 px-2 py-0.5 rounded">
            {personaMeta.variantLabel}
          </span>

          {/* Product Match Title */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-[var(--rzp-text)]">
              {isMatched ? winnerName : 'All Products Disqualified'}
            </span>
            {isMatched && selectedProduct?.price !== undefined && selectedProduct?.price !== null && (
              <span className="text-xs text-[var(--rzp-text-muted)] font-medium">
                ({formatPrice(selectedProduct.price)})
              </span>
            )}
          </div>
        </div>

        {/* Right: Score Pill & Toggle */}
        <div className="flex items-center space-x-3 self-end md:self-auto">
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full flex items-center border ${
              isMatched
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-red-50 text-red-700 border-red-200'
            }`}
          >
            {isMatched ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-emerald-600" /> Match Score: {(item.score * 100).toFixed(1)}%
              </>
            ) : (
              <>
                <XCircle className="h-3.5 w-3.5 mr-1 text-red-600" /> Constraint Rejection
              </>
            )}
          </span>

          <button
            type="button"
            className="p-1 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
            aria-label={expanded ? 'Collapse scenario details' : 'Expand scenario details'}
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Summary Teaser when collapsed */}
      {!expanded && (
        <div className="px-4 pb-3 pt-0 text-xs text-[var(--rzp-text-secondary)] flex flex-wrap items-center justify-between gap-2 border-t border-gray-100/80 mt-1">
          <p className="truncate max-w-2xl text-[var(--rzp-text-muted)]">
            {item.explanation}
          </p>
          <div className="flex items-center gap-2">
            {isMatched ? (
              <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded flex items-center">
                <Check className="h-3 w-3 mr-1" /> {positiveSignals.length} Positive Evidence Signals
              </span>
            ) : (
              <span className="text-[11px] font-medium text-red-700 bg-red-50 px-2 py-0.5 rounded flex items-center">
                <AlertTriangle className="h-3 w-3 mr-1" /> {frictionSignals.length} Friction Signals
              </span>
            )}
          </div>
        </div>
      )}

      {/* Expanded Explainability & Decision View */}
      {expanded && (
        <div className="p-4 pt-3 border-t border-[var(--rzp-border)] space-y-4 text-xs animate-in fade-in duration-200">

          {/* PRIMARY EXPLAINABILITY CARD: 5-SECOND DEMO VIEW */}
          <BuyerReasoningCard
            item={item}
            productsMap={productsMap}
            intentSummary={intentSummary}
            personaMeta={personaMeta}
            scoreComponents={scoreComponents}
            positiveSignals={positiveSignals}
            frictionSignals={frictionSignals}
          />

          {/* COLLAPSIBLE FORENSIC PIPELINE INSPECTION */}
          <div className="border border-gray-200 rounded-xl overflow-hidden bg-white shadow-2xs">
            <button
              type="button"
              onClick={() => setShowForensicDetails(!showForensicDetails)}
              className="w-full p-3.5 bg-gray-50/90 hover:bg-gray-100/90 text-left flex items-center justify-between transition-colors select-none cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-gray-500" />
                <span className="text-xs font-bold text-gray-700">
                  {showForensicDetails
                    ? 'Hide Detailed Forensic Pipeline'
                    : 'Inspect Detailed Forensic Pipeline (Gatekeepers, Candidate Funnel & Friction Explorer)'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-gray-400 font-medium hidden sm:inline">
                  {showForensicDetails ? 'Collapse raw engine checks' : 'Deep dive engine steps'}
                </span>
                {showForensicDetails ? <ChevronUp className="h-4 w-4 text-gray-500" /> : <ChevronDown className="h-4 w-4 text-gray-500" />}
              </div>
            </button>

            {showForensicDetails && (
              <div className="p-4 space-y-6 border-t border-gray-200 bg-white animate-in fade-in duration-200">
                {/* LAYER 1: BUYER INTENT & PERSONA PROFILE */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                    <h4 className="font-bold text-[var(--rzp-text)] flex items-center text-xs uppercase tracking-wider">
                      <Target className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-ai)]" /> 1. Buyer Persona & Intent Configuration
                    </h4>
                    <span className="text-[11px] text-[var(--rzp-text-muted)]">Input Condition</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-[var(--rzp-surface-subtle)] p-3 rounded-lg border border-[var(--rzp-border)]">
                    {/* Intent Ceiling */}
                    <div>
                      <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Max Budget Ceiling</span>
                      <span className="text-xs font-semibold text-[var(--rzp-text)] block mt-0.5">
                        {intentSummary.maxBudgetText}
                      </span>
                    </div>

                    {/* Delivery Deadline */}
                    <div>
                      <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Delivery Timeline</span>
                      <span className="text-xs font-semibold text-[var(--rzp-text)] block mt-0.5">
                        {intentSummary.deliveryDeadlineToText}
                      </span>
                    </div>

                    {/* Mandatory Reqs */}
                    <div>
                      <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Mandatory Features</span>
                      <span className="text-xs font-semibold text-[var(--rzp-text)] block mt-0.5">
                        {intentSummary.requirements.length > 0 ? intentSummary.requirements.join(', ') : 'No mandatory requirement'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* LAYER 2: HARD CONSTRAINTS EVALUATION */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                    <h4 className="font-bold text-[var(--rzp-text)] flex items-center text-xs uppercase tracking-wider">
                      <ShieldCheck className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-primary)]" /> 2. Hard Disqualification Filters
                    </h4>
                    <span className="text-[11px] text-[var(--rzp-text-muted)]">Gatekeeper Checks</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
                    {hardConstraints.map((chk) => (
                      <div
                        key={chk.id}
                        className={`p-2.5 rounded-lg border flex flex-col justify-between ${
                          chk.status === 'PASSED'
                            ? 'bg-emerald-50/50 border-emerald-200'
                            : chk.status === 'FAILED'
                            ? 'bg-red-50/60 border-red-200'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-[11px] text-[var(--rzp-text)]">{chk.name}</span>
                            <span
                              className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                                chk.status === 'PASSED'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : chk.status === 'FAILED'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-200 text-gray-700'
                              }`}
                            >
                              {chk.status}
                            </span>
                          </div>
                          <p className="text-[11px] text-[var(--rzp-text-secondary)] font-medium">
                            {chk.summary}
                          </p>
                        </div>
                        <p className="text-[10px] text-[var(--rzp-text-muted)] mt-1 pt-1 border-t border-gray-100">
                          {chk.evidence}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* LAYER 3: CANDIDATE FILTERING (CATALOGUE FUNNEL) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                    <h4 className="font-bold text-[var(--rzp-text)] flex items-center text-xs uppercase tracking-wider">
                      <Filter className="h-3.5 w-3.5 mr-1.5 text-indigo-600" /> 3. Candidate Funnel & Ranking
                    </h4>
                    <span className="text-[11px] text-[var(--rzp-text-muted)]">
                      {item.total_products_evaluated != null ? (
                        <>
                          <span className="font-semibold text-emerald-700">{item.total_eligible ?? passedRankings.length}</span>
                          {' eligible '}
                          <span className="text-gray-400">· </span>
                          <span className="font-semibold text-red-600">{item.total_disqualified ?? disqualifiedRankings.length}</span>
                          {' disqualified'}
                          <span className="text-gray-400"> of </span>
                          <span className="font-semibold">{item.total_products_evaluated}</span>
                          {' evaluated'}
                          {(item.total_eligible ?? passedRankings.length) !== passedRankings.length || (item.total_disqualified ?? disqualifiedRankings.length) !== disqualifiedRankings.length ? (
                            <span className="ml-1 text-[10px] text-gray-400">(showing {passedRankings.length + disqualifiedRankings.length} examples)</span>
                          ) : null}
                        </>
                      ) : (
                        <>{passedRankings.length} of {(item.rankings || []).length} products passed filters</>
                      )}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Passed Candidates */}
                    <div className="p-3 bg-white rounded-lg border border-gray-200 space-y-2">
                      <span className="font-bold text-[11px] text-emerald-700 flex items-center justify-between">
                        <span>Eligible Candidates ({passedRankings.length})</span>
                        <span className="text-[10px] text-gray-400 font-normal">Ranked by score</span>
                      </span>

                      {passedRankings.length > 0 ? (
                        <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                          {passedRankings.map((r) => {
                            const p = productsMap[r.product_id];
                            const isWinner =
                              (r.rank === 1 || r.product_id === item.selected_product_id) && isMatched;
                            const priceToDisplay = p?.price ?? r.price;
                            return (
                              <div
                                key={r.product_id}
                                className={`p-2 rounded border flex items-center justify-between text-xs ${
                                  isWinner
                                    ? 'bg-emerald-50/70 border-emerald-300 font-semibold'
                                    : 'bg-gray-50 border-gray-100'
                                }`}
                              >
                                <div className="flex items-center space-x-2 truncate max-w-[220px]">
                                  <span
                                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                      isWinner ? 'bg-emerald-600 text-white' : 'bg-gray-200 text-gray-700'
                                    }`}
                                  >
                                    #{r.rank}
                                  </span>
                                  <span className="truncate">{p ? p.name : r.product_name || r.product_id}</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  {priceToDisplay !== undefined && priceToDisplay !== null && (
                                    <span className="text-[11px] text-gray-500">{formatPrice(priceToDisplay)}</span>
                                  )}
                                  <span className="font-mono font-bold text-[var(--rzp-primary)]">
                                    {(r.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 italic py-2">No catalogue products passed hard constraints.</p>
                      )}
                    </div>

                    {/* Disqualified Candidates */}
                    <div className="p-3 bg-white rounded-lg border border-gray-200 space-y-2">
                      <span className="font-bold text-[11px] text-red-700 flex items-center justify-between">
                        <span>Disqualified Products ({disqualifiedRankings.length})</span>
                        <span className="text-[10px] text-gray-400 font-normal">Failed hard gates</span>
                      </span>

                      {disqualifiedRankings.length > 0 ? (
                        <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                          {disqualifiedRankings.map((r) => {
                            const p = productsMap[r.product_id];
                            return (
                              <div
                                key={r.product_id}
                                className="p-2 bg-red-50/40 rounded border border-red-100 flex items-center justify-between text-xs"
                              >
                                <span className="truncate max-w-[200px] text-gray-700">
                                  {p ? p.name : r.product_name || r.product_id}
                                </span>
                                <div className="flex items-center gap-1 flex-wrap justify-end">
                                  {(r.frictions || ['DISQUALIFIED']).map((fn, idx) => (
                                    <span
                                      key={idx}
                                      className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-red-100 text-red-800"
                                    >
                                      {fn}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-400 italic py-2">All evaluated catalogue items passed constraints.</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* LAYER 7: MERCHANT FRICTION EXPLORER */}
                {frictionSignals.length > 0 && (
                  <FrictionExplorer
                    signals={frictionSignals}
                    productsMap={productsMap}
                    intentSummary={intentSummary}
                  />
                )}

                {/* Reason Code Tags */}
                {item.reason_codes && item.reason_codes.length > 0 && (
                  <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-[var(--rzp-text-muted)]">
                    <span>Engine Decision Reason Codes:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {item.reason_codes.map((code) => (
                        <span
                          key={code}
                          className="font-mono font-semibold bg-gray-100 text-gray-700 px-2 py-0.5 rounded border border-gray-200"
                        >
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
};
