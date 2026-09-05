import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import {
  Package,
  Bot,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Layers,
  TestTube,
  ShoppingBag,
  Activity,
  Users,
  Database,
  RefreshCw,
  ChevronRight
} from 'lucide-react';
import { analyticsApi } from '../../api/analytics';
import { simulationApi } from '../../api/simulation';
import type { Recommendation, MerchantOverviewAnalytics } from '../../types';

export const Dashboard = () => {
  const [analytics, setAnalytics] = useState<MerchantOverviewAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const overviewRes = await analyticsApi.getOverview();
        setAnalytics(overviewRes.data);

        try {
          const recRes = await simulationApi.getRecommendations();
          setRecommendations(recRes.data || []);
        } catch {
          setRecommendations([]);
        }
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-10 pb-12">
      {/* Header section with connected status */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 pb-6 border-b border-[var(--rzp-border)]">
        <div className="space-y-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-[var(--rzp-text)] tracking-tight">GraahakLens Intelligence</h1>
            <div className="hidden sm:flex items-center px-2.5 py-1 rounded-full bg-[var(--rzp-success-soft)] border border-[var(--rzp-success)]/20">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--rzp-success)] mr-1.5 animate-pulse"></span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-success)]">System Active</span>
            </div>
          </div>
          <p className="text-base text-[var(--rzp-text-muted)] max-w-2xl">
            Real-time merchant catalogue visibility and agentic buyer intelligence.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Link to="/buyer">
            <Button variant="outline" size="sm" className="h-10 px-4 shadow-sm bg-white hover:bg-gray-50 border-gray-200">
              <ShoppingBag className="h-4 w-4 mr-2 text-[var(--rzp-text-muted)]" /> Test AI Buyer
            </Button>
          </Link>
          <Link to="/simulation">
            <Button variant="ai" size="sm" className="h-10 px-6 shadow-sm">
              <PlayIcon className="h-4 w-4 mr-2" /> Run Simulation
            </Button>
          </Link>
        </div>
      </div>

      {/* THREE-STEP CORE WORKFLOW - Moved up to dominate visual hierarchy */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[var(--rzp-text)] tracking-tight">Intelligence Workflow</h2>
        </div>

        {/* Connected Journey Container */}
        <div className="relative">
          {/* Subtle connection line behind cards (desktop only) */}
          <div className="hidden lg:block absolute top-[50%] left-[10%] right-[10%] h-[2px] bg-gradient-to-r from-[var(--rzp-border)] via-[var(--rzp-primary-soft)] to-[var(--rzp-border)] -z-10"></div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Step 1: Diagnose */}
            <Card className="flex flex-col h-full bg-white shadow-sm hover:shadow-md transition-all duration-200 border border-[var(--rzp-border)] relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--rzp-ai)]"></div>
              <CardContent className="p-6 flex flex-col h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-[var(--rzp-ai-soft)] flex items-center justify-center">
                    <Bot className="h-5 w-5 text-[var(--rzp-ai)]" />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-ai)] bg-[var(--rzp-ai-soft)] px-2 py-1 rounded">
                    Step 1
                  </span>
                </div>
                <div className="space-y-1 mb-6 flex-grow">
                  <h3 className="text-xl font-bold text-[var(--rzp-text)] tracking-tight">Diagnose</h3>
                  <p className="text-sm font-medium text-[var(--rzp-text)]">Synthetic Buyer Simulation</p>
                  <p className="text-sm text-[var(--rzp-text-muted)] pt-1">
                    See how autonomous buyers evaluate your catalogue based on distinct purchasing personas.
                  </p>
                </div>
                <div className="pt-4 border-t border-[var(--rzp-border)]">
                  <Link to="/simulation" className="flex items-center text-sm font-semibold text-[var(--rzp-ai)] group-hover:text-[var(--rzp-ai-dark)] transition-colors">
                    Launch Simulator <ArrowRight className="h-4 w-4 ml-1.5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Step 2: Understand */}
            <Card className="flex flex-col h-full bg-white shadow-sm hover:shadow-md transition-all duration-200 border border-[var(--rzp-border)] relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--rzp-warning)]"></div>
              <CardContent className="p-6 flex flex-col h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-[var(--rzp-warning-soft)] flex items-center justify-center">
                    <AlertCircle className="h-5 w-5 text-[var(--rzp-warning)]" />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-warning)] bg-[var(--rzp-warning-soft)] px-2 py-1 rounded">
                    Step 2
                  </span>
                </div>
                <div className="space-y-1 mb-6 flex-grow">
                  <h3 className="text-xl font-bold text-[var(--rzp-text)] tracking-tight">Understand</h3>
                  <p className="text-sm font-medium text-[var(--rzp-text)]">Friction Insights & Recs</p>
                  <p className="text-sm text-[var(--rzp-text-muted)] pt-1">
                    Understand why products lose out and review evidence-backed actions to improve.
                  </p>
                </div>
                <div className="pt-4 border-t border-[var(--rzp-border)]">
                  <Link to="/optimization" className="flex items-center text-sm font-semibold text-[var(--rzp-warning)] group-hover:text-yellow-700 transition-colors">
                    View Recommendations <ArrowRight className="h-4 w-4 ml-1.5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Step 3: Experiment */}
            <Card className="flex flex-col h-full bg-white shadow-sm hover:shadow-md transition-all duration-200 border border-[var(--rzp-border)] relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-[var(--rzp-primary)]"></div>
              <CardContent className="p-6 flex flex-col h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-[var(--rzp-primary-soft)] flex items-center justify-center">
                    <TestTube className="h-5 w-5 text-[var(--rzp-primary)]" />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-primary)] bg-[var(--rzp-primary-soft)] px-2 py-1 rounded">
                    Step 3
                  </span>
                </div>
                <div className="space-y-1 mb-6 flex-grow">
                  <h3 className="text-xl font-bold text-[var(--rzp-text)] tracking-tight">Experiment</h3>
                  <p className="text-sm font-medium text-[var(--rzp-text)]">What-If Optimization</p>
                  <p className="text-sm text-[var(--rzp-text-muted)] pt-1">
                    Test changes safely in-memory to compute expected ROI before making production mutations.
                  </p>
                </div>
                <div className="pt-4 border-t border-[var(--rzp-border)]">
                  <Link to="/optimization" className="flex items-center text-sm font-semibold text-[var(--rzp-primary)] group-hover:text-[var(--rzp-primary-dark)] transition-colors">
                    Run What-If Analysis <ArrowRight className="h-4 w-4 ml-1.5 transition-transform group-hover:translate-x-1" />
                  </Link>
                </div>
              </CardContent>
            </Card>

          </div>
        </div>
      </section>

      {/* KPI Section */}
      <section className="space-y-4 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-[var(--rzp-text)] tracking-tight">Operational Overview</h2>
          <div className="flex items-center text-xs text-[var(--rzp-text-muted)] font-medium bg-white px-3 py-1.5 rounded-md border border-[var(--rzp-border)] shadow-sm">
            <Database className="w-3.5 h-3.5 mr-1.5" /> Canonical Database Sync
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <Card className="bg-white shadow-sm border-[var(--rzp-border)] hover:border-[var(--rzp-primary)] transition-colors">
            <CardContent className="p-5 flex flex-col h-full justify-between gap-4">
              <div className="flex items-center justify-between">
                <div className="p-2 bg-gray-50 rounded-lg text-gray-600 border border-gray-100">
                  <Package className="h-4 w-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--rzp-text)] tracking-tight">
                  {loading ? '...' : (analytics?.total_products ?? 0)}
                </p>
                <p className="text-xs font-medium text-[var(--rzp-text-muted)] mt-1 uppercase tracking-wider">Catalogue Items</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm border-[var(--rzp-border)] hover:border-[var(--rzp-success)] transition-colors">
            <CardContent className="p-5 flex flex-col h-full justify-between gap-4">
              <div className="flex items-center justify-between">
                <div className="p-2 bg-[var(--rzp-success-soft)] rounded-lg text-[var(--rzp-success)] border border-[var(--rzp-success)]/10">
                  <Layers className="h-4 w-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--rzp-text)] tracking-tight">
                  {loading ? '...' : (analytics?.total_inventory ?? 0).toLocaleString()}
                </p>
                <p className="text-xs font-medium text-[var(--rzp-text-muted)] mt-1 uppercase tracking-wider">Available Stock</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm border-[var(--rzp-border)] hover:border-[var(--rzp-info)] transition-colors">
            <CardContent className="p-5 flex flex-col h-full justify-between gap-4">
              <div className="flex items-center justify-between">
                <div className="p-2 bg-[var(--rzp-info-soft)] rounded-lg text-[var(--rzp-info)] border border-[var(--rzp-info)]/10">
                  <Activity className="h-4 w-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--rzp-text)] tracking-tight">
                  {loading ? '...' : (analytics?.total_categories ?? 0)}
                </p>
                <p className="text-xs font-medium text-[var(--rzp-text-muted)] mt-1 uppercase tracking-wider">Categories</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm border-[var(--rzp-border)] hover:border-[var(--rzp-warning)] transition-colors">
            <CardContent className="p-5 flex flex-col h-full justify-between gap-4">
              <div className="flex items-center justify-between">
                <div className="p-2 bg-[var(--rzp-warning-soft)] rounded-lg text-[var(--rzp-warning)] border border-[var(--rzp-warning)]/10">
                  <Users className="h-4 w-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--rzp-text)] tracking-tight">
                  {loading ? '...' : (analytics?.total_personas ?? 0)}
                </p>
                <p className="text-xs font-medium text-[var(--rzp-text-muted)] mt-1 uppercase tracking-wider">Sim Personas</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-sm border-[var(--rzp-border)] hover:border-[var(--rzp-ai)] transition-colors">
            <CardContent className="p-5 flex flex-col h-full justify-between gap-4">
              <div className="flex items-center justify-between">
                <div className="p-2 bg-[var(--rzp-ai-soft)] rounded-lg text-[var(--rzp-ai)] border border-[var(--rzp-ai)]/10">
                  <Sparkles className="h-4 w-4" />
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--rzp-text)] tracking-tight">
                  {loading ? '...' : (analytics?.total_recommendations ?? 0)}
                </p>
                <p className="text-xs font-medium text-[var(--rzp-text-muted)] mt-1 uppercase tracking-wider">Active Recs</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Top Active Recommendation Highlight if available */}
      {recommendations.length > 0 && (
        <section className="pt-4">
          <Card className="border border-[var(--rzp-border)] bg-white shadow-sm overflow-hidden relative">
            <div className="absolute top-0 left-0 w-1 h-full bg-[var(--rzp-ai)]"></div>
            <CardContent className="p-0">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between p-6 gap-6">
                <div className="flex items-start gap-4">
                  <div className="mt-1 p-2 bg-[var(--rzp-ai-soft)] rounded-xl text-[var(--rzp-ai)] border border-[var(--rzp-ai)]/10 shrink-0">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-bold text-[var(--rzp-text)] tracking-tight">Top Optimization Opportunity</h3>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--rzp-ai)] bg-[var(--rzp-ai-soft)] px-2 py-0.5 rounded-full border border-[var(--rzp-ai)]/20">
                        {recommendations[0].type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-[var(--rzp-text)]">{recommendations[0].title}</p>
                    <p className="text-sm text-[var(--rzp-text-muted)] max-w-3xl leading-relaxed">{recommendations[0].reason}</p>
                  </div>
                </div>

                <div className="flex flex-col items-start md:items-end gap-3 shrink-0 bg-gray-50 p-4 rounded-xl border border-gray-100 w-full md:w-auto">
                  <div className="text-sm text-[var(--rzp-text-muted)]">
                    Simulated Impact: <strong className="text-[var(--rzp-success)] text-base ml-1">+{(recommendations[0].expected_simulated_impact * 100).toFixed(0)}%</strong>
                  </div>
                  <Link to="/optimization" className="w-full md:w-auto">
                    <Button variant="ai" size="sm" className="w-full">
                      Test with What-If <ChevronRight className="h-4 w-4 ml-1.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  );
};

const PlayIcon = (props: any) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="5 3 19 12 5 21 5 3" />
  </svg>
);
