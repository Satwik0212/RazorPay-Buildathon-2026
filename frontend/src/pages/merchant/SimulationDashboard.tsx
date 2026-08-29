import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { 
  Bot, 
  Play, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  ArrowRight, 
  Filter, 
  Sliders,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { simulationApi } from '../../api/simulation';
import { personasApi } from '../../api/personas';
import { productsApi } from '../../api/products';
import { authApi } from '../../api/auth';
import type { BuyerPersona, Product, SimulationResponse } from '../../types';

export const SimulationDashboard = () => {
  const [simulating, setSimulating] = useState(false);
  const [results, setResults] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState('');
  
  // Personas & Products
  const [personas, setPersonas] = useState<BuyerPersona[]>([]);
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>(["BUDGET", "SPEED", "QUALITY", "FEATURE", "BALANCED"]);
  const [scenarioCount, setScenarioCount] = useState<number>(10);
  const [productsMap, setProductsMap] = useState<Record<string, Product>>({});
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [personaRes, productRes] = await Promise.all([
          personasApi.getPersonas().catch(() => ({ data: [] })),
          productsApi.getProducts().catch(() => ({ data: { items: [] } })),
        ]);

        if (personaRes.data && personaRes.data.length > 0) {
          setPersonas(personaRes.data);
        }

        const items = productRes.data?.items || [];
        const pMap: Record<string, Product> = {};
        items.forEach((p: Product) => {
          pMap[p.id] = p;
        });
        setProductsMap(pMap);
      } catch (err) {
        console.error('Failed to load simulation setup data:', err);
      }
    };

    fetchInitialData();
  }, []);

  const toggleProfile = (profile: string) => {
    setSelectedProfiles(prev => {
      if (prev.includes(profile)) {
        if (prev.length === 1) return prev; // keep at least one
        return prev.filter(p => p !== profile);
      } else {
        return [...prev, profile];
      }
    });
  };

  const runSimulation = async () => {
    setSimulating(true);
    setError('');
    try {
      const realMerchantId = await authApi.getOrInitMerchantId();
      if (!realMerchantId) throw new Error("No merchant session found.");
      
      const res = await simulationApi.runSimulation({
        scenario_count: scenarioCount,
        buyer_profiles: selectedProfiles
      });
      setResults(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Simulation failed to execute.');
    } finally {
      setSimulating(false);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price / 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
            <Bot className="h-6 w-6 mr-2 text-[var(--rzp-ai)]" /> Synthetic Buyer Simulation
          </h1>
          <p className="text-sm text-[var(--rzp-text-muted)]">
            Empirically diagnose how autonomous AI buyer personas discover, evaluate, and rank your catalogue.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={runSimulation} isLoading={simulating} variant="ai" className="px-5">
            <Play className="h-4 w-4 mr-2" /> Run Simulation
          </Button>
        </div>
      </div>
      
      {/* Simulation Truth & Safety Notice */}
      <div className="bg-[var(--rzp-warning-soft)] p-3.5 rounded-lg border border-[var(--rzp-warning)] flex items-start text-xs text-[var(--rzp-warning)]">
        <ShieldAlert className="h-5 w-5 mr-2.5 shrink-0" />
        <div>
          <p className="font-semibold text-sm">Simulated Analytical Environment</p>
          <p className="mt-0.5 text-[var(--rzp-text-secondary)]">
            All simulation scores, matches, and rejections are calculated by the deterministic AI evaluation engine. Results do <strong>NOT</strong> modify database catalogue state or fabricate production revenue.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-sm font-medium flex items-center">
          <AlertTriangle className="h-5 w-5 mr-2 shrink-0" />
          {error}
        </div>
      )}

      {/* Simulation Configuration Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center">
              <Sliders className="h-4 w-4 mr-2 text-[var(--rzp-primary)]" /> Simulation Parameters
            </CardTitle>
            <span className="text-xs text-[var(--rzp-text-muted)]">Target: Active Catalogue Items</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-2">
              Select Target Buyer Personas
            </label>
            <div className="flex flex-wrap gap-2">
              {['BUDGET', 'SPEED', 'QUALITY', 'FEATURE', 'BALANCED'].map(profile => {
                const isSelected = selectedProfiles.includes(profile);
                return (
                  <button
                    key={profile}
                    type="button"
                    onClick={() => toggleProfile(profile)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      isSelected
                        ? 'bg-[var(--rzp-ai-soft)] border-[var(--rzp-ai)] text-[var(--rzp-ai)] shadow-sm'
                        : 'bg-white border-[var(--rzp-border)] text-[var(--rzp-text-muted)] hover:bg-gray-50'
                    }`}
                  >
                    {profile === 'BUDGET' && '💰 Budget Conscious'}
                    {profile === 'SPEED' && '⚡ Speed First'}
                    {profile === 'QUALITY' && '⭐ Quality & Brand'}
                    {profile === 'FEATURE' && '🔍 Feature & Specs'}
                    {profile === 'BALANCED' && '⚖️ Balanced Buyer'}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-[var(--rzp-border)]">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-medium text-[var(--rzp-text-secondary)]">Scenario Volume:</span>
              {[5, 10, 20].map(cnt => (
                <button
                  key={cnt}
                  type="button"
                  onClick={() => setScenarioCount(cnt)}
                  className={`px-2.5 py-1 rounded text-xs font-semibold border ${
                    scenarioCount === cnt
                      ? 'bg-[var(--rzp-primary)] text-white border-[var(--rzp-primary)]'
                      : 'bg-white text-[var(--rzp-text-secondary)] border-[var(--rzp-border)] hover:bg-gray-50'
                  }`}
                >
                  {cnt} Scenarios
                </button>
              ))}
            </div>

            <div className="text-xs text-[var(--rzp-text-muted)]">
              Evaluates hard constraint filters + soft scoring trade-offs
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {simulating && (
        <Card className="border-[var(--rzp-ai)] shadow-[0_0_20px_rgba(124,58,237,0.08)] animate-pulse">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-[var(--rzp-ai-soft)] border-t-[var(--rzp-ai)] animate-spin"></div>
              <Bot className="h-6 w-6 text-[var(--rzp-ai)] absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[var(--rzp-text)]">
                Evaluating Persona Decision Trees...
              </h3>
              <p className="text-xs text-[var(--rzp-text-muted)] mt-1">
                Executing constraint checks across {scenarioCount} simulated buyer scenarios
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!results && !simulating && (
        <Card className="border-dashed bg-gray-50/50">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-14 h-14 bg-[var(--rzp-ai-soft)] rounded-full flex items-center justify-center mb-3 text-[var(--rzp-ai)]">
              <Bot className="h-7 w-7" />
            </div>
            <h3 className="text-base font-semibold text-[var(--rzp-text)]">No Active Simulation Run</h3>
            <p className="text-xs text-[var(--rzp-text-muted)] max-w-md mt-1">
              Select buyer personas above and click <strong>Run Simulation</strong> to diagnose how agents rank your products and where frictions occur.
            </p>
            <Button onClick={runSimulation} className="mt-5" variant="ai" size="sm">
              <Play className="h-4 w-4 mr-1.5" /> Start Simulation
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Live Simulation Results */}
      {results && !simulating && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <Card className="bg-[var(--rzp-ai-soft)] border-[var(--rzp-ai)]">
              <CardContent className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-bold text-[var(--rzp-ai)] uppercase tracking-wider">Simulated Match Rate</span>
                  <Bot className="h-4 w-4 text-[var(--rzp-ai)]" />
                </div>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">
                    {((results.summary_metrics.constraint_satisfaction_rate || 0) * 100).toFixed(1)}%
                  </p>
                  <span className="ml-2 text-xs font-semibold text-[var(--rzp-success)]">
                    {results.summary_metrics.successful_matches} of {results.summary_metrics.buyers_simulated} matched
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-bold text-[var(--rzp-text-muted)] uppercase tracking-wider">Average Persona Score</span>
                  <CheckCircle2 className="h-4 w-4 text-[var(--rzp-success)]" />
                </div>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">
                    {(
                      results.summary_metrics.average_score !== undefined
                        ? results.summary_metrics.average_score
                        : (results.results.reduce((acc, r) => acc + r.score, 0) / Math.max(results.results.length, 1))
                    ).toFixed(2)}
                  </p>
                  <span className="ml-2 text-xs text-[var(--rzp-text-muted)]">Scale 0.00 - 1.00</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-bold text-[var(--rzp-text-muted)] uppercase tracking-wider">Scenarios Evaluated</span>
                  <Filter className="h-4 w-4 text-[var(--rzp-primary)]" />
                </div>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">
                    {results.scenario_count}
                  </p>
                  <span className="ml-2 text-xs text-[var(--rzp-text-muted)]">Deterministic runs</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Friction Diagnostics Section */}
          {results.summary_metrics.friction_distribution && Object.keys(results.summary_metrics.friction_distribution).length > 0 && (
            <Card className="border-l-4 border-l-[var(--rzp-warning)]">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center text-[var(--rzp-text)]">
                    <AlertTriangle className="h-4 w-4 mr-2 text-[var(--rzp-warning)]" />
                    Detected Buyer Friction Distribution
                  </CardTitle>
                  <span className="text-xs font-semibold text-[var(--rzp-warning)] bg-[var(--rzp-warning-soft)] px-2.5 py-0.5 rounded-full">
                    {Object.values(results.summary_metrics.friction_distribution).reduce((a, b) => a + b, 0)} friction signals
                  </span>
                </div>
                <p className="text-xs text-[var(--rzp-text-muted)]">
                  Primary constraint bottlenecks and ranking penalties encountered by AI buyer personas.
                </p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
                  {Object.entries(results.summary_metrics.friction_distribution).map(([reason, count]) => (
                    <div key={reason} className="p-3 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-between">
                      <span className="text-xs font-medium text-[var(--rzp-text)] font-mono">{reason}</span>
                      <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-800 rounded">
                        {count} hits
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Detailed Persona Decision Logs */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base">Scenario Decision Logs</CardTitle>
                <p className="text-xs text-[var(--rzp-text-muted)]">
                  Inspect the step-by-step evaluation, product match, and constraint checks for each scenario.
                </p>
              </div>
              <Link to="/optimization">
                <Button variant="outline" size="sm">
                  <Sparkles className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-ai)]" /> View Recommendations
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {results.results.map((item, idx) => {
                  const isExpanded = expandedRow === idx;
                  const matchedProduct = item.selected_product_id ? productsMap[item.selected_product_id] : null;

                  return (
                    <div 
                      key={idx} 
                      className={`border rounded-lg p-4 transition-all ${
                        item.constraints_satisfied
                          ? 'border-[var(--rzp-border)] bg-white hover:border-gray-300'
                          : 'border-red-200 bg-red-50/20'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center space-x-3">
                          <span className="text-xs font-bold text-gray-400 font-mono">#{idx + 1}</span>
                          <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)]">
                            {item.persona_name}
                          </span>
                          <span className="text-sm font-semibold text-[var(--rzp-text)]">
                            {matchedProduct ? matchedProduct.name : 'No Product Matched'}
                          </span>
                          {matchedProduct && (
                            <span className="text-xs text-[var(--rzp-text-muted)] font-medium">
                              ({formatPrice(matchedProduct.price)})
                            </span>
                          )}
                        </div>

                        <div className="flex items-center space-x-3">
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full flex items-center ${
                            item.constraints_satisfied
                              ? 'bg-[var(--rzp-success-soft)] text-[var(--rzp-success)]'
                              : 'bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)]'
                          }`}>
                            {item.constraints_satisfied ? (
                              <>
                                <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Match Score: {(item.score * 100).toFixed(0)}%
                              </>
                            ) : (
                              <>
                                <XCircle className="h-3.5 w-3.5 mr-1" /> Rejection
                              </>
                            )}
                          </span>

                          <button
                            type="button"
                            onClick={() => setExpandedRow(isExpanded ? null : idx)}
                            className="p-1 hover:bg-gray-100 rounded text-gray-500"
                          >
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>

                      {/* Explanation String */}
                      <p className="text-xs text-[var(--rzp-text-secondary)] mt-2">
                        {item.explanation}
                      </p>

                      {/* Reason Codes */}
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {item.reason_codes.map(code => (
                          <span key={code} className="text-[11px] font-mono bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                            {code}
                          </span>
                        ))}
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="mt-4 pt-3 border-t border-dashed border-gray-200 text-xs space-y-3">
                          {item.frictions && item.frictions.length > 0 && (
                            <div>
                              <span className="font-semibold text-red-700 block mb-1">Detected Frictions:</span>
                              <div className="space-y-1">
                                {item.frictions.map((f, fIdx) => (
                                  <div key={fIdx} className="p-2 bg-red-50 text-red-800 rounded flex justify-between">
                                    <span>{f.description || f.reason}</span>
                                    <span className="font-bold">{f.severity || 'WARN'}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {item.rankings && item.rankings.length > 0 && (
                            <div>
                              <span className="font-semibold text-gray-700 block mb-1">Candidate Product Rankings:</span>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {item.rankings.map(r => {
                                  const p = productsMap[r.product_id];
                                  return (
                                    <div key={r.product_id} className="p-2 bg-gray-50 rounded border flex justify-between items-center">
                                      <span className="truncate max-w-[200px]">{p ? p.name : r.product_id}</span>
                                      <span className="font-mono font-bold text-[var(--rzp-primary)]">
                                        Rank #{r.rank} (Score: {r.score})
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Next Step CTA */}
          <div className="p-4 bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border)] rounded-lg flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-semibold text-[var(--rzp-text)]">Ready to resolve detected buyer frictions?</h4>
              <p className="text-xs text-[var(--rzp-text-muted)] mt-0.5">
                Review actionable recommendations and simulate price or delivery changes with the What-If tool.
              </p>
            </div>
            <Link to="/optimization">
              <Button variant="ai" size="sm" className="whitespace-nowrap">
                Review & Optimize <ArrowRight className="h-4 w-4 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
