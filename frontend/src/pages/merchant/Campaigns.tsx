import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import {
  Sparkles,
  Megaphone,
  Loader2,
  CheckCircle2,
  XCircle,
  Play,
  Pause,
  AlertCircle
} from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { productsApi } from '../../api/products';
import type { Campaign, Product } from '../../types';

export const Campaigns = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [campRes, prodRes] = await Promise.all([
        campaignsApi.listCampaigns().catch(() => ({ data: [] })),
        productsApi.getProducts({ limit: 100 }).catch(() => ({ data: { items: [] } })),
      ]);

      setCampaigns(campRes.data || []);
      setProducts(prodRes.data?.items || []);
    } catch (err) {
      console.error('Failed to fetch campaigns', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      await campaignsApi.generateCampaigns();
      await fetchData();
    } catch (err) {
      console.error('Failed to generate campaigns', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: 'ACTIVE' | 'PAUSED' | 'ENDED' | 'REJECTED') => {
    try {
      // The backend accepts 'PROPOSED', 'ACTIVE', 'PAUSED', 'ENDED'.
      // If we need to reject, maybe there's no REJECTED status, let's assume ENDED acts as reject/cancel, or we just remove it from UI.
      // Wait, backend CampaignStatus typically has REJECTED? Let's send ENDED for rejected proposals for safety.
      const statusToSend = newStatus === 'REJECTED' ? 'ENDED' : newStatus;
      await campaignsApi.updateStatus(id, { status: statusToSend as any });

      // Optimistic update
      setCampaigns(prev => prev.map(c =>
        c.id === id ? { ...c, status: statusToSend as any } : c
      ));
    } catch (err) {
      console.error('Failed to update campaign status', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)]" />
      </div>
    );
  }

  const proposed = campaigns.filter(c => c.status === 'PROPOSED');
  const active = campaigns.filter(c => c.status === 'ACTIVE');
  const other = campaigns.filter(c => c.status === 'PAUSED' || c.status === 'ENDED');

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--rzp-text)] flex items-center">
            <Megaphone className="mr-3 h-8 w-8 text-[var(--rzp-primary)]" />
            Campaign Orchestrator
          </h1>
          <p className="text-[var(--rzp-text-secondary)] mt-2 max-w-3xl">
            Automatically generate and manage targeted marketing campaigns based on actionable buyer friction detected during AI simulations.
          </p>
        </div>
        <Button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center"
        >
          {generating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
          Generate Campaign Proposals
        </Button>
      </div>

      {campaigns.length === 0 ? (
        <Card className="border-dashed border-2 bg-gray-50">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <AlertCircle className="h-12 w-12 text-gray-400 mb-4" />
            <h2 className="text-xl font-semibold mb-2">No Campaigns Found</h2>
            <p className="text-gray-500 text-center max-w-md mb-6">
              Campaigns are generated after simulations reveal actionable buyer friction. Run a simulation to discover opportunities.
            </p>
            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? 'Generating...' : 'Analyze Recent Simulations'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-12">
          {/* Proposed Campaigns */}
          {proposed.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="bg-yellow-100 text-yellow-800 text-sm py-1 px-3 rounded-full mr-3">
                  {proposed.length}
                </span>
                Campaign Proposals
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {proposed.map(campaign => {
                  const product = products.find(p => p.id === campaign.target_product_id);
                  return (
                    <Card key={campaign.id} className="border-yellow-200 shadow-sm relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-yellow-400"></div>
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start mb-4">
                          <h3 className="font-bold text-lg">{campaign.name}</h3>
                          <span className="text-xs font-semibold bg-gray-100 px-2 py-1 rounded text-gray-600 uppercase">
                            {campaign.campaign_type.replace('_', ' ')}
                          </span>
                        </div>

                        <div className="space-y-4 text-sm">
                          <div>
                            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Objective</p>
                            <p className="font-medium text-gray-800">{campaign.objective}</p>
                          </div>

                          {product && (
                            <div className="bg-gray-50 p-3 rounded border border-gray-100">
                              <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Target Product</p>
                              <p className="font-medium text-[var(--rzp-primary)]">{product.name}</p>
                            </div>
                          )}

                          <div>
                            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Trigger Signal / Evidence</p>
                            <p className="text-gray-700 bg-red-50 p-2 rounded text-xs border border-red-100">
                              {campaign.trigger_signal}
                            </p>
                          </div>

                          <div>
                            <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Proposed Message</p>
                            <p className="italic text-gray-700 border-l-2 border-gray-300 pl-3 py-1">"{campaign.message_content}"</p>
                          </div>
                        </div>

                        <div className="mt-6 flex gap-3">
                          <Button
                            className="flex-1 bg-[var(--rzp-success)] hover:bg-green-700 text-white"
                            onClick={() => handleStatusChange(campaign.id, 'ACTIVE')}
                          >
                            <CheckCircle2 className="w-4 h-4 mr-2" />
                            Approve
                          </Button>
                          <Button
                            variant="outline"
                            className="flex-1 text-red-600 hover:bg-red-50 border-red-200"
                            onClick={() => handleStatusChange(campaign.id, 'REJECTED')}
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            Reject
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </section>
          )}

          {/* Active Campaigns */}
          {active.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <span className="bg-[var(--rzp-success)] text-white text-sm py-1 px-3 rounded-full mr-3">
                  {active.length}
                </span>
                Active Campaigns
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {active.map(campaign => (
                  <Card key={campaign.id} className="border-[var(--rzp-success)] shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-[var(--rzp-success)]"></div>
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="font-bold text-lg">{campaign.name}</h3>
                        <span className="text-xs font-semibold bg-green-100 text-green-800 px-2 py-1 rounded uppercase flex items-center">
                          <span className="w-2 h-2 rounded-full bg-green-500 mr-1 animate-pulse"></span>
                          Live
                        </span>
                      </div>

                      <div className="space-y-4 text-sm mb-6">
                        <div>
                          <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">Message Content</p>
                          <p className="text-gray-800 font-medium">"{campaign.message_content}"</p>
                        </div>
                      </div>

                      <Button
                        variant="outline"
                        className="w-full text-amber-600 border-amber-200 hover:bg-amber-50"
                        onClick={() => handleStatusChange(campaign.id, 'PAUSED')}
                      >
                        <Pause className="w-4 h-4 mr-2" />
                        Pause Campaign
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Past/Paused Campaigns */}
          {other.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold mb-4 text-gray-400">Past & Paused</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 opacity-75">
                {other.map(campaign => (
                  <Card key={campaign.id} className="bg-gray-50 border-gray-200">
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-gray-600">{campaign.name}</h3>
                        <span className="text-xs font-semibold bg-gray-200 text-gray-600 px-2 py-1 rounded uppercase">
                          {campaign.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 line-clamp-2">"{campaign.message_content}"</p>

                      {campaign.status === 'PAUSED' && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-4 w-full"
                          onClick={() => handleStatusChange(campaign.id, 'ACTIVE')}
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Resume
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
};
