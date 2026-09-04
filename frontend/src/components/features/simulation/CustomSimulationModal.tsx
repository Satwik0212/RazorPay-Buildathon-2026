import React, { useState, useCallback } from 'react';
import { X, Plus, Tag, AlertTriangle, CheckCircle2, Bot, RotateCcw } from 'lucide-react';
import type { CustomBuyerConfig } from '../../../types';

interface WeightDimension {
  key: keyof CustomBuyerConfig['weights'];
  label: string;
  description: string;
  icon: string;
  defaultValue: number;
}

const WEIGHT_DIMENSIONS: WeightDimension[] = [
  { key: 'quality',  label: 'Quality',             description: 'Product rating, return rate, description completeness', icon: '⭐', defaultValue: 0.30 },
  { key: 'metadata', label: 'Features / Metadata',  description: 'Product specifications, attributes, images',           icon: '🔍', defaultValue: 0.25 },
  { key: 'delivery', label: 'Delivery Speed',       description: 'Shipping time, estimated delivery days',               icon: '🚚', defaultValue: 0.20 },
  { key: 'returns',  label: 'Return Policy',        description: 'Return window, return-friendliness',                   icon: '↩️', defaultValue: 0.15 },
  { key: 'price',    label: 'Price / Value',        description: 'Price relative to budget ceiling',                     icon: '💰', defaultValue: 0.10 },
];

const DEFAULT_WEIGHTS: CustomBuyerConfig['weights'] = {
  quality: 0.30, metadata: 0.25, delivery: 0.20, returns: 0.15, price: 0.10,
};

interface CustomSimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: CustomBuyerConfig) => void;
  isLoading?: boolean;
}

