import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import {
  ShoppingBag, Search, ShoppingCart, ShieldCheck,
  CheckCircle, ArrowLeft, Loader2, AlertCircle, XCircle,
  Plus, Minus, Trash2
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { authApi } from '../../api/auth';
import { buyerApi } from '../../api/buyer';
import { cartsApi } from '../../api/carts';
import { quotesApi } from '../../api/quotes';
import { authorizationsApi } from '../../api/authorizations';
import { checkoutApi } from '../../api/checkout';
import { buyerApiClient } from '../../api/client';

import { campaignsApi } from '../../api/campaigns';
import { upsellApi } from '../../api/upsell';
import { ProductRecommendations } from '../../components/features/buyer/ProductRecommendations';
import type { Campaign, UpsellResponse, UpsellSuggestion } from '../../types';

import type { Quote, Cart, Product, Authorization, CheckoutOrder } from '../../types';
import axios from 'axios';

// Extend window for Razorpay
declare global {
  interface Window {
    Razorpay: any;
  }
}

const extractErrorMessage = (err: any, fallback: string): string => {
  return (
    err.response?.data?.error?.message ||
    (typeof err.response?.data?.detail === 'string' ? err.response?.data?.detail : null) ||
    err.response?.data?.message ||
    err.message ||
    fallback
  );
};

export const BuyerFlow = () => {
  const [step, setStep] = useState<'auth' | 'catalog' | 'product_detail' | 'cart' | 'checkout' | 'success'>('auth');

  // Data state
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [activeCart, setActiveCart] = useState<Cart | null>(null);
  const [activeQuote, setActiveQuote] = useState<Quote | null>(null);
  const [activeAuth, setActiveAuth] = useState<Authorization | null>(null);
  const [activeOrder, setActiveOrder] = useState<CheckoutOrder | null>(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAiSearch, setIsAiSearch] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authData, setAuthData] = useState({ name: '', email: '', password: '' });
  const [activeCampaigns, setActiveCampaigns] = useState<Campaign[]>([]);
  const [upsellData, setUpsellData] = useState<UpsellResponse | null>(null);
  const [upsellLoading, setUpsellLoading] = useState(false);
  const [upsellError, setUpsellError] = useState<string | null>(null);
  const [addingSuggestionId, setAddingSuggestionId] = useState<string | null>(null);
  const [addedSuggestionId, setAddedSuggestionId] = useState<string | null>(null);

  useEffect(() => {
    // Check if buyer is logged in
    const token = localStorage.getItem('buyer_token');
    if (token) {
      setStep('catalog');
      fetchProducts();
      fetchCampaigns();
    }
  }, []);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price / 100);
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      let res;
      if (authMode === 'login') {
        res = await axios.post(`${import.meta.env.VITE_API_URL || '/api/v1'}/auth/login`, {
          email: authData.email.trim(),
          password: authData.password,
        });
      } else {
        res = await axios.post(`${import.meta.env.VITE_API_URL || '/api/v1'}/auth/register`, {
          name: authData.name.trim() || 'Buyer',
          email: authData.email.trim(),
          password: authData.password,
          role: 'CUSTOMER',
        });
      }
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('buyer_token', res.data.access_token);
      if (res.data.user) {
        localStorage.setItem('user_profile', JSON.stringify(res.data.user));
      }
      setStep('catalog');
      fetchProducts();
      fetchCampaigns();
    } catch (err: any) {
      setError(extractErrorMessage(err, `Failed to ${authMode}`));
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaigns = async () => {
    try {
      const merchantId = localStorage.getItem('buyer_merchant_id');
      if (!merchantId) return; // No merchant context – skip
      const res = await campaignsApi.getActiveCampaigns(merchantId);
      setActiveCampaigns(res.data.filter(c => c.status === 'ACTIVE'));
    } catch (err) {
      console.error('Failed to load campaigns', err);
    }
  };

  const fetchProducts = async (query?: string) => {
    setLoading(true);
    try {
      const endpoint = query?.trim()
        ? `/catalog?search=${encodeURIComponent(query.trim())}`
        : '/catalog';
      const res = await buyerApiClient.get(endpoint);
      // Assume the paginated response has items
      setProducts(res.data.items || []);
    } catch (err: any) {
      console.error(err);
      setError(extractErrorMessage(err, 'Failed to load catalog.'));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchProducts();
      fetchCampaigns();
      return;
    }
    setLoading(true);
    setError('');
    try {
      if (isAiSearch) {
        const intentRes = await buyerApi.parseIntent(searchQuery);
        const searchRes = await buyerApi.searchCatalogue({
          category: intentRes.data.intent.category,
          max_budget: intentRes.data.intent.max_budget,
          requirements: intentRes.data.intent.requirements,
          preferences: intentRes.data.intent.preferences
        });
        setProducts(searchRes.data.results || []);
      } else {
        // Standard search - pass search param to backend endpoint enabling server-side full catalog search across all 2,980 products
        await fetchProducts(searchQuery.trim());
      }
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Search failed.'));
    } finally {
      setLoading(false);
    }
  };

  const viewProduct = async (product: Product) => {
    setSelectedProduct(product);
    setStep('product_detail');
    setUpsellData(null);
    setUpsellLoading(true);
    setUpsellError(null);
    try {
      const res = await upsellApi.getProductSuggestions(product.id);
      setUpsellData(res.data);
    } catch (err: any) {
      console.error('Failed to load upsell suggestions', err);
      setUpsellError(extractErrorMessage(err, 'Failed to load recommendations.'));
    } finally {
      setUpsellLoading(false);
    }
  };

  const handleAddSuggestionToCart = async (suggestion: UpsellSuggestion) => {
    if (!selectedProduct) return;
    setAddingSuggestionId(suggestion.product_id);
    setError('');
    try {
      let cartId = activeCart?.id;
      if (!cartId || activeCart?.merchant_id !== selectedProduct.merchant_id) {
        // Create cart for the product's merchant
        const cartRes = await cartsApi.createCart({ merchant_id: selectedProduct.merchant_id });
        cartId = cartRes.data.id;
        setActiveCart(cartRes.data);
      }

      const res = await cartsApi.createItem(cartId as string, {
        product_id: suggestion.product_id,
        quantity: 1
      });
      setActiveCart(res.data);
      setAddedSuggestionId(suggestion.product_id);
      setTimeout(() => {
        setAddedSuggestionId(null);
      }, 2500);
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('buyer_token');
        setStep('auth');
        setError('Your session has expired. Please sign in again.');
      } else {
        console.error('Failed to add suggestion to cart', err);
        setError(extractErrorMessage(err, 'Could not add recommended product to cart.'));
      }
    } finally {
      setAddingSuggestionId(null);
    }
  };

  const addToCart = async () => {
    if (!selectedProduct) return;
    if (selectedProduct.inventory && selectedProduct.inventory.available_quantity <= 0) {
      setError('This product is currently out of stock.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      let cartId = activeCart?.id;
      if (!cartId) {
        // Create cart for the product's merchant
        const cartRes = await cartsApi.createCart({ merchant_id: selectedProduct.merchant_id });
        cartId = cartRes.data.id;
        setActiveCart(cartRes.data);
      } else if (activeCart?.merchant_id !== selectedProduct.merchant_id) {
        // Simple handling: clear cart and create new if different merchant
        const cartRes = await cartsApi.createCart({ merchant_id: selectedProduct.merchant_id });
        cartId = cartRes.data.id;
        setActiveCart(cartRes.data);
      }

      const res = await cartsApi.createItem(cartId as string, { product_id: selectedProduct.id, quantity: 1 });
      setActiveCart(res.data);
      setStep('cart');
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('buyer_token');
        setStep('auth');
        setError('Your session has expired. Please sign in again.');
      } else {
        setError(extractErrorMessage(err, 'Failed to add to cart.'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId: string, newQuantity: number) => {
    if (!activeCart || newQuantity < 1) return;
    setLoading(true);
    setError('');
    try {
      const res = await cartsApi.updateItem(activeCart.id, itemId, { quantity: newQuantity });
      setActiveCart(res.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('buyer_token');
        setStep('auth');
        setError('Your session has expired. Please sign in again.');
      } else {
        setError(extractErrorMessage(err, 'Failed to update item quantity.'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    if (!activeCart) return;
    setLoading(true);
    setError('');
    try {
      const res = await cartsApi.removeItem(activeCart.id, itemId);
      setActiveCart(res.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('buyer_token');
        setStep('auth');
        setError('Your session has expired. Please sign in again.');
      } else {
        setError(extractErrorMessage(err, 'Failed to remove item.'));
      }
    } finally {
      setLoading(false);
    }
  };

  const proceedToCheckout = async () => {
    if (!activeCart) return;
    setLoading(true);
    setError('');
    try {
      const quoteRes = await quotesApi.createQuote(activeCart.id);
      setActiveQuote(quoteRes.data);

      const authRes = await authorizationsApi.createAuthorization(quoteRes.data.quote_id);
      setActiveAuth(authRes.data);

      if (authRes.data.status !== 'APPROVED') {
        throw new Error(`Merchant policy block: ${authRes.data.status}`);
      }

      const orderRes = await checkoutApi.createOrder({
        quote_id: quoteRes.data.quote_id,
        authorization_id: authRes.data.authorization_id
      });
      setActiveOrder(orderRes.data);

      setStep('checkout');
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('buyer_token');
        setStep('auth');
        setError('Your session has expired. Please sign in again.');
      } else {
        setError(extractErrorMessage(err, 'Checkout initialization failed.'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRazorpayPayment = () => {
    if (!activeOrder) return;

    // In case the Razorpay mock script is injected or actual script is used
    if (!window.Razorpay) {
      setError('Razorpay SDK not loaded. Please ensure you have internet connection.');
      return;
    }

    const options = {
      key: (activeOrder as any).razorpay_key_id, // Ensure we pass the key from backend
      amount: activeOrder.amount,
      currency: activeOrder.currency,
      name: "GraahakLens Store",
      description: "Test Transaction",
      order_id: activeOrder.razorpay_order_id,
      handler: async function (response: any) {
        // P0-3 FIX: Verify payment on the server before showing success.
        // The backend validates HMAC signature, transitions order to PAID,
        // creates a Payment record, marks the cart COMPLETED, and decrements inventory.
        setLoading(true);
        setError('');
        try {
          const token = localStorage.getItem('buyer_token');
          const verifyRes = await axios.post(
            `${import.meta.env.VITE_API_URL || '/api/v1'}/payments/verify`,
            {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          if (verifyRes.data.success) {
            setStep('success');
          } else {
            setError('Payment verification failed. Please contact support.');
          }
        } catch (err: any) {
          setError(extractErrorMessage(err, 'Payment verification failed. Please try again.'));
        } finally {
          setLoading(false);
        }
      },
      prefill: {
        name: "Test Buyer",
        email: "buyer@demo.com",
      },
      theme: {
        color: "#6822CC"
      }
    };

    const rzp = new window.Razorpay(options);
    rzp.on('payment.failed', function (response: any){
      setError(`Payment failed: ${response.error.description}`);
    });
    rzp.open();
  };

  const renderHeader = (title: string, showBack?: boolean, backAction?: () => void) => (
    <div className="flex items-center mb-6">
      {showBack && (
        <Button variant="ghost" onClick={backAction} className="mr-2 p-2">
          <ArrowLeft className="h-5 w-5" />
        </Button>
      )}
      <h1 className="text-2xl font-bold text-[var(--rzp-text)]">{title}</h1>

      {step !== 'auth' && (
        <div className="ml-auto">
          <Button variant="outline" onClick={() => setStep('cart')} className="relative">
            <ShoppingCart className="h-5 w-5 mr-2" />
            Cart
            {activeCart?.items?.length ? (
              <span className="absolute -top-2 -right-2 bg-[var(--rzp-primary)] text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {activeCart.items.reduce((acc, item) => acc + item.quantity, 0)}
              </span>
            ) : null}
          </Button>
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {error && (
        <div className="mb-6 p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-md border border-[var(--rzp-danger)] flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 mt-0.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* AUTH STEP */}
      {step === 'auth' && (
        <Card className="max-w-md mx-auto mt-12 shadow-lg">
          <CardHeader className="text-center">
            <ShoppingBag className="h-12 w-12 mx-auto text-[var(--rzp-primary)] mb-4" />
            <CardTitle className="text-2xl">GraahakLens Buyer Portal</CardTitle>
            <p className="text-sm text-gray-500 mt-2">
              {authMode === 'login' ? 'Sign in to access the store.' : 'Create an account to start shopping.'}
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAuth} className="space-y-4">
              {authMode === 'register' && (
                <div className="space-y-2">
                  <label htmlFor="buyer-name">Full Name</label>
                  <Input
                    id="buyer-name"
                    type="text"
                    required
                    value={authData.name}
                    onChange={e => setAuthData({...authData, name: e.target.value})}
                    placeholder="e.g. Priya Sharma"
                  />
                </div>
              )}
              <div className="space-y-2">
                <label htmlFor="email">Email</label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={authData.email}
                  onChange={e => setAuthData({...authData, email: e.target.value})}
                  placeholder="buyer@example.com"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="password">Password</label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={authData.password}
                  onChange={e => setAuthData({...authData, password: e.target.value})}
                  placeholder="••••••••"
                />
              </div>
              <Button type="submit" className="w-full" isLoading={loading}>
                {authMode === 'login' ? 'Sign In' : 'Register'}
              </Button>
            </form>
          </CardContent>
          <CardFooter className="justify-center">
            <Button variant="ghost" className="text-[var(--rzp-primary)]" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
              {authMode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* CATALOG STEP */}
      {step === 'catalog' && (
        <div>
          {renderHeader('Discover Products')}
          {activeCampaigns.length > 0 && (
            <div className="mb-8 space-y-4">
              {activeCampaigns.map(camp => (
                <div key={camp.id} className="bg-gradient-to-r from-[var(--rzp-primary-soft)] to-blue-50 border border-[var(--rzp-primary)] rounded-lg p-6 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="bg-blue-100 text-[var(--rzp-primary)] text-xs font-bold px-2 py-1 rounded uppercase tracking-wider mb-2 inline-block">
                      Special Offer
                    </span>
                    <h3 className="text-xl font-bold text-gray-900">{camp.name}</h3>
                    <p className="text-gray-700 mt-1">{camp.message_content}</p>
                  </div>
                  {camp.target_product_id && (
                    <Button onClick={() => {
                      const p = products.find(x => x.id === camp.target_product_id);
                      if (p) viewProduct(p);
                    }}>
                      View Offer
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}


          <div className="flex flex-col md:flex-row gap-4 mb-8">
            <div className="flex-1 relative">
              <Input
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder={isAiSearch ? "e.g. I want a cheap gaming laptop under 50k" : "Search products..."}
                className="pl-10 h-12"
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            </div>
            <div className="flex items-center gap-2">
              <label className="whitespace-nowrap flex items-center cursor-pointer text-sm">
                <input
                  type="checkbox"
                  className="mr-2 rounded text-[var(--rzp-primary)] focus:ring-[var(--rzp-primary)]"
                  checked={isAiSearch}
                  onChange={e => setIsAiSearch(e.target.checked)}
                />
                Use AI Assistant
              </label>
              <Button onClick={handleSearch} isLoading={loading} className="h-12 px-6">
                Search
              </Button>
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="h-10 w-10 animate-spin text-[var(--rzp-primary)]" />
            </div>
          ) : products.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {products.map(product => (
                <Card key={product.id} className="cursor-pointer hover:shadow-md transition-shadow h-full flex flex-col" onClick={() => viewProduct(product)}>
                  <div className="bg-gray-100 h-48 w-full flex items-center justify-center rounded-t-lg overflow-hidden">
                    <ShoppingBag className="h-16 w-16 text-gray-300" />
                  </div>
                  <CardContent className="pt-4 flex-grow">
                    <div className="text-xs font-semibold text-[var(--rzp-primary)] uppercase tracking-wider mb-1">
                      {product.category}
                    </div>
                    <h3 className="font-bold text-lg mb-2 line-clamp-2">{product.name}</h3>
                    <p className="text-xl font-bold text-[var(--rzp-text)] mt-auto">
                      {formatPrice(product.price)}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-20 bg-gray-50 rounded-lg border border-dashed border-gray-300">
              <ShoppingBag className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No products found</h3>
              <p className="text-gray-500 mt-1">Try adjusting your search query.</p>
              <Button variant="outline" className="mt-4" onClick={() => { setSearchQuery(''); fetchProducts();
      fetchCampaigns(); }}>
                Clear Search
              </Button>
            </div>
          )}
        </div>
      )}

      {/* PRODUCT DETAIL STEP */}
      {step === 'product_detail' && selectedProduct && (
        <div>
          {renderHeader('Product Details', true, () => setStep('catalog'))}
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-gray-100 rounded-lg h-96 flex items-center justify-center">
              <ShoppingBag className="h-32 w-32 text-gray-300" />
            </div>
            <div className="flex flex-col">
              <div className="text-sm font-semibold text-[var(--rzp-primary)] uppercase tracking-wider mb-2">
                {selectedProduct.category}
              </div>
              <h1 className="text-3xl font-bold text-[var(--rzp-text)] mb-4">{selectedProduct.name}</h1>
              <p className="text-gray-600 mb-6 flex-grow">{selectedProduct.description || 'No description available for this product.'}</p>

              {selectedProduct.metadata && Object.keys(selectedProduct.metadata).length > 0 && (
                <div className="bg-gray-50 p-4 rounded-md mb-6 border">
                  <h4 className="font-medium mb-2 text-sm text-gray-500">Specifications</h4>
                  <ul className="text-sm space-y-1">
                    {Object.entries(selectedProduct.metadata).map(([key, value]) => (
                      <li key={key} className="flex">
                        <span className="w-1/3 text-gray-500 capitalize">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-medium text-[var(--rzp-text)]">{String(value)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex items-center justify-between mt-auto pt-6 border-t border-gray-200">
                <div>
                  <p className="text-3xl font-bold text-[var(--rzp-text)]">{formatPrice(selectedProduct.price)}</p>
                  {selectedProduct.inventory && selectedProduct.inventory.available_quantity <= 0 ? (
                    <p className="text-sm text-[var(--rzp-danger)] font-medium mt-1 flex items-center">
                      <XCircle className="h-4 w-4 mr-1" /> Out of stock
                    </p>
                  ) : (
                    <p className="text-sm text-[var(--rzp-success)] font-medium mt-1 flex items-center">
                      <CheckCircle className="h-4 w-4 mr-1" />
                      {selectedProduct.inventory?.available_quantity !== undefined
                        ? `${selectedProduct.inventory.available_quantity} in stock`
                        : 'In stock'}
                    </p>
                  )}
                </div>
                <Button
                  onClick={addToCart}
                  isLoading={loading}
                  disabled={Boolean(selectedProduct.inventory && selectedProduct.inventory.available_quantity <= 0)}
                  size="lg"
                  className="px-8"
                >
                  {selectedProduct.inventory && selectedProduct.inventory.available_quantity <= 0 ? 'Out of Stock' : 'Add to Cart'}
                </Button>
              </div>
            </div>
          </div>

          {/* AI-Powered Upsell / Cross-sell Recommendations */}
          <ProductRecommendations
            upsellData={upsellData}
            isLoading={upsellLoading}
            error={upsellError}
            currentProduct={selectedProduct}
            catalogProducts={products}
            onViewProduct={viewProduct}
            onAddToCart={handleAddSuggestionToCart}
            addingSuggestionId={addingSuggestionId}
            addedSuggestionId={addedSuggestionId}
            formatPrice={formatPrice}
          />
        </div>
      )}

      {/* CART STEP */}
      {step === 'cart' && (
        <div>
          {renderHeader('Your Cart', true, () => setStep('catalog'))}

          {!activeCart || !activeCart.items || activeCart.items.length === 0 ? (
            <div className="text-center py-20 bg-gray-50 rounded-lg border border-dashed border-gray-300">
              <ShoppingCart className="h-16 w-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-xl font-medium text-gray-900">Your cart is empty</h3>
              <Button className="mt-6" onClick={() => setStep('catalog')}>
                Continue Shopping
              </Button>
            </div>
          ) : (
            <div className="grid lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-4">
                {activeCart.items.map((item) => (
                  <Card key={item.id}>
                    <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-center space-x-4 flex-grow">
                        <div className="bg-gray-100 h-20 w-20 rounded flex items-center justify-center shrink-0">
                          <ShoppingBag className="h-8 w-8 text-gray-400" />
                        </div>
                        <div>
                          <h4 className="font-bold text-gray-900">{item.product?.name || `Product ID: ${item.product_id}`}</h4>
                          <p className="text-sm text-gray-500">
                            {item.product ? `${formatPrice(item.product.price)} each` : ''}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between sm:justify-end space-x-4">
                        <div className="flex items-center border rounded-md">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                            disabled={loading || item.quantity <= 1}
                            title="Decrease quantity"
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                          <span className="w-8 text-center text-sm font-semibold">{item.quantity}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                            disabled={loading}
                            title="Increase quantity"
                          >
                            <Plus className="h-3 w-3" />
                          </Button>
                        </div>

                        <div className="text-right min-w-[80px]">
                          <p className="font-bold text-[var(--rzp-text)]">
                            {item.product ? formatPrice(item.product.price * item.quantity) : 'Price unknown'}
                          </p>
                        </div>

                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleRemoveItem(item.id)}
                          disabled={loading}
                          title="Remove item"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div>
                <Card className="sticky top-6">
                  <CardHeader>
                    <CardTitle>Order Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between font-medium text-gray-700">
                      <span>Estimated Subtotal</span>
                      <span>
                        {formatPrice(
                          activeCart.items.reduce((acc, item) => acc + (item.product?.price || 0) * item.quantity, 0)
                        )}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 flex items-start bg-blue-50 p-3 rounded text-blue-800">
                      <ShieldCheck className="h-5 w-5 mr-2 shrink-0" />
                      The definitive total will be calculated by the server during checkout to apply taxes, shipping, and discounts securely.
                    </p>
                  </CardContent>
                  <CardFooter>
                    <Button onClick={proceedToCheckout} isLoading={loading} className="w-full h-12 text-lg">
                      Proceed to Checkout
                    </Button>
                  </CardFooter>
                </Card>
              </div>
            </div>
          )}
        </div>
      )}

      {/* CHECKOUT STEP */}
      {step === 'checkout' && activeOrder && activeQuote && (
        <div className="max-w-2xl mx-auto">
          {renderHeader('Checkout', true, () => setStep('cart'))}

          <Card className="mb-6 border-[var(--rzp-primary)] shadow-md">
            <CardHeader className="bg-[var(--rzp-primary-soft)] border-b border-[var(--rzp-primary)]">
              <CardTitle className="text-[var(--rzp-primary)] flex items-center">
                <ShieldCheck className="h-5 w-5 mr-2" /> Server-Verified Quote
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-3 text-[var(--rzp-text)]">
                <div className="flex justify-between">
                  <span className="text-[var(--rzp-text-secondary)]">Subtotal</span>
                  <span>{formatPrice(activeQuote.subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--rzp-text-secondary)]">Shipping</span>
                  <span>{formatPrice(activeQuote.shipping)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--rzp-text-secondary)]">Tax</span>
                  <span>{formatPrice(activeQuote.tax)}</span>
                </div>
                <div className="pt-3 mt-3 border-t border-dashed border-gray-300 flex justify-between font-bold text-xl">
                  <span>Total Due</span>
                  <span>{formatPrice(activeQuote.subtotal + activeQuote.shipping + activeQuote.tax)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Payment Details</CardTitle>
              <p className="text-sm text-gray-500 mt-2">Complete your purchase securely via Razorpay</p>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-gray-50 border rounded-md mb-6 flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 font-medium">Order ID</p>
                  <p className="font-mono text-sm">{activeOrder.razorpay_order_id}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500 font-medium">Amount</p>
                  <p className="font-bold">{formatPrice(activeOrder.amount)}</p>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleRazorpayPayment} isLoading={loading} className="w-full h-14 text-lg bg-[#3399cc] hover:bg-[#2b82ad] text-white">
                Pay with Razorpay
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* SUCCESS STEP */}
      {step === 'success' && (
        <Card className="max-w-md mx-auto mt-12 shadow-lg border-[var(--rzp-success)] overflow-hidden">
          <div className="bg-[var(--rzp-success)] h-2 w-full"></div>
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-20 w-20 text-[var(--rzp-success)] mx-auto mb-6" />
            <h2 className="text-3xl font-bold text-[var(--rzp-text)] mb-2">Order Confirmed!</h2>
            <p className="text-[var(--rzp-text-secondary)] mb-6">
              Thank you for your purchase. Your payment was successful and your order is being processed.
            </p>
            {activeOrder && (
              <div className="bg-gray-50 p-4 rounded-md text-left mb-8 border border-gray-100">
                <p className="text-sm text-gray-500 mb-1">Order Reference:</p>
                <p className="font-mono text-sm font-medium">{activeOrder.razorpay_order_id}</p>
              </div>
            )}
            <Button className="w-full" onClick={() => {
              setStep('catalog');
              setActiveCart(null);
              setActiveQuote(null);
              setActiveAuth(null);
              setActiveOrder(null);
            }}>
              Continue Shopping
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
