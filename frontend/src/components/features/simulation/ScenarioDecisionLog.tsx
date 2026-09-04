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

      {/* Expanded 7-Layer Decision Hierarchy */}
      {expanded && (
        <div className="p-4 pt-3 border-t border-[var(--rzp-border)] space-y-6 text-xs animate-in fade-in duration-200">
          
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
                {/* Use backend-provided totals when available (post-truncation-fix).
                    Fall back to item.rankings.length for older results. */}
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
                            {p?.price !== undefined && p.price !== null && (
                              <span className="text-[11px] text-gray-500">{formatPrice(p.price)}</span>
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

          {/* LAYER 4: SELECTED PRODUCT & DECISION HERO */}
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
              <h4 className="font-bold text-[var(--rzp-text)] flex items-center text-xs uppercase tracking-wider">
                <Trophy className="h-3.5 w-3.5 mr-1.5 text-amber-500" /> 4. Evaluation Decision Outcome
              </h4>
              <span className="text-[11px] text-[var(--rzp-text-muted)]">Engine Selection</span>
            </div>

            {isMatched ? (
              <div className="p-3.5 bg-gradient-to-r from-emerald-50/80 via-white to-emerald-50/40 rounded-lg border border-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-base shrink-0">
                    #1
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                      Top Selected Match
                    </span>
                    <h3 className="font-bold text-sm text-[var(--rzp-text)]">{winnerName}</h3>
                    <p className="text-xs text-[var(--rzp-text-muted)]">
                      {selectedProduct?.category
                        ? `Category: ${selectedProduct.category}`
                        : intentSummary.category
                        ? `Category: ${intentSummary.category}`
                        : 'Catalogue Item'}
                      {selectedProduct?.price !== undefined && selectedProduct?.price !== null && (
                        <> • Price: <strong>{formatPrice(selectedProduct.price)}</strong></>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4 self-end sm:self-auto">
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Match Score</span>
                    <span className="text-xl font-bold text-emerald-700">{(item.score * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-3.5 bg-red-50/80 rounded-lg border border-red-200 text-red-900 flex items-start space-x-3">
                <XCircle className="h-5 w-5 text-red-600 mt-0.5 shrink-0" />
                <div>
                  <h4 className="font-bold text-xs text-red-900">Synthetic Buyer Rejected All Candidate Products</h4>
                  <p className="text-xs text-red-700 mt-0.5">
                    {item.explanation || 'No product in your merchant catalogue satisfied this buyer persona\'s hard constraints.'}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* LAYER 5: SCORE BREAKDOWN / COMPONENT ANALYSIS */}
          {scoreComponents.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                <h4 className="font-bold text-[var(--rzp-text)] flex items-center text-xs uppercase tracking-wider">
                  <BarChart3 className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-primary)]" /> 5. Weighted Score Components
                </h4>
                <span className="text-[11px] text-[var(--rzp-text-muted)]">
                  Formula: ∑ (Component Score × Persona Weight)
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {scoreComponents.map((c) => (
                  <div key={c.key} className="p-2.5 bg-gray-50 border border-gray-200 rounded-lg space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-[var(--rzp-text)] truncate">{c.label}</span>
                      <span className="font-mono font-bold text-[var(--rzp-primary)] text-[11px]">
                        {(c.score * 100).toFixed(0)}%
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-[var(--rzp-primary)] h-full rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(c.score * 100, 100)}%` }}
                      />
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-[var(--rzp-text-muted)] pt-0.5">
                      <span>Weight: {(c.weight * 100).toFixed(0)}%</span>
                      <span className="truncate max-w-[130px]" title={c.evidence}>
                        {c.evidence}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* LAYER 6: POSITIVE SIGNALS (WHY IT WON) */}
          {positiveSignals.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                <h4 className="font-bold text-emerald-800 flex items-center text-xs uppercase tracking-wider">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1.5 text-emerald-600" /> 6. Positive Decision Evidence (Why It Won)
                </h4>
                <span className="text-[11px] text-emerald-700 font-semibold">{positiveSignals.length} signals</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {positiveSignals.map((sig, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-emerald-50/60 border border-emerald-200 rounded-lg flex items-start space-x-2"
                  >
                    <Check className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-xs text-emerald-900 block">{sig.title}</span>
                      <p className="text-[11px] text-emerald-800 mt-0.5">{sig.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

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
  );
};
