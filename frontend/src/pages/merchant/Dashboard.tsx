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
  Users
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
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)]">AI Commerce Intelligence</h1>
          <p className="text-sm text-[var(--rzp-text-muted)] mt-1">
            Real-time merchant catalogue visibility and agentic buyer intelligence.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/simulation">
            <Button variant="ai" size="sm">
              <PlayIcon className="h-4 w-4 mr-1.5" /> Run Simulation
            </Button>
          </Link>
          <Link to="/buyer">
            <Button variant="outline" size="sm">
              <ShoppingBag className="h-4 w-4 mr-1.5" /> Test AI Buyer
            </Button>
          </Link>
        </div>
      </div>

      {/* Top Metrics Row - REAL Authoritative Data */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] flex items-center">
            <span className="w-2 h-2 rounded-full bg-[var(--rzp-success)] mr-2"></span>
            Real Catalogue Operations
          </h2>
          <span className="text-xs text-[var(--rzp-text-muted)] font-medium">Source: Canonical Database</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
          <Card>
            <CardContent className="p-5">
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Catalogue Items</span>
                <div className="p-2 bg-[var(--rzp-primary-soft)] rounded-lg text-[var(--rzp-primary)]">
                  <Package className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold text-[var(--rzp-text)]">
                  {loading ? '...' : (analytics?.total_products ?? 0)}
                </p>
                <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                  {loading ? '...' : (analytics?.active_products ?? 0)} active in discovery
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Available Stock</span>
                <div className="p-2 bg-[var(--rzp-success-soft)] rounded-lg text-[var(--rzp-success)]">
                  <Layers className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold text-[var(--rzp-text)]">
                  {loading ? '...' : (analytics?.total_inventory ?? 0).toLocaleString()}
                </p>
                <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                  Authoritative units
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Categories</span>
                <div className="p-2 bg-[var(--rzp-info-soft)] rounded-lg text-[var(--rzp-info)]">
                  <Activity className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold text-[var(--rzp-text)]">
                  {loading ? '...' : (analytics?.total_categories ?? 0)}
                </p>
                <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                  Active taxonomies
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Personas</span>
                <div className="p-2 bg-[var(--rzp-warning-soft)] rounded-lg text-[var(--rzp-warning)]">
                  <Users className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold text-[var(--rzp-text)]">
                  {loading ? '...' : (analytics?.total_personas ?? 0)}
                </p>
                <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                  Configured buyer types
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex justify-between items-start">
                <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Actionable Recs</span>
                <div className="p-2 bg-[var(--rzp-ai-soft)] rounded-lg text-[var(--rzp-ai)]">
                  <Sparkles className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold text-[var(--rzp-text)]">
                  {loading ? '...' : (analytics?.total_recommendations ?? 0)}
                </p>
                <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                  Evidence-backed
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Intelligence Pipeline Flow: Understand -> Simulate -> Optimize */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1: Simulations */}
        <Card className="flex flex-col justify-between hover:shadow-md transition-shadow border-t-4 border-t-[var(--rzp-ai)]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)] px-2 py-0.5 rounded">
                Step 1: Diagnose
              </span>
              <Bot className="h-5 w-5 text-[var(--rzp-ai)]" />
            </div>
            <CardTitle className="text-lg mt-2">Synthetic Buyer Simulation</CardTitle>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Evaluate how autonomous personas (Budget, Speed, Quality, Feature) evaluate your prices and delivery times.
            </p>
          </CardHeader>
          <CardContent>
            <div className="bg-[var(--rzp-surface-subtle)] p-3 rounded-lg border border-[var(--rzp-border)] text-xs text-[var(--rzp-text-secondary)] space-y-1.5">
              <div className="flex items-center text-[var(--rzp-text)] font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-[var(--rzp-success)] mr-1.5 shrink-0" />
                Deterministic Scoring Engine
              </div>
              <p>Detect hard constraint rejections & soft ranking frictions across 5 personas.</p>
            </div>
            <div className="mt-4">
              <Link to="/simulation">
                <Button variant="ai" className="w-full" size="sm">
                  Launch Simulator <ArrowRight className="h-4 w-4 ml-1.5" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Step 2: Recommendations */}
        <Card className="flex flex-col justify-between hover:shadow-md transition-shadow border-t-4 border-t-[var(--rzp-warning)]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider bg-[var(--rzp-warning-soft)] text-[var(--rzp-warning)] px-2 py-0.5 rounded">
                Step 2: Understand
              </span>
              <Sparkles className="h-5 w-5 text-[var(--rzp-warning)]" />
            </div>
            <CardTitle className="text-lg mt-2">Friction Insights & Recs</CardTitle>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Actionable recommendations derived from empirical buyer agent rejections in your catalogue.
            </p>
          </CardHeader>
          <CardContent>
            <div className="bg-[var(--rzp-surface-subtle)] p-3 rounded-lg border border-[var(--rzp-border)] text-xs text-[var(--rzp-text-secondary)] space-y-1.5">
              <div className="flex items-center text-[var(--rzp-text)] font-medium">
                <AlertCircle className="h-3.5 w-3.5 text-[var(--rzp-warning)] mr-1.5 shrink-0" />
                Evidence-Based Rationale
              </div>
              <p>
                {recommendations.length > 0
                  ? `${recommendations.length} optimization opportunities ready for review.`
                  : 'Run buyer simulations to automatically generate friction-based recommendations.'}
              </p>
            </div>
            <div className="mt-4">
              <Link to="/optimization">
                <Button variant="outline" className="w-full" size="sm">
                  View Recommendations <ArrowRight className="h-4 w-4 ml-1.5" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Step 3: What-If Experimentation */}
        <Card className="flex flex-col justify-between hover:shadow-md transition-shadow border-t-4 border-t-[var(--rzp-primary)]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider bg-[var(--rzp-primary-soft)] text-[var(--rzp-primary)] px-2 py-0.5 rounded">
                Step 3: Experiment
              </span>
              <TestTube className="h-5 w-5 text-[var(--rzp-primary)]" />
            </div>
            <CardTitle className="text-lg mt-2">What-If Optimization</CardTitle>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Simulate price drops, delivery promise improvements, or metadata enrichment in-memory with 0 database risk.
            </p>
          </CardHeader>
          <CardContent>
            <div className="bg-[var(--rzp-surface-subtle)] p-3 rounded-lg border border-[var(--rzp-border)] text-xs text-[var(--rzp-text-secondary)] space-y-1.5">
              <div className="flex items-center text-[var(--rzp-text)] font-medium">
                <CheckCircle2 className="h-3.5 w-3.5 text-[var(--rzp-primary)] mr-1.5 shrink-0" />
                Zero Production Mutation
              </div>
              <p>Compute expected baseline vs simulated selection rate deltas safely.</p>
            </div>
            <div className="mt-4">
              <Link to="/optimization">
                <Button variant="primary" className="w-full" size="sm">
                  Run What-If Analysis <ArrowRight className="h-4 w-4 ml-1.5" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Active Recommendation Highlight if available */}
      {recommendations.length > 0 && (
        <Card className="border-[var(--rzp-ai)] bg-gradient-to-r from-purple-50/50 via-white to-white">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5 text-[var(--rzp-ai)]" />
                <CardTitle className="text-base text-[var(--rzp-text)]">Top Optimization Opportunity</CardTitle>
              </div>
              <span className="text-xs font-semibold text-[var(--rzp-ai)] bg-[var(--rzp-ai-soft)] px-2.5 py-0.5 rounded-full">
                Confidence: {(recommendations[0].confidence * 100).toFixed(0)}%
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="space-y-1">
                <h4 className="font-semibold text-sm text-[var(--rzp-text)]">{recommendations[0].title}</h4>
                <p className="text-xs text-[var(--rzp-text-secondary)] max-w-2xl">{recommendations[0].reason}</p>
                <div className="flex items-center gap-4 text-xs font-medium pt-1 text-[var(--rzp-text-muted)]">
                  <span>Type: <strong className="text-[var(--rzp-text)]">{recommendations[0].type}</strong></span>
                  <span>Simulated Impact: <strong className="text-[var(--rzp-success)]">+{(recommendations[0].expected_simulated_impact * 100).toFixed(0)}%</strong></span>
                </div>
              </div>
              <Link to="/optimization">
                <Button variant="ai" size="sm" className="whitespace-nowrap">
                  Test with What-If <ArrowRight className="h-4 w-4 ml-1.5" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const PlayIcon = (props: any) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="5 3 19 12 5 21 5 3" />
  </svg>
);
