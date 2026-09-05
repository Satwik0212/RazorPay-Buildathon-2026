import React, { useState } from 'react';
import { 
  Sparkles, 
  TrendingUp, 
  Plus, 
  ShoppingBag, 
  Layers, 
  Check, 
  Loader2, 
  AlertCircle
} from 'lucide-react';
import { Card, CardContent } from '../../ui/Card';
import { Button } from '../../ui/Button';
import type { UpsellResponse, UpsellSuggestion, Product } from '../../../types';

interface ProductRecommendationsProps {
  upsellData: UpsellResponse | null;
  isLoading: boolean;
  error: string | null;
  currentProduct: Product;
  catalogProducts: Product[];
  onViewProduct: (product: Product) => void;
  onAddToCart: (suggestion: UpsellSuggestion) => Promise<void>;
  addingSuggestionId: string | null;
  addedSuggestionId: string | null;
  formatPrice: (price: number) => string;
}

export const ProductRecommendations: React.FC<ProductRecommendationsProps> = ({
  upsellData,
  isLoading,
  error,
  currentProduct,
  catalogProducts,
  onViewProduct,
  onAddToCart,
  addingSuggestionId,
  addedSuggestionId,
  formatPrice,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'upsell' | 'cross_sell'>('all');

  // Loading Skeleton State
  if (isLoading) {
    return (
      <div className="mt-12 border-t border-[var(--rzp-border)] pt-10">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-6 h-6 rounded-full bg-[var(--rzp-primary-soft)] flex items-center justify-center text-[var(--rzp-primary)] animate-pulse">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-[var(--rzp-text)]">
              AI Shopping Assistant
            </h3>
            <p className="text-xs text-[var(--rzp-text-muted)]">
              Analyzing catalogue for grounded upgrades and complementary add-ons...
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse border-gray-200">
              <CardContent className="p-5 space-y-4">
                <div className="bg-gray-100 h-36 rounded-lg w-full" />
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-5 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-100 rounded w-full" />
                <div className="h-10 bg-gray-200 rounded-lg w-full pt-2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Graceful Error State (never blocks the main page)
  if (error) {
    return (
      <div className="mt-12 border-t border-[var(--rzp-border)] pt-8">
        <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800">
            <span className="font-semibold block mb-0.5">Recommendations temporarily unavailable</span>
            Grounded catalogue suggestions could not be loaded at this time. Your current product selection and checkout remain fully functional.
          </div>
        </div>
      </div>
    );
  }

  // Safe checks for data availability
  const upsells = Array.isArray(upsellData?.upsell) ? upsellData!.upsell : [];
  const crossSells = Array.isArray(upsellData?.cross_sell) ? upsellData!.cross_sell : [];
  const hasSuggestions = upsells.length > 0 || crossSells.length > 0;

  // Empty State
  if (!hasSuggestions) {
    return null; // Keep product detail view clean when no recommendations are found
  }

  const displayedUpsells = activeTab === 'all' || activeTab === 'upsell' ? upsells : [];
  const displayedCrossSells = activeTab === 'all' || activeTab === 'cross_sell' ? crossSells : [];

  const handleCardClick = (suggestion: UpsellSuggestion) => {
    // Find matching full product from catalogue if loaded, otherwise construct minimal Product
    const found = catalogProducts.find((p) => p.id === suggestion.product_id);
    if (found) {
      onViewProduct(found);
    } else {
      onViewProduct({
        id: suggestion.product_id,
        merchant_id: currentProduct.merchant_id,
        name: suggestion.name,
        price: suggestion.price,
        category: suggestion.category,
        currency: currentProduct.currency || 'INR',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
  };

  return (
    <div className="mt-12 border-t border-[var(--rzp-border)] pt-10 space-y-8">
      {/* Header & Badges */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 bg-gradient-to-tr from-purple-100 to-blue-100 text-[var(--rzp-primary)] rounded-md">
              <Sparkles className="h-4 w-4" />
            </span>
            <h3 className="text-xl font-bold text-[var(--rzp-text)]">
              GraahakLens Shopping Assistant
            </h3>
          </div>
          <p className="text-sm text-[var(--rzp-text-muted)]">
            Tailored suggestions discovered from active merchant catalogue and real-time inventory.
          </p>
        </div>

        {/* Intelligence Meta Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {upsellData?.ai_powered && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 shadow-2xs">
              <Sparkles className="w-3 h-3 text-purple-600" />
              AI-Grounded Reasoning
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
            <Layers className="w-3 h-3 text-blue-600" />
            Deterministic Catalogue Match
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-[var(--rzp-border)] pb-2 text-sm">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
            activeTab === 'all'
              ? 'bg-gray-900 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          All Suggestions ({upsells.length + crossSells.length})
        </button>
        {upsells.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab('upsell')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'upsell'
                ? 'bg-purple-600 text-white'
                : 'text-purple-700 hover:bg-purple-50'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            Upgrades ({upsells.length})
          </button>
        )}
        {crossSells.length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab('cross_sell')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'cross_sell'
                ? 'bg-emerald-600 text-white'
                : 'text-emerald-700 hover:bg-emerald-50'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            Add-ons ({crossSells.length})
          </button>
        )}
      </div>

      {/* Section 1: UPSELL / UPGRADES */}
      {displayedUpsells.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-600" />
              <h4 className="text-lg font-bold text-gray-900">
                Better fit for higher performance needs
              </h4>
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-purple-700 bg-purple-50 border border-purple-200 px-2.5 py-0.5 rounded-full">
              Premium Alternatives
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedUpsells.map((item) => {
              const matched = catalogProducts.find((p) => p.id === item.product_id);
              const imageUrl = matched?.metadata?.image_urls?.[0];
              const priceDiff = item.price - currentProduct.price;
              const isAdding = addingSuggestionId === item.product_id;
              const isAdded = addedSuggestionId === item.product_id;

              return (
                <Card
                  key={item.product_id}
                  className="flex flex-col justify-between border-purple-100 hover:border-purple-300 hover:shadow-md transition-all group bg-white"
                >
                  <CardContent className="p-5 flex flex-col h-full">
                    {/* Visual Media / Placeholder */}
                    <div 
                      onClick={() => handleCardClick(item)}
                      className="bg-purple-50/50 rounded-lg h-36 flex items-center justify-center mb-4 overflow-hidden relative cursor-pointer group-hover:opacity-95 transition-opacity"
                    >
                      {imageUrl ? (
                        <img 
                          src={imageUrl} 
                          alt={item.name} 
                          className="h-full w-full object-contain p-2"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <ShoppingBag className="h-10 w-10 text-purple-300" />
                      )}
                      
                      <div className="absolute top-2 left-2 bg-purple-600 text-white text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md shadow-2xs">
                        Upgrade
                      </div>

                      {item.score !== undefined && (
                        <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-xs text-gray-700 border border-gray-200 text-[10px] font-semibold px-2 py-0.5 rounded-md">
                          Match: {Math.round(item.score * 100)}%
                        </div>
                      )}
                    </div>

                    {/* Metadata & Title */}
                    <div className="text-[11px] font-semibold text-purple-700 uppercase tracking-wider mb-1">
                      {item.category}
                    </div>
                    <h5 
                      onClick={() => handleCardClick(item)}
                      className="font-bold text-gray-900 line-clamp-2 mb-2 group-hover:text-purple-700 transition-colors cursor-pointer text-sm"
                      title={item.name}
                    >
                      {item.name}
                    </h5>

                    {/* Price & Difference */}
                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="text-lg font-bold text-[var(--rzp-text)]">
                        {formatPrice(item.price)}
                      </span>
                      {priceDiff > 0 && (
                        <span className="text-xs font-medium text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded">
                          +{formatPrice(priceDiff)} vs current
                        </span>
                      )}
                    </div>

                    {/* Grounded AI/Catalogue Reason */}
                    <div className="bg-purple-50/80 border border-purple-100 rounded-lg p-3 text-xs text-gray-700 mb-4 flex-grow">
                      <div className="flex items-center gap-1 font-semibold text-purple-900 mb-1">
                        <Sparkles className="w-3 h-3 text-purple-600" />
                        <span>Why this was suggested:</span>
                      </div>
                      <p className="italic leading-relaxed text-gray-600">
                        {item.explanation ||
                          `Superior tier in ${item.category} evaluated against your criteria for enhanced durability and specifications.`}
                      </p>
                      {item.ai_confidence !== undefined && item.ai_confidence !== null && (
                        <div className="mt-2 pt-1.5 border-t border-purple-200/60 text-[10px] text-purple-800 font-medium flex items-center justify-between">
                          <span>AI Confidence Score</span>
                          <span>{Math.round(item.ai_confidence * 100)}%</span>
                        </div>
                      )}
                    </div>

                    {/* Buyer Actions (Authoritative Cart Integration) */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 mt-auto">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCardClick(item)}
                        className="text-xs border-purple-200 hover:border-purple-300 hover:bg-purple-50 text-purple-900"
                      >
                        View Details
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => onAddToCart(item)}
                        disabled={isAdding}
                        className={`text-xs ${
                          isAdded
                            ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                            : 'bg-purple-600 hover:bg-purple-700 text-white'
                        }`}
                      >
                        {isAdding ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                            Adding...
                          </>
                        ) : isAdded ? (
                          <>
                            <Check className="w-3 h-3 mr-1" />
                            Added!
                          </>
                        ) : (
                          <>
                            <Plus className="w-3 h-3 mr-1" />
                            Add to Cart
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Section 2: CROSS-SELL / COMPLEMENTARY ACCESSORIES */}
      {displayedCrossSells.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-600" />
              <h4 className="text-lg font-bold text-gray-900">
                Pairs well with your current selection
              </h4>
            </div>
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
              Frequently Paired Add-on
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedCrossSells.map((item) => {
              const matched = catalogProducts.find((p) => p.id === item.product_id);
              const imageUrl = matched?.metadata?.image_urls?.[0];
              const isAdding = addingSuggestionId === item.product_id;
              const isAdded = addedSuggestionId === item.product_id;

              return (
                <Card
                  key={item.product_id}
                  className="flex flex-col justify-between border-emerald-100 hover:border-emerald-300 hover:shadow-md transition-all group bg-white"
                >
                  <CardContent className="p-5 flex flex-col h-full">
                    {/* Visual Media / Placeholder */}
                    <div 
                      onClick={() => handleCardClick(item)}
                      className="bg-emerald-50/50 rounded-lg h-36 flex items-center justify-center mb-4 overflow-hidden relative cursor-pointer group-hover:opacity-95 transition-opacity"
                    >
                      {imageUrl ? (
                        <img 
                          src={imageUrl} 
                          alt={item.name} 
                          className="h-full w-full object-contain p-2"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <ShoppingBag className="h-10 w-10 text-emerald-300" />
                      )}

                      <div className="absolute top-2 left-2 bg-emerald-600 text-white text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md shadow-2xs">
                        Add-on
                      </div>

                      {item.score !== undefined && (
                        <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-xs text-gray-700 border border-gray-200 text-[10px] font-semibold px-2 py-0.5 rounded-md">
                          Relevance: {Math.round(item.score * 100)}%
                        </div>
                      )}
                    </div>

                    {/* Metadata & Title */}
                    <div className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider mb-1">
                      {item.category}
                    </div>
                    <h5 
                      onClick={() => handleCardClick(item)}
                      className="font-bold text-gray-900 line-clamp-2 mb-2 group-hover:text-emerald-700 transition-colors cursor-pointer text-sm"
                      title={item.name}
                    >
                      {item.name}
                    </h5>

                    {/* Price */}
                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="text-lg font-bold text-[var(--rzp-text)]">
                        {formatPrice(item.price)}
                      </span>
                      <span className="text-xs text-gray-500 font-medium">
                        Complete your setup
                      </span>
                    </div>

                    {/* Grounded Reason Callout */}
                    <div className="bg-emerald-50/80 border border-emerald-100 rounded-lg p-3 text-xs text-gray-700 mb-4 flex-grow">
                      <div className="flex items-center gap-1 font-semibold text-emerald-900 mb-1">
                        <Sparkles className="w-3 h-3 text-emerald-600" />
                        <span>Why this was suggested:</span>
                      </div>
                      <p className="italic leading-relaxed text-gray-600">
                        {item.explanation ||
                          `Complementary accessory in ${item.category} frequently paired with ${currentProduct.name} to maximize utility.`}
                      </p>
                      {item.ai_confidence !== undefined && item.ai_confidence !== null && (
                        <div className="mt-2 pt-1.5 border-t border-emerald-200/60 text-[10px] text-emerald-800 font-medium flex items-center justify-between">
                          <span>AI Compatibility Score</span>
                          <span>{Math.round(item.ai_confidence * 100)}%</span>
                        </div>
                      )}
                    </div>

                    {/* Buyer Actions */}
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 mt-auto">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCardClick(item)}
                        className="text-xs border-emerald-200 hover:border-emerald-300 hover:bg-emerald-50 text-emerald-900"
                      >
                        View Details
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => onAddToCart(item)}
                        disabled={isAdding}
                        className={`text-xs ${
                          isAdded
                            ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                            : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                        }`}
                      >
                        {isAdding ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                            Adding...
                          </>
                        ) : isAdded ? (
                          <>
                            <Check className="w-3 h-3 mr-1" />
                            Added!
                          </>
                        ) : (
                          <>
                            <Plus className="w-3 h-3 mr-1" />
                            Add to Cart
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
