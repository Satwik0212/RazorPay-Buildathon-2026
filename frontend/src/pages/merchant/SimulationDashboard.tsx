import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import {
  Bot,
  Play,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  Filter,
  Sliders,
  Lightbulb,
  Scale,
  TrendingUp,
  TrendingDown,
  Minus,
  Package,
  PenLine
} from 'lucide-react';
import { simulationApi } from '../../api/simulation';
import { personasApi } from '../../api/personas';
import { productsApi } from '../../api/products';
import { authApi } from '../../api/auth';
import type { BuyerPersona, Product, SimulationResponse, CustomBuyerConfig } from '../../types';
import { RecommendationPipelineHeader, type PipelineStepId } from '../../components/features/recommendations';
import { ScenarioDecisionLog } from '../../components/features/simulation';
import CustomSimulationModal from '../../components/features/simulation/CustomSimulationModal';


export const SimulationDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const stepParam = searchParams.get('step') as PipelineStepId | null;
  const currentStep: PipelineStepId = (stepParam === 'friction') ? 'friction' : 'simulation';

  const [simulating, setSimulating] = useState(false);
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [results, setResults] = useState<SimulationResponse | null>(null);

  const [baselineRun, setBaselineRun] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState('');

  // Personas & Products
  const [personas, setPersonas] = useState<BuyerPersona[]>([]);
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [scenarioCount, setScenarioCount] = useState<number>(10);
  const [productsMap, setProductsMap] = useState<Record<string, Product>>({});
  const [totalCatalogueProducts, setTotalCatalogueProducts] = useState<number>(2977);

  // Restore previous run or baseline from sessionStorage
  useEffect(() => {
    try {
      const savedBaseline = sessionStorage.getItem('simulation_baseline_run');
      if (savedBaseline) {
        setBaselineRun(JSON.parse(savedBaseline));
      }
    } catch {
      // ignore
    }
  }, []);

  // Scroll to section when step param changes
  useEffect(() => {
    if (stepParam === 'friction') {
      const el = document.getElementById('friction-section') || document.getElementById('simulation-section');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (stepParam === 'simulation') {
      const el = document.getElementById('simulation-section');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  }, [stepParam, results]);

  // Auto-trigger a fresh simulation when navigated here with ?rerun=true
  // (e.g., after clicking "Re-run Simulation" on a recommendation card).
  // Clears the param immediately to prevent re-firing on subsequent renders.
  const rerunParam = searchParams.get('rerun');
  useEffect(() => {
    if (rerunParam === 'true') {
      // Remove the rerun param first to prevent infinite loop
      setSearchParams({ step: 'simulation' }, { replace: true });
      // Slight delay to let the param removal complete before kicking off the sim
      setTimeout(() => {
        runSimulation();
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rerunParam]);

  const handleStepClick = (step: PipelineStepId) => {
    if (step === 'simulation') {
      setSearchParams({ step: 'simulation' });
      const el = document.getElementById('simulation-section');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (step === 'friction') {
      setSearchParams({ step: 'friction' });
      const el = document.getElementById('friction-section') || document.getElementById('simulation-section');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    } else if (step === 'insight') {
      navigate('/optimization?step=insight');
    } else if (step === 'action') {
      navigate('/optimization?step=action');
    }
  };

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [personaRes, productRes] = await Promise.all([
          personasApi.getPersonas().catch(() => ({ data: [] })),
          productsApi.getProducts({ limit: 100 }).catch(() => ({ data: { items: [], total: 2977 } })),
        ]);

        if (personaRes.data && personaRes.data.length > 0) {
          setPersonas(personaRes.data);
          setSelectedProfiles(personaRes.data.map((p: BuyerPersona) => p.name.split(' ')[0].toUpperCase()));
        }

        const totalCount = productRes.data?.total || 2977;
        setTotalCatalogueProducts(totalCount);

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
        if (prev.length === 1) return prev;
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
      if (results) {
        setBaselineRun(results);
        try {
          sessionStorage.setItem('simulation_baseline_run', JSON.stringify(results));
        } catch {
          // ignore
        }
      }

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

  const runCustomSimulation = async (config: CustomBuyerConfig) => {
    setIsCustomModalOpen(false);
    setSimulating(true);
    setError('');
    try {
      if (results) {
        setBaselineRun(results);
        try {
          sessionStorage.setItem('simulation_baseline_run', JSON.stringify(results));
        } catch {
          // ignore
        }
      }

      const res = await simulationApi.runSimulation({ custom_buyer: config });
      setResults(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Custom simulation failed to execute.');
    } finally {
      setSimulating(false);
    }
  };



  const getPersonaIcon = (name: string) => {
    const n = name.toUpperCase();
    if (n.includes('BUDGET')) return '💰';
    if (n.includes('SPEED')) return '⚡';
    if (n.includes('QUALITY')) return '⭐';
    if (n.includes('FEATURE')) return '🔍';
    if (n.includes('BALANCED')) return '⚖️';
    return '🤖';
  };

  const totalFrictionSignals = results?.summary_metrics?.friction_distribution
    ? Object.values(results.summary_metrics.friction_distribution).reduce((a, b) => a + b, 0)
    : 0;

  const baselineFrictionSignals = baselineRun?.summary_metrics?.friction_distribution
    ? Object.values(baselineRun.summary_metrics.friction_distribution).reduce((a, b) => a + b, 0)
    : 0;

  const matchRateDelta = results && baselineRun
    ? Number((((results.summary_metrics.constraint_satisfaction_rate || 0) - (baselineRun.summary_metrics.constraint_satisfaction_rate || 0)) * 100).toFixed(1))
    : null;

  const avgScoreDelta = results && baselineRun
    ? Number(((results.summary_metrics.average_score || 0) - (baselineRun.summary_metrics.average_score || 0)).toFixed(2))
    : null;


  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center tracking-tight">
            <Bot className="h-6 w-6 mr-2.5 text-[var(--rzp-ai)]" /> Synthetic Buyer Simulation
          </h1>
          <p className="text-sm text-[var(--rzp-text-muted)] mt-1">
            Empirically diagnose how autonomous AI buyer personas discover, evaluate, and rank your catalogue.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsCustomModalOpen(true)}
            disabled={simulating}
            className="px-4 py-2 text-xs font-semibold border border-[var(--rzp-ai)] text-[var(--rzp-ai)] rounded-lg hover:bg-[var(--rzp-ai-soft)] transition-colors flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PenLine className="h-3.5 w-3.5" />
            Custom Simulation
          </button>
          <Button onClick={runSimulation} isLoading={simulating} variant="ai" className="px-5 shadow-sm font-semibold">
            <Play className="h-4 w-4 mr-2" /> Run Simulation
          </Button>
        </div>
      </div>

      {/* Visual Analytical Pipeline Header */}
      <RecommendationPipelineHeader currentStep={currentStep} onStepClick={handleStepClick} />

      {/* Simulation Truth & Safety Notice */}
      <div className="bg-[var(--rzp-warning-soft)] p-3.5 rounded-lg border border-[var(--rzp-warning)] flex items-start text-xs text-[var(--rzp-warning)]">
        <ShieldAlert className="h-5 w-5 mr-2.5 shrink-0" />
        <div>
          <p className="font-semibold text-sm text-[var(--rzp-text)]">Simulated Analytical Environment</p>
          <p className="mt-0.5 text-[var(--rzp-text-secondary)]">
            All simulation scores, matches, and rejections are calculated by the deterministic AI evaluation engine. Results reflect simulated persona constraint satisfaction and do <strong>NOT</strong> fabricate production revenue.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-sm font-medium flex items-center border border-red-200">
          <AlertTriangle className="h-5 w-5 mr-2 shrink-0" />
          {error}
        </div>
      )}

      {/* Simulation Configuration Card */}
      <div id="simulation-section" className="scroll-mt-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center font-bold">
                <Sliders className="h-4 w-4 mr-2 text-[var(--rzp-primary)]" /> Simulation Parameters
              </CardTitle>
              <span className="text-xs text-[var(--rzp-text-muted)] font-medium">Target: Active Catalogue Items</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-[var(--rzp-text-muted)] block mb-2">
                Select Target Buyer Personas
              </label>
              <div className="flex flex-wrap gap-2">
                {personas.map(persona => {
                  const profileCode = persona.name.split(' ')[0].toUpperCase();
                  const isSelected = selectedProfiles.includes(profileCode);
                  return (
                    <button
                      key={persona.id}
                      type="button"
                      onClick={() => toggleProfile(profileCode)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                        isSelected
                          ? 'bg-[var(--rzp-ai-soft)] border-[var(--rzp-ai)] text-[var(--rzp-ai)] shadow-xs'
                          : 'bg-white border-[var(--rzp-border)] text-[var(--rzp-text-muted)] hover:bg-gray-50'
                      }`}
                    >
                      {getPersonaIcon(persona.name)} {persona.name}
                    </button>
                  );
                })}
                {personas.length === 0 && (
                  <span className="text-xs text-gray-500 italic">Loading personas from database...</span>
                )}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-[var(--rzp-border)]">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-semibold text-[var(--rzp-text-secondary)]">Scenario Volume:</span>
                {[5, 10, 20].map(cnt => (
                  <button
                    key={cnt}
                    type="button"
                    onClick={() => setScenarioCount(cnt)}
                    className={`px-3 py-1 rounded-md text-xs font-bold border transition-all ${
                      scenarioCount === cnt
                        ? 'bg-[var(--rzp-primary)] text-white border-[var(--rzp-primary)] shadow-2xs'
                        : 'bg-white text-[var(--rzp-text-secondary)] border-[var(--rzp-border)] hover:bg-gray-50'
                    }`}
                  >
                    {cnt} Scenarios
                  </button>
                ))}
              </div>

              <div className="text-xs text-[var(--rzp-text-muted)] font-medium">
                Evaluates hard constraint filters + soft scoring trade-offs
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Loading State */}
      {simulating && (
        <Card className="border-[var(--rzp-ai)] shadow-[0_0_20px_rgba(124,58,237,0.08)] animate-pulse">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-[var(--rzp-ai-soft)] border-t-[var(--rzp-ai)] animate-spin"></div>
              <Bot className="h-6 w-6 text-[var(--rzp-ai)] absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[var(--rzp-text)]">
                Evaluating Persona Decision Trees...
              </h3>
              <p className="text-xs text-[var(--rzp-text-muted)] mt-1">
                Executing constraint checks across {scenarioCount} simulated buyer scenarios against live catalogue state
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
              Choose a predefined buyer persona below, or create your own custom AI buyer to diagnose how agents rank your products.
            </p>
            <div className="flex items-center gap-3 mt-5">
              <Button onClick={runSimulation} variant="ai" size="sm">
                <Play className="h-4 w-4 mr-1.5" /> Start Simulation
              </Button>
              <button
                type="button"
                onClick={() => setIsCustomModalOpen(true)}
                className="px-4 py-1.5 text-xs font-semibold border border-[var(--rzp-ai)] text-[var(--rzp-ai)] rounded-lg hover:bg-[var(--rzp-ai-soft)] transition-colors flex items-center gap-1.5"
              >
                <PenLine className="h-3.5 w-3.5" /> Custom Simulation
              </button>
            </div>
          </CardContent>
        </Card>
      )}


      {/* Live Simulation Results */}
      {results && !simulating && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Custom simulation result banner */}
          {results.summary_metrics?.metric_type === 'CUSTOM SIMULATION' && (
            <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-fuchsia-50 via-purple-50 to-indigo-50 border border-fuchsia-200 rounded-xl text-sm">
              <span className="text-xl shrink-0">🎯</span>
              <div className="flex-1 min-w-0">
                <span className="font-bold text-fuchsia-800">
                  Custom Buyer Simulation — "{results.summary_metrics.custom_buyer_name}"
                </span>
                <span className="text-fuchsia-600 text-xs ml-2">
                  {results.scenario_count} scenario{results.scenario_count !== 1 ? 's' : ''} ·{' '}
                  {Math.round((results.summary_metrics.constraint_satisfaction_rate || 0) * 100)}% match rate ·{' '}
                  Avg score {Math.round((results.summary_metrics.average_score || 0) * 100)}%
                </span>
              </div>
              <span className="text-[11px] bg-fuchsia-100 text-fuchsia-700 border border-fuchsia-200 px-2 py-0.5 rounded-full font-semibold shrink-0">
                CUSTOM
              </span>
            </div>
          )}

          {/* SECTION: BEFORE vs AFTER SIMULATION COMPARISON (WHEN BASELINE EXISTS) */}

          {baselineRun && (
            <Card className="border-2 border-[var(--rzp-primary)] shadow-sm bg-gradient-to-br from-white via-purple-50/20 to-white">
              <CardHeader className="pb-3 border-b border-[var(--rzp-border)]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <Scale className="h-5 w-5 text-[var(--rzp-primary)]" />
                    <CardTitle className="text-base font-bold text-[var(--rzp-text)]">
                      Before vs After Simulation Evaluation
                    </CardTitle>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-purple-100 text-purple-900 px-2 py-0.5 rounded border border-purple-200">
                      SIMULATED RESULT
                    </span>
                    <Link to="/transactions" className="text-xs text-[var(--rzp-primary)] font-semibold hover:underline">
                      Audit Trail →
                    </Link>
                  </div>
                </div>
                <p className="text-xs text-[var(--rzp-text-muted)]">
                  Measured comparison between the baseline simulation and the post-intervention simulation.
                </p>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                {/* Metric Delta Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  {/* Match Rate */}
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                      Simulated Match Rate
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-gray-400 line-through">
                        {((baselineRun.summary_metrics.constraint_satisfaction_rate || 0) * 100).toFixed(1)}%
                      </span>
                      <ArrowRight className="h-3 w-3 text-gray-400 inline" />
                      <span className="text-base font-black text-[var(--rzp-text)]">
                        {((results.summary_metrics.constraint_satisfaction_rate || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                    {matchRateDelta !== null && (
                      <div className={`text-[11px] font-bold flex items-center ${
                        matchRateDelta > 0 ? 'text-emerald-600' : matchRateDelta === 0 ? 'text-gray-500' : 'text-amber-600'
                      }`}>
                        {matchRateDelta > 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : matchRateDelta === 0 ? <Minus className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                        {matchRateDelta > 0 ? `+${matchRateDelta}% Delta` : `${matchRateDelta}% Delta`}
                      </div>
                    )}
                  </div>

                  {/* Avg Persona Score */}
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                      Avg Persona Score
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-gray-400 line-through">
                        {(baselineRun.summary_metrics.average_score || 0).toFixed(2)}
                      </span>
                      <ArrowRight className="h-3 w-3 text-gray-400 inline" />
                      <span className="text-base font-black text-[var(--rzp-text)]">
                        {(results.summary_metrics.average_score || 0).toFixed(2)}
                      </span>
                    </div>
                    {avgScoreDelta !== null && (
                      <div className={`text-[11px] font-bold flex items-center ${
                        avgScoreDelta > 0 ? 'text-emerald-600' : avgScoreDelta === 0 ? 'text-gray-500' : 'text-amber-600'
                      }`}>
                        {avgScoreDelta > 0 ? `+${avgScoreDelta} Score Delta` : `${avgScoreDelta} Score Delta`}
                      </div>
                    )}
                  </div>

                  {/* Friction Count */}
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
                      Total Friction Signals
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-gray-400 line-through">{baselineFrictionSignals.toLocaleString()}</span>
                      <ArrowRight className="h-3 w-3 text-gray-400 inline" />
                      <span className="text-base font-black text-[var(--rzp-danger)]">{totalFrictionSignals.toLocaleString()}</span>
                    </div>
                    <span className="text-[11px] text-gray-500">
                      {totalFrictionSignals < baselineFrictionSignals
                        ? `Reduced by ${(baselineFrictionSignals - totalFrictionSignals).toLocaleString()} signals`
                        : `${totalFrictionSignals.toLocaleString()} total signals (a product can contribute multiple signals)`}
                    </span>
                  </div>
                </div>

                {/* Honest Verdict Banner */}
                <div className={`p-3 rounded-lg text-xs font-semibold border ${
                  matchRateDelta !== null && matchRateDelta > 0
                    ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                    : matchRateDelta === 0
                    ? 'bg-gray-100 text-gray-700 border-gray-300'
                    : 'bg-amber-50 text-amber-900 border-amber-200'
                }`}>
                  {matchRateDelta !== null && matchRateDelta > 0 ? (
                    <span>
                      ✓ <strong>SIMULATED IMPROVEMENT:</strong> Constraint satisfaction increased from{' '}
                      {((baselineRun.summary_metrics.constraint_satisfaction_rate || 0) * 100).toFixed(1)}% to{' '}
                      {((results.summary_metrics.constraint_satisfaction_rate || 0) * 100).toFixed(1)}% (+{matchRateDelta}%) across evaluated buyer scenarios.
                    </span>
                  ) : matchRateDelta === 0 ? (
                    <span>
                      ℹ <strong>No measurable improvement observed in this simulation.</strong> Buyer persona constraints produced identical match counts under current scenario configurations.
                    </span>
                  ) : (
                    <span>
                      ⚠ <strong>Simulated match rate shifted:</strong> {matchRateDelta}%. Review persona trade-offs and constraint sensitivities.
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Transition Highlight Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-purple-50 via-indigo-50 to-white border border-[var(--rzp-ai)] flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-[var(--rzp-ai)] text-white flex items-center justify-center shrink-0 shadow-xs">
                <Lightbulb className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[var(--rzp-text)]">
                  Simulation Complete: {totalFrictionSignals.toLocaleString()} Friction {totalFrictionSignals === 1 ? 'Signal' : 'Signals'} Detected
                </h3>
                <p className="text-xs text-[var(--rzp-text-secondary)]">
                  Evaluated across catalogue products. A product can contribute multiple friction signals.
                </p>
              </div>
            </div>

            <Link to="/optimization?step=action">
              <Button variant="primary" size="sm" className="whitespace-nowrap shadow-sm font-semibold">
                <Sparkles className="h-3.5 w-3.5 mr-1.5" /> View Recommendations (Step 4) <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </Link>
          </div>

          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-[var(--rzp-ai-soft)] border-[var(--rzp-ai)]">
              <CardContent className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-bold text-[var(--rzp-ai)] uppercase tracking-wider">Simulated Match Rate</span>
                  <Bot className="h-4 w-4 text-[var(--rzp-ai)]" />
                </div>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-extrabold text-[var(--rzp-text)]">
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
                  <p className="text-3xl font-extrabold text-[var(--rzp-text)]">
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
                  <span className="text-xs font-bold text-[var(--rzp-text-muted)] uppercase tracking-wider">Products Analyzed</span>
                  <Package className="h-4 w-4 text-[var(--rzp-primary)]" />
                </div>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-extrabold text-[var(--rzp-text)]">
                    {totalCatalogueProducts.toLocaleString()}
                  </p>
                  <span className="ml-2 text-xs text-[var(--rzp-text-muted)]">Active SKUs</span>
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
                  <p className="text-3xl font-extrabold text-[var(--rzp-text)]">
                    {results.scenario_count}
                  </p>
                  <span className="ml-2 text-xs text-[var(--rzp-text-muted)]">Deterministic runs</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Friction Diagnostics Section (STEP 2: BUYER FRICTION) */}
          {results.summary_metrics.friction_distribution && Object.keys(results.summary_metrics.friction_distribution).length > 0 && (
            <div id="friction-section" className="scroll-mt-6">
              <Card className="border-l-4 border-l-[var(--rzp-warning)]">
                <CardHeader className="pb-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <CardTitle className="text-base flex items-center text-[var(--rzp-text)] font-bold">
                      <AlertTriangle className="h-4 w-4 mr-2 text-[var(--rzp-warning)]" />
                      Detected Buyer Friction Distribution (Stage 02)
                    </CardTitle>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                        {totalCatalogueProducts.toLocaleString()} Products Analyzed
                      </span>
                      <span className="text-xs font-semibold text-[var(--rzp-warning)] bg-[var(--rzp-warning-soft)] px-2.5 py-0.5 rounded-full border border-amber-200">
                        {totalFrictionSignals.toLocaleString()} Friction Signals
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-[var(--rzp-text-muted)]">
                    Evaluated <strong>{totalCatalogueProducts.toLocaleString()} Products Analyzed</strong> across {results.scenario_count} buyer scenarios ({totalFrictionSignals.toLocaleString()} total friction signals). A single product can contribute multiple friction signals.
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
                    {Object.entries(results.summary_metrics.friction_distribution).map(([reason, count]) => (
                      <div key={reason} className="p-3 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-between">
                        <span className="text-xs font-semibold text-[var(--rzp-text)] font-mono">{reason}</span>
                        <span className="text-xs font-bold px-2 py-0.5 bg-amber-100 text-amber-800 rounded">
                          {count.toLocaleString()} friction signals
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Detailed Persona Decision Logs */}
          <div id="logs-section" className="scroll-mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle className="text-base font-bold">Scenario Decision Logs</CardTitle>
                  <p className="text-xs text-[var(--rzp-text-muted)]">
                    Inspect the step-by-step evaluation, product match, and constraint checks for each scenario.
                  </p>
                </div>
                <Link to="/optimization?step=action">
                  <Button variant="outline" size="sm" className="font-semibold">
                    <Sparkles className="h-3.5 w-3.5 mr-1.5 text-[var(--rzp-ai)]" /> View Recommendations
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {results.results.map((item, idx) => (
                    <ScenarioDecisionLog
                      key={`${item.persona_name}-${idx}`}
                      item={item}
                      index={idx}
                      productsMap={productsMap}
                      isExpandedDefault={idx === 0}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Next Step CTA */}
          <div className="p-5 bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border)] rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
            <div>
              <h4 className="text-sm font-bold text-[var(--rzp-text)]">Ready to resolve detected buyer frictions?</h4>
              <p className="text-xs text-[var(--rzp-text-muted)] mt-0.5">
                Review actionable recommendations and simulate price or delivery changes with the What-If tool.
              </p>
            </div>
            <Link to="/optimization?step=action">
              <Button variant="ai" size="sm" className="whitespace-nowrap shadow-sm font-semibold">
                Review & Optimize (Step 4) <ArrowRight className="h-4 w-4 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Custom Simulation Modal (portal-like fixed overlay) */}
      <CustomSimulationModal
        isOpen={isCustomModalOpen}
        onClose={() => setIsCustomModalOpen(false)}
        onSubmit={runCustomSimulation}
        isLoading={simulating}
      />
    </div>
  );
};
