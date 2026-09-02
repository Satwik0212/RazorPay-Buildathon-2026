import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { 
  BarChart2, 
  Layers, 
  CheckCircle2, 
  AlertCircle,
  Bot,
  Sparkles,
  TrendingDown,
  Activity,
  ArrowRight,
  Package,
  Users
} from 'lucide-react';
import { analyticsApi } from '../../api/analytics';
import type { MerchantIntelligenceAnalytics } from '../../types';

export const Analytics = () => {
  const [data, setData] = useState<MerchantIntelligenceAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await analyticsApi.getIntelligence();
        setData(res.data);
      } catch (err) {
        console.error('Failed to load analytics data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 text-[var(--rzp-text-muted)]">
        Loading intelligence data...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col justify-center items-center h-64 text-[var(--rzp-text-muted)]">
        <p>Failed to load intelligence data.</p>
        <Button className="mt-4" onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  const { overview, persona_performance, friction_breakdown, product_intelligence, recommendation_lifecycle } = data;
  
  const hasSimulations = persona_performance.length > 0;
  const hasRecommendations = (overview.total_recommendations) > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
            <Activity className="h-6 w-6 mr-2 text-[var(--rzp-primary)]" /> Merchant Intelligence
          </h1>
          <p className="text-sm text-[var(--rzp-text-muted)]">
            Empirical discovery metrics from AI buyer simulations.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/optimization">
            <Button variant="outline" size="sm">
              <Sparkles className="h-4 w-4 mr-1.5" /> Optimizations
            </Button>
          </Link>
          <Link to="/simulation">
            <Button variant="ai" size="sm">
              <Bot className="h-4 w-4 mr-1.5" /> Run Simulation
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Catalogue</span>
              <Package className="h-4 w-4 text-[var(--rzp-primary)]" />
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-[var(--rzp-text)]">{overview.active_products} / {overview.total_products}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">Active products</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Personas</span>
              <Users className="h-4 w-4 text-[var(--rzp-success)]" />
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-[var(--rzp-text)]">{overview.total_personas}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">Known AI buyers</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Inventory</span>
              <Layers className="h-4 w-4 text-[var(--rzp-warning)]" />
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-[var(--rzp-text)]">{overview.total_inventory}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">Units available</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Recommendations</span>
              <Sparkles className="h-4 w-4 text-[var(--rzp-ai)]" />
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-[var(--rzp-text)]">{overview.total_recommendations}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">Generated actions</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {!hasSimulations ? (
        <Card className="bg-[var(--rzp-surface-subtle)] border-dashed">
          <CardContent className="p-10 flex flex-col items-center justify-center text-center">
            <Bot className="h-12 w-12 text-[var(--rzp-text-muted)] mb-4" />
            <h3 className="text-lg font-bold text-[var(--rzp-text)] mb-2">Run a buyer simulation to generate merchant intelligence.</h3>
            <p className="text-[var(--rzp-text-secondary)] max-w-md mb-6">
              Intelligence is derived from actual deterministic buyer simulations against your products. Run your first simulation to discover friction.
            </p>
            <Link to="/simulation">
              <Button variant="ai">Run Simulation</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Buyer Persona Performance */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center">
                <Users className="h-4 w-4 mr-2 text-[var(--rzp-primary)]" /> Buyer Persona Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {persona_performance.map((p) => (
                  <div key={p.persona_name} className="border border-[var(--rzp-border)] rounded-md p-3">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-semibold text-sm">{p.persona_name}</h4>
                      <span className="text-xs px-2 py-1 bg-[var(--rzp-surface-subtle)] rounded-full">
                        {p.matches} matches / {p.rejections} rejections
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-[var(--rzp-text-secondary)]">
                      <span>Avg Score: {(p.average_score * 100).toFixed(0)}%</span>
                      <span>Total runs: {p.total_simulations}</span>
                    </div>
                    {p.top_frictions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-[var(--rzp-border-light)]">
                        <p className="text-xs text-[var(--rzp-warning)] flex items-center">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Top friction: {p.top_frictions[0].replace(/_/g, ' ')}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Friction & Recommendations */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center">
                  <TrendingDown className="h-4 w-4 mr-2 text-[var(--rzp-warning)]" /> Friction Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                {friction_breakdown.length === 0 ? (
                  <p className="text-sm text-[var(--rzp-text-muted)] text-center py-4">No actionable friction detected yet.</p>
                ) : (
                  <div className="space-y-3">
                    {friction_breakdown.map((f) => (
                      <div key={f.friction_type} className="flex justify-between items-center text-sm">
                        <span className="capitalize">{f.friction_type.replace(/_/g, ' ')}</span>
                        <span className="font-semibold px-2 py-0.5 bg-[var(--rzp-surface-subtle)] rounded text-xs">{f.count} occurrences</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center">
                  <CheckCircle2 className="h-4 w-4 mr-2 text-[var(--rzp-success)]" /> Recommendation Lifecycle
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between text-center">
                  <div>
                    <p className="text-2xl font-bold text-[var(--rzp-primary)]">{recommendation_lifecycle.proposed}</p>
                    <p className="text-xs text-[var(--rzp-text-secondary)] uppercase">Proposed</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-[var(--rzp-success)]">{recommendation_lifecycle.applied}</p>
                    <p className="text-xs text-[var(--rzp-text-secondary)] uppercase">Applied</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-[var(--rzp-text-muted)]">{recommendation_lifecycle.rejected}</p>
                    <p className="text-xs text-[var(--rzp-text-secondary)] uppercase">Rejected</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Product Intelligence */}
      {hasRecommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center">
              <BarChart2 className="h-4 w-4 mr-2 text-[var(--rzp-primary)]" /> Product-Level Intelligence
            </CardTitle>
          </CardHeader>
          <CardContent>
            {product_intelligence.length === 0 ? (
              <p className="text-sm text-[var(--rzp-text-muted)] text-center py-4">No product-specific recommendations available.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-[var(--rzp-text-muted)] uppercase bg-[var(--rzp-surface-subtle)] border-b border-[var(--rzp-border)]">
                    <tr>
                      <th className="px-4 py-3">Product</th>
                      <th className="px-4 py-3">Problem</th>
                      <th className="px-4 py-3">Evidence</th>
                      <th className="px-4 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {product_intelligence.map((intel) => (
                      <tr key={intel.recommendation_id} className="border-b border-[var(--rzp-border-light)] hover:bg-[var(--rzp-surface-subtle)] transition-colors">
                        <td className="px-4 py-3 font-medium text-[var(--rzp-text)]">{intel.product_name}</td>
                        <td className="px-4 py-3 text-[var(--rzp-warning)]">{intel.problem}</td>
                        <td className="px-4 py-3 text-[var(--rzp-text-secondary)] max-w-xs truncate" title={intel.evidence}>{intel.evidence}</td>
                        <td className="px-4 py-3">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="text-[var(--rzp-primary)]"
                            onClick={() => navigate('/optimization')}
                          >
                            {intel.recommended_action}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
