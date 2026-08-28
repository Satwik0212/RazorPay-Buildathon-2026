import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Bot, Play, Settings2, ShieldAlert } from 'lucide-react';
import { simulationApi } from '../../api/simulation';
import { authApi } from '../../api/auth';

export const SimulationDashboard = () => {
  const [simulating, setSimulating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const runSimulation = async () => {
    setSimulating(true);
    setError('');
    try {
      const meRes = await authApi.getMe();
      const realMerchantId = meRes.data.merchant_id;
      if (!realMerchantId) throw new Error("No merchant ID associated with session.");
      
      const res = await simulationApi.runSimulation({
        merchant_id: realMerchantId, 
        scenario_count: 5,
        buyer_profiles: ["BUDGET", "QUALITY"]
      });
      setResults(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Simulation failed to run.');
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)] flex items-center">
            <Bot className="h-6 w-6 mr-2 text-[var(--rzp-ai)]" /> Synthetic Buyer Simulation
          </h1>
          <p className="text-sm text-[var(--rzp-text-muted)]">Test your catalogue against synthetically generated AI buyer personas.</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline">
            <Settings2 className="h-4 w-4 mr-2" /> Configure Personas
          </Button>
          <Button onClick={runSimulation} isLoading={simulating} variant="ai">
            <Play className="h-4 w-4 mr-2" /> Run Simulation
          </Button>
        </div>
      </div>
      
      <div className="bg-[var(--rzp-warning-soft)] p-3 rounded-lg border border-[var(--rzp-warning)] flex items-start text-sm text-[var(--rzp-warning)]">
        <ShieldAlert className="h-5 w-5 mr-2 shrink-0" />
        <p>
          <strong>Simulated Data Notice:</strong> All results on this page are generated from synthetic simulations and do NOT reflect real production revenue or orders.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-sm font-medium">
          {error}
        </div>
      )}

      {!results && !simulating && (
        <Card className="border-dashed bg-gray-50/50">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 bg-[var(--rzp-ai-soft)] rounded-full flex items-center justify-center mb-4">
              <Bot className="h-8 w-8 text-[var(--rzp-ai)]" />
            </div>
            <h3 className="text-lg font-semibold text-[var(--rzp-text)]">Ready to Simulate</h3>
            <p className="text-sm text-[var(--rzp-text-muted)] max-w-md mt-2">
              Run a simulation to see how different AI personas evaluate your products based on price, delivery, and policies.
            </p>
            <Button onClick={runSimulation} className="mt-6" variant="ai">
              Start Simulation
            </Button>
          </CardContent>
        </Card>
      )}

      {simulating && (
        <Card className="border-[var(--rzp-ai)] shadow-[0_0_15px_rgba(124,58,237,0.1)]">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-4 border-[var(--rzp-ai-soft)] border-t-[var(--rzp-ai)] animate-spin"></div>
              <Bot className="h-6 w-6 text-[var(--rzp-ai)] absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[var(--rzp-text)] flex items-center justify-center">
                Analysing buyer constraints...
              </h3>
              <p className="text-sm text-[var(--rzp-text-muted)] mt-1">Evaluating simulated scenarios</p>
            </div>
          </CardContent>
        </Card>
      )}

      {results && !simulating && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-[var(--rzp-ai-soft)] border-[var(--rzp-ai)]">
              <CardContent className="p-6">
                <p className="text-sm font-medium text-[var(--rzp-ai)]">Simulated Matches</p>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">{results.summary_metrics.successful_matches}</p>
                  <span className="ml-2 text-sm font-medium text-[var(--rzp-success)]">out of {results.summary_metrics.buyers_simulated}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm font-medium text-[var(--rzp-text-muted)]">Satisfaction Rate</p>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">{results.summary_metrics.constraint_satisfaction_rate * 100}%</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm font-medium text-[var(--rzp-text-muted)]">Scenarios Checked</p>
                <div className="mt-2 flex items-baseline">
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">{results.scenario_count}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Synthetic Buyer Persona Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {results.results.map((res: any, idx: number) => (
                  <div key={idx} className="border-b pb-4 last:border-b-0 last:pb-0">
                    <div className="flex justify-between text-sm font-medium mb-1">
                      <span>Persona: {res.persona_name}</span>
                      <span className="text-[var(--rzp-success)]">Score: {res.score}</span>
                    </div>
                    <p className="text-sm text-[var(--rzp-text-secondary)]">{res.explanation}</p>
                    <div className="flex mt-2 gap-2">
                       {res.reason_codes.map((code: string) => (
                         <span key={code} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                           {code}
                         </span>
                       ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
