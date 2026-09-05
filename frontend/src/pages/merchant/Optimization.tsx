import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import {
  Sparkles,
  Loader2,
  TestTube,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Play,
  RotateCcw,
  Zap,
  Bot,
  CheckCircle2,
  ArrowRight,
  FileCheck2,
  Layers
} from 'lucide-react';
import { simulationApi } from '../../api/simulation';
import { productsApi } from '../../api/products';
import type { Recommendation, Product, WhatIfResponse } from '../../types';
import {
  RecommendationPipelineHeader,
  RecommendationSummaryBanner,
  RecommendationCard,
  RecommendationFilters,
  type RecommendationFilterState,
  type PipelineStepId,
  getRecommendationCategory,
  getRecommendationSeverity,
  formatPriceInINR
} from '../../components/features/recommendations';

export const Optimization: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const stepParam = searchParams.get('step') as PipelineStepId | null;
  const currentStep: PipelineStepId = stepParam === 'insight' ? 'insight' : 'action';

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(true);

  // Filter & Sort State
  const [filters, setFilters] = useState<RecommendationFilterState>({
    search: '',
    status: 'ALL',
    category: 'ALL',
    severity: 'ALL',
    sortBy: 'impact_desc'
  });

  // What-If Experiment State
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [hypothesis, setHypothesis] = useState<string>('Improve price and delivery terms to increase buyer match rate');
  const [priceOverride, setPriceOverride] = useState<string>('');
  const [deliveryDaysOverride, setDeliveryDaysOverride] = useState<string>('');
  const [returnDaysOverride, setReturnDaysOverride] = useState<string>('');
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResponse | null>(null);
  const [whatIfError, setWhatIfError] = useState('');

  // Scroll to section when step param changes
  useEffect(() => {
    if (stepParam === 'insight') {
      const el = document.getElementById('merchant-insight');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (stepParam === 'action') {
      const el = document.getElementById('recommended-actions');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  }, [stepParam]);

  const handleStepClick = (step: PipelineStepId) => {
    if (step === 'simulation') {
      navigate('/simulation?step=simulation');
    } else if (step === 'friction') {
      navigate('/simulation?step=friction');
    } else if (step === 'insight') {
      setSearchParams({ step: 'insight' });
      const el = document.getElementById('merchant-insight');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (step === 'action') {
      setSearchParams({ step: 'action' });
      const el = document.getElementById('recommended-actions');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const loadData = async () => {
    setLoadingRecs(true);
    try {
      const [prodRes] = await Promise.all([
        productsApi.getProducts({ limit: 100 }).catch(() => ({ data: { items: [] } })),
      ]);

      const items = prodRes.data.items || [];
      setProducts(items);
      if (items.length > 0 && !selectedProductId) {
        setSelectedProductId(items[0].id);
      }

      const res = await simulationApi.getRecommendations();
      setRecommendations(res.data || []);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
    } finally {
      setLoadingRecs(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApplyRecommendationToWhatIf = (rec: Recommendation) => {
    if (rec.product_id) {
      setSelectedProductId(rec.product_id);
    }
    setHypothesis(`Testing recommendation: ${rec.title}`);

    if (rec.action_data?.friction_type === 'DELIVERY_UNCLEAR' || rec.type.includes('DELIVERY')) {
       setDeliveryDaysOverride(String(rec.action_data?.new_delivery_days ?? 2));
    }
    if (rec.action_data?.friction_type === 'RETURN_UNCLEAR' || rec.type.includes('RETURN')) {
       setReturnDaysOverride(String(rec.action_data?.new_return_days ?? 14));
    }

    if (rec.action_data?.new_price) {
      setPriceOverride(String(rec.action_data.new_price / 100));
    } else if (rec.action_data?.friction_type === 'PRICE_MISMATCH') {
      const prod = products.find(p => p.id === rec.product_id);
      if (prod) {
        setPriceOverride(String(Math.round((prod.price * 0.9) / 100)));
      }
    }

    if (rec.action_data?.delivery_days) {
      setDeliveryDaysOverride(String(rec.action_data.delivery_days));
    }
    if (rec.action_data?.return_days) {
      setReturnDaysOverride(String(rec.action_data.return_days));
    }

    const element = document.getElementById('what-if-section');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleRunWhatIf = async (e: React.FormEvent) => {
    e.preventDefault();
    setWhatIfLoading(true);
    setWhatIfError('');
    try {

      const modifications: Record<string, any> = {};
      if (selectedProductId) {
        modifications.product_id = selectedProductId;
      }
      if (priceOverride) {
        modifications.price = Math.round(parseFloat(priceOverride) * 100);
      }
      if (deliveryDaysOverride) {
        modifications.delivery_days = parseInt(deliveryDaysOverride, 10);
      }
      if (returnDaysOverride) {
        modifications.return_days = parseInt(returnDaysOverride, 10);
      }

      const res = await simulationApi.runWhatIf({
        hypothesis: hypothesis || 'Simulated catalogue optimization hypothesis',
        modifications,
      });

      setWhatIfResult(res.data);
    } catch (err: any) {
      setWhatIfError(err.response?.data?.detail || err.message || 'What-If analysis failed.');
    } finally {
      setWhatIfLoading(false);
    }
  };

  const handleStatusChange = async (id: string, status: string) => {
    try {
      const res = await simulationApi.updateRecommendationStatus(id, status);
      setRecommendations(prev => prev.map(r => r.id === id ? { ...r, status: res.data.status } : r));

      // If a recommendation was applied, refresh products to get the mutated DB state
      if (status === 'APPLIED') {
        const prodRes = await productsApi.getProducts({ limit: 100 }).catch(() => null);
        if (prodRes?.data?.items) {
          setProducts(prodRes.data.items);
        }
      }
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  const selectedProduct = products.find(p => p.id === selectedProductId);

  const availableCategories = useMemo(() => {
    const set = new Set<string>();
    recommendations.forEach(r => {
      const { category } = getRecommendationCategory(r);
      set.add(category);
    });
    return Array.from(set);
  }, [recommendations]);

  const statusCounts = useMemo(() => {
    return {
      all: recommendations.length,
      proposed: recommendations.filter(r => r.status === 'PROPOSED').length,
      applied: recommendations.filter(r => r.status === 'APPLIED').length,
      rejected: recommendations.filter(r => r.status === 'REJECTED').length
    };
  }, [recommendations]);

  const appliedRecommendations = useMemo(() => {
    return recommendations.filter(r => r.status === 'APPLIED');
  }, [recommendations]);

  const filteredRecommendations = useMemo(() => {
    return recommendations
      .filter(rec => {
        if (filters.status !== 'ALL' && rec.status !== filters.status) {
          return false;
        }

        if (filters.category !== 'ALL') {
          const { category } = getRecommendationCategory(rec);
          if (category !== filters.category) return false;
        }

        if (filters.severity !== 'ALL') {
          const matchedProd = rec.product_id ? products.find(p => p.id === rec.product_id) : undefined;
          const { severity } = getRecommendationSeverity(rec, matchedProd);
          if (severity !== filters.severity) return false;
        }

        if (filters.search.trim()) {
          const q = filters.search.toLowerCase();
          const matchedProd = rec.product_id ? products.find(p => p.id === rec.product_id) : undefined;
          const matchesTitle = rec.title.toLowerCase().includes(q);
          const matchesReason = rec.reason.toLowerCase().includes(q);
          const matchesProduct = matchedProd ? matchedProd.name.toLowerCase().includes(q) : false;
          const matchesAction = rec.action_data?.suggested_change
            ? String(rec.action_data.suggested_change).toLowerCase().includes(q)
            : false;
          if (!matchesTitle && !matchesReason && !matchesProduct && !matchesAction) {
            return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        if (filters.sortBy === 'impact_desc') {
          return (b.expected_simulated_impact || 0) - (a.expected_simulated_impact || 0);
        }
        if (filters.sortBy === 'confidence_desc') {
          return (b.confidence || 0) - (a.confidence || 0);
        }
        if (filters.sortBy === 'frictions_desc') {
          const countA = Number(a.action_data?.friction_count) || 1;
          const countB = Number(b.action_data?.friction_count) || 1;
          return countB - countA;
        }
        if (filters.sortBy === 'newest') {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        }
        return 0;
      });
  }, [recommendations, products, filters]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center tracking-tight">
          <Sparkles className="h-6 w-6 mr-2.5 text-[var(--rzp-ai)]" />
          Empirical Optimizations & What-If Simulator
        </h1>
        <p className="text-sm text-[var(--rzp-text-muted)] mt-1">
          Actionable merchant intelligence discovered from autonomous buyer persona constraint checks and in-memory What-If scenario experiments.
        </p>
      </div>

      {/* Visual Analytical Pipeline Header */}
      <RecommendationPipelineHeader currentStep={currentStep} onStepClick={handleStepClick} />

      {/* CLOSED-LOOP MUTATION VERIFICATION BANNER */}
      {appliedRecommendations.length > 0 && (
        <div className="bg-gradient-to-r from-emerald-50 via-green-50 to-teal-50 border border-emerald-300 rounded-xl p-4 shadow-sm space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                <FileCheck2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-emerald-950 flex items-center">
                  <span>{appliedRecommendations.length} Recommendation {appliedRecommendations.length === 1 ? 'Mutation' : 'Mutations'} Applied to Live Catalogue</span>
                  <span className="ml-2 text-[10px] font-mono font-bold bg-emerald-200/80 text-emerald-900 px-2 py-0.5 rounded">
                    POSTGRES PERSISTED
                  </span>
                </h3>
                <p className="text-xs text-emerald-800 mt-0.5">
                  Production catalogue attributes have been updated. Audit trail recorded in database.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              <Link to="/transactions">
                <Button variant="outline" size="sm" className="text-xs font-semibold border-emerald-300 text-emerald-900 hover:bg-emerald-100">
                  Audit Log →
                </Button>
              </Link>
              <Button
                variant="ai"
                size="sm"
                onClick={() => navigate('/simulation?step=simulation')}
                className="text-xs font-semibold shadow-sm"
              >
                <Play className="h-3.5 w-3.5 mr-1" /> Re-run Simulation to Verify
              </Button>
            </div>
          </div>

          <div className="pt-2 border-t border-emerald-200/60 flex flex-wrap gap-2 text-xs">
            <span className="text-[11px] font-semibold text-emerald-900 uppercase tracking-wider">Applied Changes:</span>
            {appliedRecommendations.map(r => (
              <span key={r.id} className="inline-flex items-center px-2 py-0.5 rounded bg-white border border-emerald-200 text-emerald-900 text-[11px] font-medium shadow-2xs">
                <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-600" />
                {r.title}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Aggregate Intelligence Summary Banner (MERCHANT INSIGHT) */}
      <div id="merchant-insight" className="scroll-mt-6">
        <RecommendationSummaryBanner
          recommendations={recommendations}
          products={products}
          onRunSimulation={() => navigate('/simulation?step=simulation')}
        />
      </div>

      {/* SECTION 1: ACTIONABLE RECOMMENDATIONS (RECOMMENDED ACTION) */}
      <div id="recommended-actions" className="space-y-4 pt-2 scroll-mt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-[var(--rzp-text)] flex items-center">
              <Zap className="h-4 w-4 mr-2 text-[var(--rzp-warning)]" /> Actionable Catalogue Interventions
            </h2>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Explicit BEFORE vs AFTER state changes derived from simulated buyer persona frictions.
            </p>
          </div>
          <span className="text-xs font-semibold text-[var(--rzp-text-muted)]">
            Showing {filteredRecommendations.length} of {recommendations.length} recommendations
          </span>
        </div>

        {/* Filter Toolbar */}
        {recommendations.length > 0 && (
          <RecommendationFilters
            filters={filters}
            onChange={setFilters}
            counts={statusCounts}
            categories={availableCategories}
          />
        )}

        {/* Recommendation Cards Content */}
        {loadingRecs ? (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-[var(--rzp-border)] shadow-sm space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)]" />
            <p className="text-xs font-semibold text-[var(--rzp-text-muted)]">Loading evidence-backed recommendations...</p>
          </div>
        ) : recommendations.length === 0 ? (
          <Card className="border-dashed bg-gray-50/50">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-12 h-12 rounded-full bg-[var(--rzp-ai-soft)] flex items-center justify-center text-[var(--rzp-ai)] mb-3">
                <Bot className="h-6 w-6" />
              </div>
              <h3 className="text-base font-semibold text-[var(--rzp-text)]">No Active Recommendations</h3>
              <p className="text-xs text-[var(--rzp-text-muted)] max-w-md mt-1 mb-5">
                Recommendations are generated when synthetic buyer personas encounter price ceiling rejections, unstated return policies, missing delivery timelines, or inventory stockouts.
              </p>
              <Button variant="ai" size="sm" onClick={() => navigate('/simulation?step=simulation')}>
                <Play className="h-4 w-4 mr-1.5" /> Launch Buyer Simulation
              </Button>
            </CardContent>
          </Card>
        ) : filteredRecommendations.length === 0 ? (
          <Card className="border-dashed bg-gray-50/50">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <AlertTriangle className="h-8 w-8 text-amber-500 mb-2" />
              <h3 className="text-sm font-semibold text-[var(--rzp-text)]">No Recommendations Match Selected Filters</h3>
              <p className="text-xs text-[var(--rzp-text-muted)] mt-1 mb-4">
                Try adjusting your search query, status tab, or category filters.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFilters({ search: '', status: 'ALL', category: 'ALL', severity: 'ALL', sortBy: 'impact_desc' })}
              >
                Reset Filters
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {filteredRecommendations.map((rec) => {
              const matchedProd = rec.product_id ? products.find(p => p.id === rec.product_id) : undefined;
              return (
                <RecommendationCard
                  key={rec.id}
                  recommendation={rec}
                  product={matchedProd}
                  onStatusChange={handleStatusChange}
                  onTestWithWhatIf={handleApplyRecommendationToWhatIf}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: WHAT-IF INTERACTIVE WORKBENCH */}
      <div id="what-if-section" className="space-y-4 pt-6 border-t border-[var(--rzp-border)] scroll-mt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold text-[var(--rzp-text)] flex items-center">
              <TestTube className="h-5 w-5 mr-2 text-[var(--rzp-primary)]" /> Interactive What-If Simulator
            </h2>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Simulate the exact match score and selection rate delta if you modify price, delivery speed, or return policies in-memory.
            </p>
          </div>

          <div className="bg-[var(--rzp-surface-subtle)] px-3 py-1.5 rounded-lg border border-[var(--rzp-border)] flex items-center text-xs text-[var(--rzp-text-secondary)]">
            <ShieldCheck className="h-4 w-4 text-[var(--rzp-primary)] mr-1.5 shrink-0" />
            <span>Zero Production Mutation Guarantee</span>
          </div>
        </div>

        {whatIfError && (
          <div className="p-3.5 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-xs font-medium flex items-center border border-red-200">
            <AlertTriangle className="h-4 w-4 mr-2 shrink-0" />
            {whatIfError}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Form */}
          <div className="lg:col-span-5">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center justify-between">
                  <span>Configure Experiment</span>
                  <span className="text-[10px] text-[var(--rzp-text-muted)] font-normal uppercase tracking-wider">In-Memory Override</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRunWhatIf} className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-[var(--rzp-text)] block mb-1.5">Target Product</label>
                    <select
                      value={selectedProductId}
                      onChange={(e) => setSelectedProductId(e.target.value)}
                      className="w-full h-9 rounded-lg border border-[var(--rzp-border-strong)] bg-white px-3 text-xs focus:ring-2 focus:ring-[var(--rzp-primary)] focus:outline-none"
                    >
                      <option value="">All Products in Catalogue</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({formatPriceInINR(p.price)})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[var(--rzp-text)] block mb-1.5">Experiment Hypothesis</label>
                    <Input
                      placeholder="e.g. Reduce price to ₹4,499 to win Budget-Conscious buyers"
                      value={hypothesis}
                      onChange={(e) => setHypothesis(e.target.value)}
                      className="text-xs"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-[var(--rzp-text)] block mb-1.5">
                        Proposed Price (₹)
                      </label>
                      <Input
                        type="number"
                        placeholder={selectedProduct ? String(selectedProduct.price / 100) : '4999'}
                        value={priceOverride}
                        onChange={(e) => setPriceOverride(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-[var(--rzp-text)] block mb-1.5">
                        Delivery Speed (Days)
                      </label>
                      <Input
                        type="number"
                        placeholder="2"
                        value={deliveryDaysOverride}
                        onChange={(e) => setDeliveryDaysOverride(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-[var(--rzp-text)] block mb-1.5">
                      Return Window (Days)
                    </label>
                    <Input
                      type="number"
                      placeholder="14"
                      value={returnDaysOverride}
                      onChange={(e) => setReturnDaysOverride(e.target.value)}
                      className="text-xs"
                    />
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setPriceOverride('');
                        setDeliveryDaysOverride('');
                        setReturnDaysOverride('');
                        setWhatIfResult(null);
                      }}
                      className="text-xs text-gray-500 hover:text-[var(--rzp-text)]"
                    >
                      <RotateCcw className="h-3 w-3 mr-1" /> Reset Overrides
                    </Button>
                    <Button type="submit" variant="primary" size="sm" isLoading={whatIfLoading}>
                      <Play className="h-3.5 w-3.5 mr-1" /> Run What-If Simulation
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Results Comparison View */}
          <div className="lg:col-span-7">
            {!whatIfResult && !whatIfLoading && (
              <Card className="border-dashed bg-gray-50/50 h-full flex flex-col items-center justify-center p-8 text-center min-h-[300px]">
                <TestTube className="h-10 w-10 text-gray-300 mb-3" />
                <h3 className="text-sm font-semibold text-[var(--rzp-text)]">Ready to Simulate What-If Delta</h3>
                <p className="text-xs text-[var(--rzp-text-muted)] max-w-sm mt-1 mb-4">
                  Select a recommendation above and click <strong>Test in What-If</strong>, or adjust parameters on the left to simulate comparative persona match rates safely.
                </p>
              </Card>
            )}

            {whatIfLoading && (
              <Card className="h-full flex flex-col items-center justify-center p-12 text-center border-[var(--rzp-primary)] animate-pulse min-h-[300px]">
                <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)] mb-3" />
                <h3 className="text-sm font-semibold text-[var(--rzp-text)]">Evaluating Baseline vs Proposed Catalogue...</h3>
                <p className="text-xs text-[var(--rzp-text-muted)] mt-1">Executing persona decision scoring in-memory</p>
              </Card>
            )}

            {whatIfResult && !whatIfLoading && (
              <div className="space-y-4 animate-in fade-in duration-300">
                {/* TARGET PRODUCT PANEL (primary, when a specific product is targeted) */}
                {whatIfResult.target_product_metrics && selectedProductId && (() => {
                  const tpm = whatIfResult.target_product_metrics!;
                  const scoreDeltaPositive = tpm.score_delta >= 0;
                  const eligDelta = tpm.eligibility_delta;
                  return (
                    <Card className="border-2 border-[var(--rzp-primary)] shadow-sm">
                      <CardHeader className="pb-3 bg-[var(--rzp-primary-soft)] border-b border-[var(--rzp-primary)]">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-sm text-[var(--rzp-primary)] flex items-center font-bold">
                            <Sparkles className="h-4 w-4 mr-1.5" /> What-If: Target Product Outcome
                          </CardTitle>
                          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center ${
                            scoreDeltaPositive
                              ? 'bg-[var(--rzp-success-soft)] text-[var(--rzp-success)] border border-[var(--rzp-success)]'
                              : 'bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] border border-[var(--rzp-danger)]'
                          }`}>
                            {scoreDeltaPositive ? <TrendingUp className="h-3.5 w-3.5 mr-1" /> : <TrendingDown className="h-3.5 w-3.5 mr-1" />}
                            Score Delta: {scoreDeltaPositive ? `+${tpm.score_delta_pct}%` : `${tpm.score_delta_pct}%`}
                          </span>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          {/* Baseline Product Box */}
                          <div className="p-3.5 bg-gray-50 border border-gray-200 rounded-lg text-xs space-y-2">
                            <span className="font-bold text-gray-500 uppercase tracking-wider block text-[10px]">
                              Current Baseline
                            </span>
                            <div className="text-xl font-black text-[var(--rzp-text)]">
                              {(tpm.baseline_avg_score * 100).toFixed(1)}%
                            </div>
                            <p className="text-[11px] text-[var(--rzp-text-muted)]">Match Score</p>
                            <p className="text-[11px] text-gray-500">
                              Eligible: {(tpm.baseline_eligible_rate * 100).toFixed(0)}% of {tpm.scenarios_evaluated} personas
                            </p>
                          </div>
                          {/* Proposed Product Box */}
                          <div className="p-3.5 bg-purple-50/70 border border-purple-200 rounded-lg text-xs space-y-2">
                            <span className="font-bold text-[var(--rzp-ai)] uppercase tracking-wider block text-[10px]">
                              Proposed (Simulated)
                            </span>
                            <div className="text-xl font-black text-[var(--rzp-primary)]">
                              {(tpm.proposed_avg_score * 100).toFixed(1)}%
                            </div>
                            <p className="text-[11px] text-[var(--rzp-text-muted)]">Match Score</p>
                            <p className="text-[11px] text-gray-500">
                              Eligible: {(tpm.proposed_eligible_rate * 100).toFixed(0)}% of {tpm.scenarios_evaluated} personas
                              {eligDelta > 0 && <span className="ml-1 text-emerald-700 font-semibold">(↑ +{(eligDelta * 100).toFixed(0)}%)</span>}
                              {eligDelta < 0 && <span className="ml-1 text-red-700 font-semibold">(↓ {(eligDelta * 100).toFixed(0)}%)</span>}
                            </p>
                          </div>
                        </div>
                        <div className="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-[var(--rzp-text-secondary)]">
                          <strong>Hypothesis: </strong>{whatIfResult.hypothesis}
                        </div>
                        {/* Catalogue-wide context (secondary) */}
                        <details className="text-[11px] text-[var(--rzp-text-muted)] border-t border-gray-100 pt-2 cursor-pointer">
                          <summary className="font-semibold text-gray-500 hover:text-gray-700 select-none">
                            Catalogue-wide context (all {whatIfResult.baseline_metrics.total_scenarios} personas, all products)
                          </summary>
                          <div className="mt-2 grid grid-cols-2 gap-2 text-[11px]">
                            <div className="p-2 bg-gray-50 rounded border border-gray-100">
                              <span className="text-gray-400 block">Baseline match rate</span>
                              <span className="font-semibold">{((whatIfResult.baseline_metrics.simulated_selection_rate ?? 0) * 100).toFixed(1)}%</span>
                            </div>
                            <div className="p-2 bg-purple-50/50 rounded border border-purple-100">
                              <span className="text-gray-400 block">Proposed match rate</span>
                              <span className="font-semibold">{((whatIfResult.simulated_metrics.simulated_selection_rate ?? 0) * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                          <p className="mt-1.5 text-[10px] text-gray-400">
                            Catalogue-wide metrics change slowly when only one product of {products.length}+ is modified.
                          </p>
                        </details>
                        <div className="text-[11px] text-[var(--rzp-text-muted)] flex items-center justify-between pt-1 border-t border-gray-100">
                          <span>In-Memory Evaluation · Zero Production Mutation</span>
                          <span className="font-mono text-gray-500">ID: {whatIfResult.id.slice(0, 8)}...</span>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })()}

                {/* CATALOGUE-WIDE PANEL (shown only when no specific product targeted) */}
                {!whatIfResult.target_product_metrics && (
                  <Card className="border-2 border-[var(--rzp-primary)] shadow-sm">
                    <CardHeader className="pb-3 bg-[var(--rzp-primary-soft)] border-b border-[var(--rzp-primary)]">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm text-[var(--rzp-primary)] flex items-center font-bold">
                          <Sparkles className="h-4 w-4 mr-1.5" /> What-If Comparative Outcome
                        </CardTitle>
                        <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center ${
                          whatIfResult.delta_percentage >= 0
                            ? 'bg-[var(--rzp-success-soft)] text-[var(--rzp-success)] border border-[var(--rzp-success)]'
                            : 'bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] border border-[var(--rzp-danger)]'
                        }`}>
                          {whatIfResult.delta_percentage >= 0 ? (
                            <TrendingUp className="h-3.5 w-3.5 mr-1" />
                          ) : (
                            <TrendingDown className="h-3.5 w-3.5 mr-1" />
                          )}
                          Score Delta: {whatIfResult.delta_percentage >= 0 ? `+${whatIfResult.delta_percentage}%` : `${whatIfResult.delta_percentage}%`}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-4 space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        {/* Baseline Box */}
                        <div className="p-3.5 bg-gray-50 border border-gray-200 rounded-lg text-xs space-y-1.5">
                          <span className="font-bold text-gray-500 uppercase tracking-wider block text-[10px]">
                            Current Baseline
                          </span>
                          <div className="text-xl font-black text-[var(--rzp-text)]">
                            {(
                              (whatIfResult.baseline_metrics.simulated_selection_rate !== undefined
                                ? whatIfResult.baseline_metrics.simulated_selection_rate
                                : whatIfResult.baseline_metrics.conversion_rate !== undefined
                                ? whatIfResult.baseline_metrics.conversion_rate
                                : 0) * 100
                            ).toFixed(1)}% Match
                          </div>
                          <p className="text-[11px] text-[var(--rzp-text-muted)]">
                            {whatIfResult.baseline_metrics.average_score !== undefined
                              ? `Avg Score: ${whatIfResult.baseline_metrics.average_score}`
                              : 'Deterministic Baseline'}
                          </p>
                        </div>

                        {/* Proposed Box */}
                        <div className="p-3.5 bg-purple-50/70 border border-purple-200 rounded-lg text-xs space-y-1.5">
                          <span className="font-bold text-[var(--rzp-ai)] uppercase tracking-wider block text-[10px]">
                            Proposed (Simulated)
                          </span>
                          <div className="text-xl font-black text-[var(--rzp-primary)]">
                            {(
                              (whatIfResult.simulated_metrics.simulated_selection_rate !== undefined
                                ? whatIfResult.simulated_metrics.simulated_selection_rate
                                : whatIfResult.simulated_metrics.conversion_rate !== undefined
                                ? whatIfResult.simulated_metrics.conversion_rate
                                : 0) * 100
                            ).toFixed(1)}% Match
                          </div>
                          <p className="text-[11px] text-[var(--rzp-text-muted)]">
                            {whatIfResult.simulated_metrics.average_score !== undefined
                              ? `Avg Score: ${whatIfResult.simulated_metrics.average_score}`
                              : 'Simulated Change'}
                          </p>
                        </div>
                      </div>

                      <div className="p-3 bg-gray-50 rounded-md border border-gray-100 text-xs text-[var(--rzp-text-secondary)]">
                        <strong>Hypothesis Evaluated: </strong> {whatIfResult.hypothesis}
                      </div>

                      <div className="text-[11px] text-[var(--rzp-text-muted)] flex items-center justify-between pt-2 border-t border-gray-100">
                        <span>In-Memory Evaluation</span>
                        <span className="font-mono text-gray-500">ID: {whatIfResult.id.slice(0, 8)}...</span>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