const CustomSimulationModal: React.FC<CustomSimulationModalProps> = ({
  isOpen, onClose, onSubmit, isLoading = false,
}) => {
  const [name, setName] = useState('');
  const [maxBudget, setMaxBudget] = useState<string>('');
  const [deliveryDays, setDeliveryDays] = useState<string>('');
  const [requirementInput, setRequirementInput] = useState('');
  const [requirements, setRequirements] = useState<string[]>([]);
  const [weights, setWeights] = useState<CustomBuyerConfig['weights']>(DEFAULT_WEIGHTS);
  const [scenarioCount, setScenarioCount] = useState<number>(10);

  const totalWeight = Object.values(weights).reduce((s, v) => s + v, 0);
  const weightError = Math.abs(totalWeight - 1.0) > 0.01;
  const totalPct = Math.round(totalWeight * 100);

  const handleWeightChange = useCallback((key: keyof typeof weights, pct: number) => {
    setWeights(prev => ({ ...prev, [key]: Math.max(0, pct) / 100 }));
  }, []);

  const resetWeights = useCallback(() => setWeights(DEFAULT_WEIGHTS), []);

  const addRequirement = useCallback(() => {
    const tag = requirementInput.trim().toLowerCase();
    if (tag && !requirements.includes(tag) && requirements.length < 20) {
      setRequirements(prev => [...prev, tag]);
    }
    setRequirementInput('');
  }, [requirementInput, requirements]);

  const removeRequirement = useCallback((tag: string) => {
    setRequirements(prev => prev.filter(r => r !== tag));
  }, []);

  const handleRequirementKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addRequirement(); }
  };

  const canSubmit = name.trim().length > 0 && !weightError && !isLoading;

  const handleSubmit = useCallback(() => {
    if (!canSubmit) return;
    const config: CustomBuyerConfig = {
      name: name.trim(),
      ...(maxBudget && parseInt(maxBudget, 10) > 0 ? { max_budget: parseInt(maxBudget, 10) } : {}),
      ...(deliveryDays && parseInt(deliveryDays, 10) > 0 ? { delivery_deadline_days: parseInt(deliveryDays, 10) } : {}),
      requirements,
      weights,
      scenario_count: scenarioCount,
    };
    onSubmit(config);
  }, [canSubmit, name, maxBudget, deliveryDays, requirements, weights, scenarioCount, onSubmit]);

  const handleReset = () => {
    setName(''); setMaxBudget(''); setDeliveryDays('');
    setRequirementInput(''); setRequirements([]);
    setWeights(DEFAULT_WEIGHTS); setScenarioCount(10);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-lg flex items-center justify-center">
              <Bot className="h-4 w-4 text-[var(--rzp-ai)]" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--rzp-text)]">Create Custom AI Buyer</h2>
              <p className="text-[11px] text-[var(--rzp-text-muted)]">Define your own buyer persona and run it against your full catalogue</p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 p-6 space-y-5">
          {/* Name */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-1.5">
              Buyer Persona Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text" maxLength={100}
              placeholder="e.g. Weekend Audio Buyer, Budget Traveller, Gift Shopper"
              value={name} onChange={e => setName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-[var(--rzp-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--rzp-ai)] focus:border-[var(--rzp-ai)] placeholder:text-gray-400"
            />
          </div>

          {/* Budget + Delivery */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-1.5">
                Max Budget (₹) <span className="text-[11px] font-normal text-gray-400">optional</span>
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium text-gray-500">₹</span>
                <input type="number" min={1} placeholder="5000" value={maxBudget}
                  onChange={e => setMaxBudget(e.target.value)}
                  className="w-full pl-7 pr-3 py-2 text-sm border border-[var(--rzp-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--rzp-ai)] focus:border-[var(--rzp-ai)]"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-1.5">
                Delivery Within <span className="text-[11px] font-normal text-gray-400">optional</span>
              </label>
              <div className="relative">
                <input type="number" min={1} max={365} placeholder="3" value={deliveryDays}
                  onChange={e => setDeliveryDays(e.target.value)}
                  className="w-full pl-3 pr-12 py-2 text-sm border border-[var(--rzp-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--rzp-ai)] focus:border-[var(--rzp-ai)]"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">days</span>
              </div>
            </div>
          </div>

          {/* Requirements */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-1.5">
              Required Product Features <span className="text-[11px] font-normal text-gray-400">optional — press Enter to add</span>
            </label>
            {requirements.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {requirements.map(tag => (
                  <span key={tag} className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-medium rounded-full">
                    <Tag className="h-3 w-3" />
                    {tag}
                    <button type="button" onClick={() => removeRequirement(tag)} className="text-indigo-400 hover:text-indigo-700 ml-0.5">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input type="text"
                placeholder="e.g. warranty, bluetooth, noise-cancellation"
                value={requirementInput} onChange={e => setRequirementInput(e.target.value)}
                onKeyDown={handleRequirementKeyDown} disabled={requirements.length >= 20}
                className="flex-1 px-3 py-2 text-sm border border-[var(--rzp-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--rzp-ai)] focus:border-[var(--rzp-ai)] disabled:opacity-50"
              />
              <button type="button" onClick={addRequirement}
                disabled={!requirementInput.trim() || requirements.length >= 20}
                className="px-3 py-2 bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)] border border-[var(--rzp-ai)] rounded-lg text-xs font-semibold hover:bg-[var(--rzp-ai)] hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Weights */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)]">
                Buyer Priorities (Scoring Weights)
              </label>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full border flex items-center gap-1 ${weightError ? 'bg-red-50 text-red-700 border-red-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'}`}>
                  {weightError ? (<><AlertTriangle className="h-3 w-3" /> {totalPct}% (must be 100%)</>) : (<><CheckCircle2 className="h-3 w-3" /> {totalPct}% ✓</>)}
                </span>
                <button type="button" onClick={resetWeights} className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-[var(--rzp-ai)] transition-colors">
                  <RotateCcw className="h-3 w-3" /> Reset
                </button>
              </div>
            </div>
            <div className="space-y-3 bg-gray-50/70 rounded-xl border border-[var(--rzp-border)] p-4">
              {WEIGHT_DIMENSIONS.map(dim => {
                const pct = Math.round((weights[dim.key] ?? 0) * 100);
                return (
                  <div key={dim.key}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-[var(--rzp-text)] flex items-center gap-1.5">
                        <span>{dim.icon}</span>{dim.label}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-[var(--rzp-text-muted)] hidden sm:block">{dim.description}</span>
                        <span className="font-mono font-bold text-xs text-[var(--rzp-primary)] w-8 text-right">{pct}%</span>
                      </div>
                    </div>
                    <input type="range" min={0} max={100} step={5} value={pct}
                      onChange={e => handleWeightChange(dim.key, parseInt(e.target.value, 10))}
                      className="w-full h-1.5 accent-[var(--rzp-ai)] cursor-pointer"
                    />
                  </div>
                );
              })}
            </div>
            {weightError && (
              <p className="mt-2 text-xs text-red-600 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                Weights must sum to exactly 100%. Current total: {totalPct}%. Adjust the sliders above.
              </p>
            )}
          </div>

          {/* Scenario count */}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-2">Scenario Runs</label>
            <div className="flex gap-2">
              {[1, 5, 10, 20].map(cnt => (
                <button key={cnt} type="button" onClick={() => setScenarioCount(cnt)}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold border transition-all ${scenarioCount === cnt ? 'bg-[var(--rzp-primary)] text-white border-[var(--rzp-primary)]' : 'bg-white text-[var(--rzp-text-secondary)] border-[var(--rzp-border)] hover:bg-gray-50'}`}>
                  {cnt}×
                </button>
              ))}
            </div>
            <p className="text-[11px] text-[var(--rzp-text-muted)] mt-1.5">
              All {scenarioCount} scenario{scenarioCount > 1 ? 's' : ''} run deterministically — same inputs produce the same winner every time.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between gap-3 shrink-0 bg-gray-50/50">
          <button type="button" onClick={handleReset} className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1.5 transition-colors">
            <RotateCcw className="h-3.5 w-3.5" /> Clear form
          </button>
          <div className="flex items-center gap-3">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-[var(--rzp-text-secondary)] bg-white border border-[var(--rzp-border)] rounded-lg hover:bg-gray-50 transition-colors">
              Cancel
            </button>
            <button type="button" onClick={handleSubmit} disabled={!canSubmit}
              className={`px-5 py-2 text-xs font-bold rounded-lg transition-all ${canSubmit ? 'bg-gradient-to-r from-[var(--rzp-ai)] to-indigo-600 text-white shadow-sm hover:shadow-md hover:opacity-90' : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}>
              {isLoading
                ? <span className="flex items-center gap-2"><div className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />Running…</span>
                : <span className="flex items-center gap-2"><Bot className="h-3.5 w-3.5" />Run Custom Simulation</span>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomSimulationModal;
