import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Sparkles, ArrowRight, Loader2 } from 'lucide-react';
import { simulationApi } from '../../api/simulation';
import { authApi } from '../../api/auth';

export const Optimization = () => {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const meRes = await authApi.getMe();
        const merchantId = meRes.data.merchant_id;
        
        // Pass merchant ID properly or omit if none
        const res = await simulationApi.getRecommendations(merchantId || '');
        setRecommendations(res.data);
      } catch (err) {
        console.error('Failed to fetch recommendations');
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
          <Sparkles className="h-6 w-6 mr-2 text-[var(--rzp-ai)]" /> AI Optimizations
        </h1>
        <p className="text-sm text-[var(--rzp-text-muted)]">Actionable recommendations to improve your AI Commerce Readiness.</p>
      </div>

      {recommendations.length === 0 ? (
        <Card className="border-dashed bg-gray-50/50">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <h3 className="text-lg font-semibold text-[var(--rzp-text)]">No Recommendations Yet</h3>
            <p className="text-sm text-[var(--rzp-text-muted)] max-w-md mt-2">
              Run more simulations to generate actionable optimization insights.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {recommendations.map((rec: any) => (
            <Card key={rec.id} className={`border-l-4 ${rec.impact === 'HIGH' ? 'border-l-[var(--rzp-warning)]' : 'border-l-[var(--rzp-info)]'}`}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle>{rec.title}</CardTitle>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                    rec.impact === 'HIGH' 
                      ? 'bg-[var(--rzp-warning-soft)] text-[var(--rzp-warning)]' 
                      : 'bg-[var(--rzp-info-soft)] text-[var(--rzp-info)]'
                  }`}>
                    {rec.impact} Impact
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-[var(--rzp-text-secondary)] mb-4">
                  {rec.description}
                </p>
                <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-[var(--rzp-border)]">
                  <Button variant="outline" size="sm">Run What-If Simulation</Button>
                  <Button variant="ai" size="sm" className="ml-auto">
                    Review Change <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
