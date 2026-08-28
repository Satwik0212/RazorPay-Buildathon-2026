import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Bot, Search, ShoppingCart, ShieldCheck, CheckCircle, Clock, Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';
import { authApi } from '../../api/auth';
import { buyerApi } from '../../api/buyer';
import { cartsApi } from '../../api/carts';
import { quotesApi } from '../../api/quotes';
import { authorizationsApi } from '../../api/authorizations';
import { checkoutApi } from '../../api/checkout';
import type { Quote, Cart, Product, Authorization, CheckoutOrder } from '../../types';

export const BuyerFlow = () => {
  const [step, setStep] = useState<'intent' | 'products' | 'cart' | 'quote' | 'checkout' | 'success'>('intent');
  const [intentQuery, setIntentQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Setup state
  const [merchantId, setMerchantId] = useState<string | null>(null);
  const [buyerSetup, setBuyerSetup] = useState(false);

  // State populated from API calls
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [activeCart, setActiveCart] = useState<Cart | null>(null);
  const [activeQuote, setActiveQuote] = useState<Quote | null>(null);
  const [activeAuth, setActiveAuth] = useState<Authorization | null>(null);
  const [activeOrder, setActiveOrder] = useState<CheckoutOrder | null>(null);

  useEffect(() => {
    const setupDemoBuyer = async () => {
      try {
        let currentMerchantId = null;
        try {
          const meRes = await authApi.getMe();
          currentMerchantId = meRes.data.merchant_id;
        } catch (err) {
          // Auto-login as demo merchant for development/demo ease
          const loginRes = await authApi.login({ email: 'merchant@demo.com', password: 'password123' });
          localStorage.setItem('access_token', loginRes.data.access_token);
          const meRes2 = await authApi.getMe();
          currentMerchantId = meRes2.data.merchant_id;
        }
        setMerchantId(currentMerchantId);

        // Check if we already have a buyer token
        if (!localStorage.getItem('buyer_token')) {
          const randomEmail = `buyer_${Date.now()}@demo.com`;
          const res = await authApi.register({ email: randomEmail, password: 'password123', role: 'CUSTOMER' });
          localStorage.setItem('buyer_token', res.data.access_token);
        }
        setBuyerSetup(true);
      } catch (err: any) {
        console.error(err);
        const errMsg = err.response?.data?.detail || err.message || 'Unknown error';
        setError(`Failed to setup buyer environment: ${errMsg}`);
        setBuyerSetup(true);
      }
    };
    setupDemoBuyer();
  }, []);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price / 100);
  };

  if (!buyerSetup) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)] mb-4" />
        <p className="text-sm text-[var(--rzp-text-muted)]">Setting up demo buyer session...</p>
      </div>
    );
  }

  const parseIntent = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await buyerApi.parseIntent(intentQuery);
      
      // Real backend might not return recommendations directly in intent response
      // We must search catalogue based on structured intent
      const searchRes = await buyerApi.searchCatalogue({
        category: res.data.intent.category,
        max_budget: res.data.intent.max_budget,
        requirements: res.data.intent.requirements,
        preferences: res.data.intent.preferences
      });
      
      setRecommendations(searchRes.data.results);
      setStep('products');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse intent or search products.');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId: string) => {
    if (!merchantId) {
      setError('Merchant ID not found.');
      return;
    }
    setLoading(true);
    try {
      // Create cart first if we don't have one
      let cartId = activeCart?.id;
      if (!cartId) {
        const cartRes = await cartsApi.createCart({ merchant_id: merchantId });
        cartId = cartRes.data.id;
      }
      
      // Then add item
      const res = await cartsApi.createItem(cartId as string, { product_id: productId, quantity: 1 });
      setActiveCart(res.data);
      setStep('cart');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add to cart.');
    } finally {
      setLoading(false);
    }
  };

  const generateQuote = async () => {
    if (!activeCart) return;
    setLoading(true);
    setError('');
    try {
      // 1. Get deterministic quote
      const quoteRes = await quotesApi.createQuote(activeCart.id);
      setActiveQuote(quoteRes.data);
      
      // 2. Authorize quote against merchant policies
      const authRes = await authorizationsApi.createAuthorization(quoteRes.data.quote_id);
      setActiveAuth(authRes.data);
      
      setStep('quote');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate secure quote or authorization.');
    } finally {
      setLoading(false);
    }
  };

  const processCheckout = async () => {
    if (!activeQuote || !activeAuth) return;
    setLoading(true);
    setError('');
    try {
      if (activeAuth.status !== 'APPROVED') {
        throw new Error('Authorization not approved. Cannot checkout.');
      }
      
      // Create Razorpay Order via backend
      const orderRes = await checkoutApi.createOrder({ 
        quote_id: activeQuote.quote_id,
        authorization_id: activeAuth.authorization_id
      });
      setActiveOrder(orderRes.data);
      
      // In a real app, Razorpay checkout modal would open here using orderRes.data.razorpay_order_id
      setStep('checkout');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Checkout failed.');
    } finally {
      setLoading(false);
    }
  };

  if (!buyerSetup) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--rzp-primary)] mb-4" />
        <p className="text-sm text-gray-500">Setting up demo buyer session...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-8">
      {/* Progress Bar */}
      <div className="mb-8 flex items-center justify-between relative">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-gray-200 -z-10 rounded-full"></div>
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-[var(--rzp-primary)] -z-10 rounded-full transition-all duration-500" 
          style={{ width: `${['intent', 'products', 'cart', 'quote', 'checkout', 'success'].indexOf(step) * 20}%` }}></div>
        
        {['intent', 'products', 'cart', 'quote', 'checkout', 'success'].map((s, i) => (
          <div key={s} className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-colors",
            ['intent', 'products', 'cart', 'quote', 'checkout', 'success'].indexOf(step) >= i
              ? "bg-[var(--rzp-primary)] text-white ring-4 ring-white"
              : "bg-gray-200 text-gray-500 ring-4 ring-white"
          )}>
            {i + 1}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-[var(--rzp-danger-soft)] text-[var(--rzp-danger)] rounded-lg text-sm font-medium">
          {error}
        </div>
      )}

      {/* Step 1: Intent */}
      {step === 'intent' && (
        <Card className="animate-in fade-in slide-in-from-bottom-4 duration-300">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bot className="h-5 w-5 mr-2 text-[var(--rzp-ai)]" /> Ask the AI Buyer
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 bg-[var(--rzp-info-soft)] rounded-md border border-[var(--rzp-info)] flex items-start">
               <Bot className="h-5 w-5 text-[var(--rzp-info)] mr-2 shrink-0 mt-0.5" />
               <p className="text-sm text-[var(--rzp-info)] font-medium">
                 This is the Buyer View. You are currently logged in as a simulated CUSTOMER connecting to the real backend.
               </p>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <textarea
                className="w-full h-32 rounded-lg border border-[var(--rzp-border-strong)] p-3 pl-10 text-sm focus:ring-2 focus:ring-[var(--rzp-primary)] focus:outline-none resize-none"
                placeholder="e.g. Find me ANC headphones under ₹5,000 that arrive within 3 days."
                value={intentQuery}
                onChange={(e) => setIntentQuery(e.target.value)}
              ></textarea>
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button onClick={parseIntent} isLoading={loading} disabled={!intentQuery}>
              Parse Intent & Search
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 2: Products */}
      {step === 'products' && (
        <Card className="animate-in fade-in slide-in-from-right-8 duration-300">
          <CardHeader>
            <CardTitle>AI Recommendation</CardTitle>
          </CardHeader>
          <CardContent>
            {recommendations.length === 0 ? (
              <p className="text-center text-[var(--rzp-text-muted)] py-8">No products match your intent.</p>
            ) : recommendations.map(product => (
              <div key={product.product_id} className="border border-[var(--rzp-border)] rounded-lg p-4 flex justify-between items-center mb-4 hover:shadow-sm transition-shadow">
                <div>
                  <h4 className="font-semibold text-[var(--rzp-text)]">{product.name}</h4>
                  <div className="mt-2 flex space-x-2 flex-wrap gap-y-2">
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Score: {(product.match_score * 100).toFixed(0)}%</span>
                    {product.matched_constraints?.map((c: string) => (
                      <span key={c} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">✓ {c}</span>
                    ))}
                    {product.failed_constraints?.map((c: string) => (
                      <span key={c} className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded">✗ {c}</span>
                    ))}
                  </div>
                </div>
                <div className="text-right flex flex-col items-end">
                  <p className="text-lg font-bold text-[var(--rzp-text)]">{formatPrice(product.price)}</p>
                  <Button onClick={() => addToCart(product.product_id)} isLoading={loading} size="sm" className="mt-2">
                    <ShoppingCart className="h-4 w-4 mr-2" /> Add to Cart
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
          <CardFooter className="justify-between border-t border-[var(--rzp-border)] pt-4 mt-2">
            <Button variant="ghost" onClick={() => setStep('intent')}>Back to search</Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 3: Cart */}
      {step === 'cart' && activeCart && (
        <Card className="animate-in fade-in slide-in-from-right-8 duration-300">
          <CardHeader>
            <CardTitle>Review Cart</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="space-y-4">
               {activeCart.items.map(item => (
                 <div key={item.id} className="flex justify-between items-center border-b border-[var(--rzp-border)] pb-4">
                    <div>
                      <p className="font-medium text-[var(--rzp-text)]">{item.product?.name || `Product: ${item.product_id}`}</p>
                      <p className="text-sm text-[var(--rzp-text-muted)]">Qty: {item.quantity}</p>
                    </div>
                 </div>
               ))}
               <div className="bg-[var(--rzp-warning-soft)] p-3 rounded-md border border-yellow-200 flex items-start">
                 <ShieldCheck className="h-5 w-5 text-[var(--rzp-warning)] mr-2 shrink-0 mt-0.5" />
                 <p className="text-sm text-[var(--rzp-warning)] font-medium">
                   Financial Logic Boundary: The frontend does not calculate the subtotal. We will request a definitive quote from the server.
                 </p>
               </div>
             </div>
          </CardContent>
          <CardFooter className="justify-between">
             <Button variant="ghost" onClick={() => setStep('products')}>Back</Button>
             <Button onClick={generateQuote} isLoading={loading}>
                Generate Secure Quote
             </Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 4: Quote & Policy */}
      {step === 'quote' && activeQuote && activeAuth && (
        <Card className="animate-in fade-in slide-in-from-right-8 duration-300 border-[var(--rzp-primary)] shadow-md">
          <CardHeader className="bg-[var(--rzp-primary-soft)] border-b border-[var(--rzp-primary)]">
            <CardTitle className="text-[var(--rzp-primary)] flex items-center">
              <ShieldCheck className="h-5 w-5 mr-2" /> Server-Verified Quote
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-2 text-sm text-[var(--rzp-text)]">
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
              <div className="pt-2 mt-2 border-t border-dashed border-gray-300 flex justify-between font-bold text-lg">
                <span>Total (Truth)</span>
                <span>{formatPrice(activeQuote.total)}</span>
              </div>
            </div>
            
            <div className={`mt-6 p-3 border rounded-md ${
              activeAuth.status === 'APPROVED' ? 'bg-[var(--rzp-success-soft)] border-[var(--rzp-success)]' :
              activeAuth.status === 'BLOCKED' ? 'bg-[var(--rzp-danger-soft)] border-[var(--rzp-danger)]' :
              'bg-[var(--rzp-warning-soft)] border-[var(--rzp-warning)]'
            }`}>
              <p className={`text-xs font-bold flex items-center justify-center uppercase ${
                activeAuth.status === 'APPROVED' ? 'text-[var(--rzp-success)]' :
                activeAuth.status === 'BLOCKED' ? 'text-[var(--rzp-danger)]' :
                'text-[var(--rzp-warning)]'
              }`}>
                <CheckCircle className="h-4 w-4 mr-1" /> Merchant Policy: {activeAuth.status}
              </p>
            </div>
          </CardContent>
          <CardFooter className="justify-between">
             <Button variant="ghost" onClick={() => setStep('cart')}>Cancel</Button>
             <Button onClick={processCheckout} isLoading={loading} className="bg-[var(--rzp-text)] hover:bg-black" disabled={activeAuth.status !== 'APPROVED'}>
                Create Razorpay Order
             </Button>
          </CardFooter>
        </Card>
      )}

      {/* Step 5: Checkout */}
      {step === 'checkout' && activeOrder && (
        <Card className="animate-in fade-in slide-in-from-right-8 duration-300">
          <CardHeader>
            <CardTitle>Razorpay Payment</CardTitle>
          </CardHeader>
          <CardContent className="py-12">
            <div className="text-center max-w-sm mx-auto">
              <div className="w-16 h-16 bg-[var(--rzp-primary-soft)] rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-[var(--rzp-primary)]">
                <span className="text-[var(--rzp-primary)] font-bold text-2xl">₹</span>
              </div>
              <p className="text-sm text-[var(--rzp-text-secondary)] mb-2">
                Order ID: {activeOrder.razorpay_order_id}
              </p>
              <p className="text-sm text-[var(--rzp-text-muted)] mb-6">
                Waiting for Razorpay standard checkout drop-in.
              </p>
              <Button onClick={() => setStep('success')} isLoading={loading} className="w-full" variant="primary">
                 Mock UI Payment Completion (Demo)
              </Button>
              <p className="text-[10px] uppercase tracking-wider text-[var(--rzp-text-muted)] mt-4 font-semibold">
                * Note: Frontend success does not equal payment truth. The backend webhook is required.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 6: Success */}
      {step === 'success' && (
        <Card className="animate-in zoom-in-95 duration-300 border-[var(--rzp-success)] shadow-lg overflow-hidden">
          <div className="bg-[var(--rzp-success)] h-2 w-full"></div>
          <CardContent className="py-10 text-center">
            <CheckCircle className="h-16 w-16 text-[var(--rzp-success)] mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-[var(--rzp-text)]">Payment Flow Completed (UI)</h2>
            <p className="text-[var(--rzp-text-secondary)] mt-2 text-sm max-w-sm mx-auto">
              The buyer journey is complete. The backend webhook handler would finalize the truth of this transaction.
            </p>
            
            <div className="mt-8 text-left border-t border-[var(--rzp-border)] pt-6">
              <h3 className="font-semibold text-sm mb-4 flex items-center">
                <Clock className="h-4 w-4 mr-2" /> Transaction Audit Trail
              </h3>
              <div className="space-y-3 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[var(--rzp-border)] before:to-transparent">
                <div className="flex items-center text-xs">
                  <div className="w-5 h-5 rounded-full bg-gray-200 border-2 border-white z-10 mr-3"></div>
                  <span className="font-medium">Intent Parsed</span>
                </div>
                <div className="flex items-center text-xs">
                  <div className="w-5 h-5 rounded-full bg-gray-200 border-2 border-white z-10 mr-3"></div>
                  <span className="font-medium">Quote Generated Server-Side</span>
                </div>
                <div className="flex items-center text-xs">
                  <div className="w-5 h-5 rounded-full bg-gray-200 border-2 border-white z-10 mr-3"></div>
                  <span className="font-medium">Policy Authorization ({activeAuth?.status})</span>
                </div>
                <div className="flex items-center text-xs">
                  <div className="w-5 h-5 rounded-full bg-[var(--rzp-success)] border-2 border-white z-10 mr-3"></div>
                  <span className="font-bold text-[var(--rzp-success)]">Waiting for Webhook Verification</span>
                </div>
              </div>
            </div>

            <Button className="mt-8" onClick={() => {
              setStep('intent');
              setIntentQuery('');
              setActiveCart(null);
              setActiveQuote(null);
              setActiveAuth(null);
              setActiveOrder(null);
            }} variant="outline">
               Start New Flow
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
