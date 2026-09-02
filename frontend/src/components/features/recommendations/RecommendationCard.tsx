import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  Package, 
  TestTube, 
  ArrowRight, 
  Clock, 
  RotateCcw,
  Check,
  FileCheck2,
  Play,
  Layers,
  AlertCircle
} from 'lucide-react';
import { Card, CardHeader, CardContent, CardFooter } from '../../ui/Card';
import { Button } from '../../ui/Button';
import type { Recommendation, Product } from '../../../types';
import { 
  getRecommendationCategory, 
  getRecommendationSeverity, 
  getTargetPersonas,
  getRecommendationFieldDetails,
  formatPriceInINR
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
  const navigate = useNavigate();
  const [updating, setUpdating] = useState(false);

  const { category, colorClass, bgClass, borderClass } = getRecommendationCategory(recommendation);
  const { severity, label: severityLabel, badgeClass: severityBadgeClass } = getRecommendationSeverity(recommendation, product);
  const targetPersonas = getTargetPersonas(recommendation);
  const fieldDetails = getRecommendationFieldDetails(recommendation, product);

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

  return (
    <Card
      className={`flex flex-col justify-between border-l-4 transition-all hover:shadow-md ${
        isApplied
          ? 'border-l-[var(--rzp-success)] bg-green-50/15'
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
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold text-[var(--rzp-success)] bg-emerald-50 border border-emerald-300 shadow-xs">
                <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-emerald-600" /> APPLIED TO CATALOGUE
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
        {/* SECTION A: BEFORE STATE & SIMULATION DISCOVERY */}
        <div className="border border-[var(--rzp-border)] rounded-lg p-3.5 bg-white space-y-2.5">
          <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 flex items-center">
              <Layers className="h-3.5 w-3.5 mr-1 text-[var(--rzp-primary)]" /> Diagnostic Baseline (BEFORE)
            </span>
            <span className="text-[10px] font-mono text-gray-400">
              {frictionCount} recorded friction {frictionCount === 1 ? 'event' : 'events'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <div>
              <span className="text-[10px] font-semibold uppercase text-gray-400 block">Product</span>
              <div className="font-semibold text-xs text-[var(--rzp-text)] truncate" title={fieldDetails.productName}>
                {fieldDetails.productName}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-semibold uppercase text-gray-400 block">Field & Current Value</span>
              <div className="font-mono text-xs font-medium text-red-700 bg-red-50/70 px-1.5 py-0.5 rounded border border-red-100 inline-block">
                {fieldDetails.field}: <strong>{fieldDetails.beforeValue}</strong>
              </div>
            </div>

            <div>
              <span className="text-[10px] font-semibold uppercase text-gray-400 block">Buyer Requirement</span>
              <div className="text-xs text-gray-700 font-medium">
                {fieldDetails.buyerRequirement}
              </div>
            </div>

            <div>
              <span className="text-[10px] font-semibold uppercase text-gray-400 block">Simulation Discovery</span>
              <div className="text-xs text-amber-800 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-100 font-medium line-clamp-2" title={fieldDetails.simulationResult}>
                {fieldDetails.simulationResult}
              </div>
            </div>
          </div>
        </div>

        {/* SECTION B: ACTION / PROPOSED INTERVENTION */}
        <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-lg space-y-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-ai)] block">
            Merchant Action
          </span>
          <p className="text-xs font-semibold text-[var(--rzp-text)]">
            {fieldDetails.actionSummary}
          </p>
        </div>

        {/* SECTION C: AFTER STATE & AUDIT (WHEN APPLIED) */}
        {isApplied && (
          <div className="border border-emerald-200 bg-emerald-50/40 rounded-lg p-3.5 space-y-2.5 animate-in fade-in">
            <div className="flex items-center justify-between border-b border-emerald-100 pb-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 flex items-center">
                <FileCheck2 className="h-3.5 w-3.5 mr-1 text-emerald-600" /> Catalogue Changed (AFTER)
              </span>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded">
                MUTATION PERSISTED
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[10px] font-semibold uppercase text-gray-500 block">Product</span>
                <span className="font-semibold text-gray-900 truncate block">{fieldDetails.productName}</span>
              </div>

              <div>
                <span className="text-[10px] font-semibold uppercase text-gray-500 block">Field Mutation</span>
                <div className="text-[11px] font-mono">
                  <span className="text-gray-400 line-through mr-1">{fieldDetails.beforeValue}</span>
                  <span className="font-bold text-emerald-700 bg-white px-1.5 py-0.5 rounded border border-emerald-200">
                    {fieldDetails.afterValue}
                  </span>
                </div>
              </div>

              <div className="sm:col-span-2 pt-1 border-t border-emerald-100/60 flex items-center justify-between">
                <div className="flex items-center space-x-1.5 text-[11px] text-gray-600">
                  <span className="font-semibold text-emerald-800">Audit Event:</span>
                  <span className="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-emerald-200 text-emerald-900 font-bold">
                    {fieldDetails.auditEventType}
                  </span>
                </div>
                <Link to="/transactions" className="text-[11px] font-bold text-[var(--rzp-primary)] hover:underline flex items-center">
                  View in Audit Log <ArrowRight className="h-3 w-3 ml-0.5" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Target Persona List */}
        <div className="space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block">
            Target Buyer Personas
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
          ) : isApplied ? (
            <div className="flex items-center space-x-2">
              <Button
                variant="ai"
                size="sm"
                onClick={() => navigate('/simulation?step=simulation')}
                className="text-xs font-semibold shadow-sm"
              >
                <Play className="h-3 w-3 mr-1" /> Re-run Simulation
              </Button>
              <Button
                variant="outline"
                size="sm"
                isLoading={updating}
                onClick={() => handleStatusUpdate('PROPOSED')}
                className="text-xs text-gray-600 hover:bg-gray-100"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1" /> Reset
              </Button>
            </div>
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
          variant="outline"
          size="sm"
          onClick={() => onTestWithWhatIf(recommendation)}
          className="text-xs font-semibold whitespace-nowrap text-purple-700 border-purple-200 hover:bg-purple-50"
        >
          <TestTube className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-ai)]" /> Test in What-If <ArrowRight className="h-3 w-3 ml-1" />
        </Button>
      </CardFooter>
    </Card>
  );
};
