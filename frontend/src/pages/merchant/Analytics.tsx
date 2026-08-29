import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { 
  LineChart, 
  BarChart2, 
  Layers, 
  ShieldAlert, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle,
  Bot,
  Sparkles
} from 'lucide-react';
import { productsApi } from '../../api/products';
import { simulationApi } from '../../api/simulation';
import { authApi } from '../../api/auth';
import type { Product, Recommendation } from '../../types';

export const Analytics = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [prodRes, merchantId] = await Promise.all([
          productsApi.getProducts(),
          authApi.getOrInitMerchantId()
        ]);
        setProducts(prodRes.data.items || []);

        try {
          const recRes = await simulationApi.getRecommendations();
          setRecommendations(recRes.data || []);
        } catch {
          setRecommendations([]);
        }
      } catch (err) {
        console.error('Failed to load analytics data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Compute actual catalogue readiness statistics from real database items
  const totalProducts = products.length;
  const productsWithMetadata = products.filter(p => p.metadata && Object.keys(p.metadata).length > 0).length;
  const productsInStock = products.filter(p => (p.inventory?.available_quantity || 0) > 0).length;
  const metadataCompletenessRate = totalProducts > 0 ? Math.round((productsWithMetadata / totalProducts) * 100) : 0;
  const inStockRate = totalProducts > 0 ? Math.round((productsInStock / totalProducts) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
            <LineChart className="h-6 w-6 mr-2 text-[var(--rzp-primary)]" /> Catalogue Readiness Analytics
          </h1>
          <p className="text-sm text-[var(--rzp-text-muted)]">
            Empirical diagnostic metrics for your AI agent discovery and transaction readiness.
          </p>
        </div>
        <Link to="/simulation">
          <Button variant="ai" size="sm">
            <Bot className="h-4 w-4 mr-1.5" /> Run Buyer Simulation
          </Button>
        </Link>
      </div>

      {/* Notice */}
      <div className="bg-[var(--rzp-surface-subtle)] p-3.5 rounded-lg border border-[var(--rzp-border)] flex items-start text-xs">
        <ShieldAlert className="h-5 w-5 text-[var(--rzp-primary)] mr-2.5 shrink-0" />
        <div className="text-[var(--rzp-text-secondary)]">
          <strong className="text-[var(--rzp-text)]">Zero Fabricated Traffic / Revenue: </strong>
          The metrics below represent real catalogue readiness scores calculated directly from your database records. Production GMV/Order aggregation will populate automatically as real payment webhooks arrive.
        </div>
      </div>

      {/* Catalogue Attribute Quality Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Metadata Richness</span>
              <Layers className="h-4 w-4 text-[var(--rzp-primary)]" />
            </div>
            <div className="mt-2">
              <p className="text-3xl font-bold text-[var(--rzp-text)]">{loading ? '...' : `${metadataCompletenessRate}%`}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                {productsWithMetadata} of {totalProducts} products have structured attributes
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Stock Availability</span>
              <CheckCircle2 className="h-4 w-4 text-[var(--rzp-success)]" />
            </div>
            <div className="mt-2">
              <p className="text-3xl font-bold text-[var(--rzp-text)]">{loading ? '...' : `${inStockRate}%`}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                {productsInStock} of {totalProducts} products ready for autonomous checkout
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">Active Friction Alerts</span>
              <AlertCircle className="h-4 w-4 text-[var(--rzp-warning)]" />
            </div>
            <div className="mt-2">
              <p className="text-3xl font-bold text-[var(--rzp-text)]">{loading ? '...' : recommendations.length}</p>
              <p className="text-xs text-[var(--rzp-text-secondary)] mt-1">
                {recommendations.length > 0 ? 'Friction detected in catalogue' : 'No active friction detected'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Readiness Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center">
            <BarChart2 className="h-4 w-4 mr-2 text-[var(--rzp-ai)]" /> AI Agent Discovery Factors
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex justify-between text-xs font-medium">
              <span>Structured Attribute Coverage (ANC, Warranty, Battery)</span>
              <span className="font-bold">{metadataCompletenessRate}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-[var(--rzp-ai)] h-2 rounded-full transition-all duration-500" style={{ width: `${metadataCompletenessRate}%` }}></div>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex justify-between text-xs font-medium">
              <span>Instant Inventory Availability</span>
              <span className="font-bold">{inStockRate}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-[var(--rzp-success)] h-2 rounded-full transition-all duration-500" style={{ width: `${inStockRate}%` }}></div>
            </div>
          </div>

          <div className="pt-4 border-t border-[var(--rzp-border)] flex items-center justify-between">
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Simulations run against these parameters to determine buyer persona rankings.
            </p>
            <Link to="/optimization">
              <Button variant="outline" size="sm">
                <Sparkles className="h-3.5 w-3.5 mr-1.5" /> Optimize Catalogue
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
