import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { 
  Sparkles, 
  ArrowRight, 
  Loader2, 
  TestTube, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown, 
  Layers, 
  Play,
  RotateCcw,
  Zap
} from 'lucide-react';
import { simulationApi } from '../../api/simulation';
import { productsApi } from '../../api/products';
import { authApi } from '../../api/auth';
import type { Recommendation, Product, WhatIfResponse } from '../../types';

export const Optimization = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [error, setError] = useState('');

  // What-If Experiment State
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [hypothesis, setHypothesis] = useState<string>('Improve price and delivery terms to increase buyer match rate');
  const [priceOverride, setPriceOverride] = useState<string>('');
  const [deliveryDaysOverride, setDeliveryDaysOverride] = useState<string>('');
  const [returnDaysOverride, setReturnDaysOverride] = useState<string>('');
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResponse | null>(null);
  const [whatIfError, setWhatIfError] = useState('');

  useEffect(() => {
    const fetchInitialData = async () => {
      setLoadingRecs(true);
      try {
        const [merchantId, prodRes] = await Promise.all([
          authApi.getOrInitMerchantId(),
          productsApi.getProducts().catch(() => ({ data: { items: [] } })),
        ]);

        const items = prodRes.data.items || [];
        setProducts(items);
        if (items.length > 0) {
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

    fetchInitialData();
  }, []);

  const handleApplyRecommendationToWhatIf = (rec: Recommendation) => {
    if (rec.product_id) {
      setSelectedProductId(rec.product_id);
    }
    setHypothesis(`Testing recommendation: ${rec.title}`);
    
    if (rec.action_data?.new_price) {
      setPriceOverride(String(rec.action_data.new_price / 100));
    }
    if (rec.action_data?.delivery_days) {
      setDeliveryDaysOverride(String(rec.action_data.delivery_days));
    }
    if (rec.action_data?.return_days) {
      setReturnDaysOverride(String(rec.action_data.return_days));
    }

    // Smooth scroll down to what-if section
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
      const realMerchantId = await authApi.getOrInitMerchantId();
      if (!realMerchantId) throw new Error("Merchant authentication required.");

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

  const selectedProduct = products.find(p => p.id === selectedProductId);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price / 100);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
          <Sparkles className="h-6 w-6 mr-2 text-[var(--rzp-ai)]" /> AI Optimizations & What-If Simulator
        </h1>
        <p className="text-sm text-[var(--rzp-text-muted)]">
          Empirical recommendations derived from buyer friction and safe, in-memory What-If scenario experiments.
        </p>
      </div>

      {/* Safety & Truth Notice */}
      <div className="bg-[var(--rzp-surface-subtle)] p-3.5 rounded-lg border border-[var(--rzp-border)] flex items-start text-xs">
        <ShieldCheck className="h-5 w-5 text-[var(--rzp-primary)] mr-2.5 shrink-0" />
        <div className="text-[var(--rzp-text-secondary)]">
          <span className="font-semibold text-[var(--rzp-text)]">Zero Production Mutation Guarantee: </span>
          The What-If engine runs 100% in-memory against deterministic simulation scenarios. Your live catalogue prices, inventory, and database records remain completely untouched.
        </div>
      </div>

      {/* SECTION 1: RECOMMENDATIONS */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[var(--rzp-text)] flex items-center">
              <Zap className="h-4 w-4 mr-2 text-[var(--rzp-warning)]" /> Empirical Recommendations
            </h2>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Discovered from buyer persona constraint rejections in your active catalogue.
            </p>
          </div>
          <span className="text-xs font-semibold text-[var(--rzp-text-muted)]">
            {recommendations.length} Active {recommendations.length === 1 ? 'Recommendation' : 'Recommendations'}
          </span>
        </div>

        {loadingRecs ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-7 w-7 animate-spin text-[var(--rzp-primary)]" />
          </div>
        ) : recommendations.length === 0 ? (
          <Card className="border-dashed bg-gray-50/50">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <Sparkles className="h-10 w-10 text-gray-300 mb-3" />
              <h3 className="text-base font-semibold text-[var(--rzp-text)]">No Active Friction Points</h3>
              <p className="text-xs text-[var(--rzp-text-muted)] max-w-md mt-1">
                Your products are currently performing well against default buyer constraints, or no friction has been detected yet.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {recommendations.map((rec) => {
              const matchedProd = rec.product_id ? products.find(p => p.id === rec.product_id) : null;

              return (
                <Card 
                  key={rec.id} 
                  className="border-l-4 border-l-[var(--rzp-ai)] flex flex-col justify-between hover:shadow-md transition-shadow"
                >
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-ai)] bg-[var(--rzp-ai-soft)] px-2 py-0.5 rounded">
                          {rec.type}
                        </span>
                        <CardTitle className="text-base mt-2">{rec.title}</CardTitle>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-xs font-semibold text-[var(--rzp-success)] bg-[var(--rzp-success-soft)] px-2 py-0.5 rounded">
                          +{(rec.expected_simulated_impact * 100).toFixed(0)}% Impact
                        </span>
                        <p className="text-[10px] text-[var(--rzp-text-muted)] mt-1">
                          Confidence: {(rec.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-1">
                    <div className="p-2.5 bg-gray-50 rounded-md border border-gray-100 text-xs text-[var(--rzp-text-secondary)]">
                      <strong className="text-[var(--rzp-text)]">Detected Friction: </strong>
                      {rec.reason}
                    </div>

                    {matchedProd && (
                      <div className="text-xs text-[var(--rzp-text-muted)] flex items-center justify-between">
                        <span>Target: <strong>{matchedProd.name}</strong></span>
                        <span>Current Price: <strong>{formatPrice(matchedProd.price)}</strong></span>
                      </div>
                    )}

                    <div className="pt-2 border-t border-[var(--rzp-border)] flex items-center justify-between">
                      <span className="text-[10px] text-[var(--rzp-text-muted)]">Source: Friction Diagnostics</span>
                      <Button 
                        variant="ai" 
                        size="sm" 
                        onClick={() => handleApplyRecommendationToWhatIf(rec)}
                        className="text-xs"
                      >
                        <TestTube className="h-3.5 w-3.5 mr-1" /> Test with What-If <ArrowRight className="h-3.5 w-3.5 ml-1" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: WHAT-IF INTERACTIVE WORKBENCH */}
      <div id="what-if-section" className="space-y-4 pt-4 border-t border-[var(--rzp-border)]">
        <div>
          <h2 className="text-base font-bold text-[var(--rzp-text)] flex items-center">
            <TestTube className="h-4 w-4 mr-2 text-[var(--rzp-primary)]" /> Interactive What-If Simulator
          </h2>
          <p className="text-xs text-[var(--rzp-text-muted)]">
            Simulate the exact score and selection rate delta if you modify price, delivery speed, or return policies.
          </p>
        </div>

        {whatIfError && (
          <div className="p-3.5 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-xs font-medium flex items-center">
            <AlertTriangle className="h-4 w-4 mr-2 shrink-0" />
            {whatIfError}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Form */}
          <div className="lg:col-span-5">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Configure Experiment</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRunWhatIf} className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-[var(--rzp-text)] block mb-1">Target Product</label>
                    <select
                      value={selectedProductId}
                      onChange={(e) => setSelectedProductId(e.target.value)}
                      className="w-full h-9 rounded-md border border-[var(--rzp-border-strong)] bg-white px-3 text-xs focus:ring-2 focus:ring-[var(--rzp-primary)] focus:outline-none"
                    >
                      <option value="">All Products in Catalogue</option>
                      {products.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({formatPrice(p.price)})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-[var(--rzp-text)] block mb-1">Hypothesis</label>
                    <Input
                      placeholder="e.g. Reduce price to ₹4,499 to win Budget Conscious buyers"
                      value={hypothesis}
                      onChange={(e) => setHypothesis(e.target.value)}
                      className="text-xs"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-[var(--rzp-text)] block mb-1">
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
                      <label className="text-xs font-medium text-[var(--rzp-text)] block mb-1">
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
                    <label className="text-xs font-medium text-[var(--rzp-text)] block mb-1">
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
                      className="text-xs"
                    >
                      <RotateCcw className="h-3 w-3 mr-1" /> Reset
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
              <Card className="border-dashed bg-gray-50/50 h-full flex flex-col items-center justify-center p-8 text-center">
                <TestTube className="h-10 w-10 text-gray-300 mb-3" />
                <h3 className="text-sm font-semibold text-[var(--rzp-text)]">Ready to Simulate What-If Delta</h3>
                <p className="text-xs text-[var(--rzp-text-muted)] max-w-sm mt-1">
                  Adjust parameter overrides on the left and execute the simulation to observe comparative persona match rates.
                </p>
              </Card>
            )}

            {whatIfLoading && (
              <Card className="h-full flex flex-col items-center justify-center p-12 text-center border-[var(--rzp-primary)] animate-pulse">
                <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)] mb-3" />
                <h3 className="text-sm font-semibold text-[var(--rzp-text)]">Evaluating Baseline vs Proposed Catalogue...</h3>
                <p className="text-xs text-[var(--rzp-text-muted)] mt-1">Running comparative personas in memory</p>
              </Card>
            )}

            {whatIfResult && !whatIfLoading && (
              <div className="space-y-4 animate-in fade-in duration-300">
                {/* Comparison Card */}
                <Card className="border-2 border-[var(--rzp-primary)]">
                  <CardHeader className="pb-3 bg-[var(--rzp-primary-soft)] border-b border-[var(--rzp-primary)]">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm text-[var(--rzp-primary)] flex items-center">
                        <Sparkles className="h-4 w-4 mr-1.5" /> What-If Comparative Outcome
                      </CardTitle>
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center ${
                        whatIfResult.delta_percentage >= 0
                          ? 'bg-[var(--rzp-success-soft)] text-[var(--rzp-success)]'
                          : 'bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)]'
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
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs space-y-1.5">
                        <span className="font-bold text-gray-500 uppercase tracking-wider block text-[10px]">
                          Current Baseline
                        </span>
                        <div className="text-lg font-bold text-[var(--rzp-text)]">
                          {(
                            (whatIfResult.baseline_metrics.simulated_selection_rate !== undefined
                              ? whatIfResult.baseline_metrics.simulated_selection_rate
                              : whatIfResult.baseline_metrics.conversion_rate !== undefined
                              ? whatIfResult.baseline_metrics.conversion_rate
                              : 0) * 100
                          ).toFixed(1)}% Match
                        </div>
                        <p className="text-[var(--rzp-text-muted)]">
                          {whatIfResult.baseline_metrics.average_score !== undefined
                            ? `Avg Score: ${whatIfResult.baseline_metrics.average_score}`
                            : whatIfResult.baseline_metrics.average_order_value !== undefined
                            ? `Simulated AOV: ${formatPrice(whatIfResult.baseline_metrics.average_order_value)}`
                            : 'Deterministic Baseline'}
                        </p>
                      </div>

                      {/* Proposed Box */}
                      <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-lg text-xs space-y-1.5">
                        <span className="font-bold text-[var(--rzp-ai)] uppercase tracking-wider block text-[10px]">
                          Proposed (Simulated)
                        </span>
                        <div className="text-lg font-bold text-[var(--rzp-primary)]">
                          {(
                            (whatIfResult.simulated_metrics.simulated_selection_rate !== undefined
                              ? whatIfResult.simulated_metrics.simulated_selection_rate
                              : whatIfResult.simulated_metrics.conversion_rate !== undefined
                              ? whatIfResult.simulated_metrics.conversion_rate
                              : 0) * 100
                          ).toFixed(1)}% Match
                        </div>
                        <p className="text-[var(--rzp-text-muted)]">
                          {whatIfResult.simulated_metrics.average_score !== undefined
                            ? `Avg Score: ${whatIfResult.simulated_metrics.average_score}`
                            : whatIfResult.simulated_metrics.average_order_value !== undefined
                            ? `Simulated AOV: ${formatPrice(whatIfResult.simulated_metrics.average_order_value)}`
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
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
