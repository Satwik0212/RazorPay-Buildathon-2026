import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Plus, Search, MoreVertical, ShieldCheck, X, Loader2, ListChecks, AlertTriangle, CheckCircle, Package } from 'lucide-react';
import { productsApi } from '../../api/products';
import { upsellApi } from '../../api/upsell';
import { analyticsApi } from '../../api/analytics';
import type { Product, UpsellResponse } from '../../types';
import { ImportCatalogueModal } from '../../components/features/catalogue/ImportCatalogueModal';

function getCompleteness(product: Product) {
  let score = 0;
  const issues: string[] = [];
  const metadata = product.metadata || {};

  if (product.description && product.description.length > 50) score += 20;
  else issues.push('Short or missing description');

  if (product.description && product.description.length > 200) score += 10;

  const specs = metadata.specifications || {};
  const specCount = Object.keys(specs).length;
  if (specCount > 0) score += 20;
  else issues.push('Missing structured specifications');

  if (specCount > 5) score += 10;

  const images = metadata.image_urls || [];
  if (images.length > 0) score += 20;
  else issues.push('Missing images');

  if (metadata.brand) score += 10;
  else if (specCount > 0) score += 10;
  else issues.push('Missing brand');

  if (product.category && product.category !== 'Uncategorized') score += 10;
  else issues.push('Uncategorized');

  return {
    score: Math.min(score, 100),
    issues,
    attributeCount: specCount + (metadata.brand ? 1 : 0) + (images.length > 0 ? 1 : 0),
    isReady: score >= 70,
  };
}

export const Catalogue = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [categories, setCategories] = useState<string[]>([]);

  const [page, setPage] = useState(1);
  const limit = 20;

  const [completenessData, setCompletenessData] = useState<any>(null);

  const [actionMenuOpenId, setActionMenuOpenId] = useState<string | null>(null);

  type ModalState = {
    type: 'ADD' | 'EDIT' | 'INVENTORY' | 'DEACTIVATE' | 'REACTIVATE' | 'DETAIL' | 'SET_DELIVERY' | null;
    product?: Product;
  };
  const [modalState, setModalState] = useState<ModalState>({ type: null });
  const [activeTab, setActiveTab] = useState<'info' | 'ai'>('info');
  const [suggestions, setSuggestions] = useState<UpsellResponse | null>(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  const [formData, setFormData] = useState<any>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showImportModal, setShowImportModal] = useState(false);

  const fetchCompleteness = async () => {
    try {
      const res = await analyticsApi.getCatalogueCompleteness();
      setCompletenessData(res.data);
    } catch (err) {
      console.error('Failed to fetch completeness data', err);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await productsApi.getCategories();
      setCategories(res.data);
    } catch (err) {
      console.error('Failed to fetch categories', err);
    }
  };

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {
        limit,
        offset: (page - 1) * limit,
      };
      if (debouncedSearch) params.search = debouncedSearch;
      if (categoryFilter !== 'ALL') params.category = categoryFilter;

      const res = await productsApi.getProducts(params);
      setProducts(res.data.items || []);
      setTotalItems(res.data.total || 0);
    } catch (err) {
      console.error('Failed to fetch products');
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, categoryFilter]);

  useEffect(() => {
    fetchCompleteness();
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset page on search
    }, 500);
    return () => clearTimeout(timer);
  }, [search]);

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCategoryFilter(e.target.value);
    setPage(1); // Reset page on filter
  };

  const openModal = (type: ModalState['type'], product?: Product) => {
    setModalState({ type, product });
    setActionMenuOpenId(null);
    setError('');
    setActiveTab('info');
    setSuggestions(null);

    if (type === 'DETAIL' && product) {
      fetchSuggestions(product.id);
    }

    if (type === 'ADD') {
      setFormData({
        name: '', description: '', category: '', price: '', initial_quantity: 10,
      });
    } else if (type === 'EDIT' && product) {
      setFormData({
        name: product.name,
        description: product.description || '',
        category: product.category,
        price: (product.price / 100).toString(),
      });
    } else if (type === 'INVENTORY' && product) {
      setFormData({ available_quantity: product.inventory?.available_quantity || 0 });
    } else if (type === 'SET_DELIVERY' && product) {
      setFormData({ delivery_days: product.metadata?.delivery_days || '' });
    }
  };

  const fetchSuggestions = async (productId: string) => {
    setSuggestionsLoading(true);
    try {
      const res = await upsellApi.getProductSuggestions(productId, 3);
      setSuggestions(res.data);
    } catch (err) {
      console.error('Failed to fetch suggestions', err);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const closeModal = () => {
    setModalState({ type: null });
    setFormData({});
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      if (modalState.type === 'ADD') {
        await productsApi.createProduct({
          name: formData.name,
          description: formData.description,
          category: formData.category,
          price: Math.round(parseFloat(formData.price) * 100),
          currency: 'INR',
          initial_quantity: parseInt(formData.initial_quantity),
          metadata: {}
        });
      } else if (modalState.type === 'EDIT' && modalState.product) {
        await productsApi.updateProduct(modalState.product.id, {
          name: formData.name,
          description: formData.description,
          category: formData.category,
          price: Math.round(parseFloat(formData.price) * 100),
          metadata: modalState.product.metadata
        });
      } else if (modalState.type === 'INVENTORY' && modalState.product) {
        await productsApi.updateInventory(modalState.product.id, parseInt(formData.available_quantity));
      } else if (modalState.type === 'SET_DELIVERY' && modalState.product) {
        const updatedMetadata = {
          ...(modalState.product.metadata || {}),
          delivery_days: parseInt(formData.delivery_days)
        };
        await productsApi.updateProduct(modalState.product.id, {
          metadata: updatedMetadata
        });
      } else if (modalState.type === 'DEACTIVATE' && modalState.product) {
        await productsApi.deactivateProduct(modalState.product.id);
      } else if (modalState.type === 'REACTIVATE' && modalState.product) {
        await productsApi.reactivateProduct(modalState.product.id);
      }

      closeModal();
      await fetchProducts();
      await fetchCompleteness();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred.');
    } finally {
      setSubmitting(false);
    }
  };

  const menuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setActionMenuOpenId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(price / 100);
  };



  return (
    <div className="space-y-6 relative pb-20">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)]">Catalogue Intelligence</h1>
          <p className="text-sm text-[var(--rzp-text-muted)] mt-1">Review the completeness and metadata readiness of your full product catalog.</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button variant="outline" onClick={() => setShowImportModal(true)}>
            ✦ Import with AI
          </Button>
          <Button onClick={() => openModal('ADD')}>
            <Plus className="h-4 w-4 mr-2" /> Add Product
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex flex-col justify-center">
            <div className="text-sm text-[var(--rzp-text-muted)] flex items-center mb-1">
              <Package className="w-4 h-4 mr-1.5" /> Total Products
            </div>
            <div className="text-2xl font-bold">{completenessData?.total_products || totalItems}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex flex-col justify-center">
            <div className="text-sm text-[var(--rzp-text-muted)] flex items-center mb-1">
              <ListChecks className="w-4 h-4 mr-1.5 text-[var(--rzp-primary)]" /> Highly Complete
            </div>
            <div className="text-2xl font-bold text-[var(--rzp-primary)]">{completenessData?.complete_products || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex flex-col justify-center">
            <div className="text-sm text-[var(--rzp-text-muted)] flex items-center mb-1">
              <AlertTriangle className="w-4 h-4 mr-1.5 text-amber-500" /> Needs Attention
            </div>
            <div className="text-2xl font-bold text-amber-600">{completenessData?.needs_attention || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex flex-col justify-center">
            <div className="text-sm text-[var(--rzp-text-muted)] flex items-center mb-1">
              <CheckCircle className="w-4 h-4 mr-1.5 text-[var(--rzp-success)]" /> Avg Completeness
            </div>
            <div className="text-2xl font-bold text-[var(--rzp-success)]">{completenessData?.average_score || 0}/100</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <div className="p-4 border-b border-[var(--rzp-border)] flex items-center bg-white rounded-t-lg">
          <div className="flex flex-col sm:flex-row gap-4 w-full">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--rzp-text-muted)]" />
              <Input
                className="pl-9"
                placeholder="Search products in database..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="flex gap-2 shrink-0 overflow-x-auto pb-1 sm:pb-0">
              <select
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-w-[150px]"
                value={categoryFilter}
                onChange={handleCategoryChange}
              >
                <option value="ALL">All Categories</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        </div>
        <CardContent className="p-0">
          <div className="overflow-visible">
            <table className="w-full text-sm text-left relative">
              <thead className="text-xs text-[var(--rzp-text-secondary)] uppercase bg-[var(--rzp-surface-subtle)] border-b border-[var(--rzp-border)]">
                <tr>
                  <th className="px-6 py-4 font-medium">Product</th>
                  <th className="px-6 py-4 font-medium">Completeness</th>
                  <th className="px-6 py-4 font-medium">Delivery SLA</th>
                  <th className="px-6 py-4 font-medium">Price</th>
                  <th className="px-6 py-4 font-medium">Inventory</th>
                  <th className="px-6 py-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-[var(--rzp-text-muted)]">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-[var(--rzp-primary)]" />
                      Loading products...
                    </td>
                  </tr>
                ) : products.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-14 text-center">
                      <Package className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                      <p className="text-base font-semibold text-gray-500 mb-1">No products yet</p>
                      <p className="text-sm text-gray-400 mb-5">Add products manually or import your catalogue from a CSV file.</p>
                      <div className="flex justify-center gap-3">
                        <Button variant="outline" onClick={() => openModal('ADD')}>
                          <Plus className="w-4 h-4 mr-1.5" /> Add Product
                        </Button>
                        <Button onClick={() => setShowImportModal(true)}>
                          ✦ Import with AI
                        </Button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  products.map((product) => {
                    const completeness = getCompleteness(product);
                    return (
                    <tr key={product.id} className="border-b border-[var(--rzp-border)] hover:bg-gray-50/50 cursor-pointer" onClick={() => openModal('DETAIL', product)}>
                      <td className="px-6 py-4">
                        <div className="font-medium text-[var(--rzp-text)] line-clamp-1" title={product.name}>{product.name}</div>
                        <div className="text-[var(--rzp-text-muted)] capitalize mb-1 text-xs">{product.category}</div>
                        {!product.is_active && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-100 text-gray-600 border border-gray-200 mt-1">
                            Draft
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col gap-1.5">
                          <div className="flex items-center">
                            <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium border flex items-center
                              ${completeness.isReady ? 'bg-green-50 text-green-700 border-green-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}
                            >
                              {completeness.isReady ? <CheckCircle className="w-3 h-3 mr-1" /> : <AlertTriangle className="w-3 h-3 mr-1" />}
                              {completeness.score}/100
                            </span>
                          </div>
                          {completeness.attributeCount > 0 && (
                            <div className="text-[11px] text-[var(--rzp-text-muted)]">
                              {completeness.attributeCount} structured attributes
                            </div>
                          )}
                          {!completeness.isReady && completeness.issues.length > 0 && (
                            <div className="text-[11px] text-amber-600 line-clamp-1" title={completeness.issues.join(', ')}>
                              Missing: {completeness.issues[0]}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {product.metadata?.delivery_days != null ? (
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5 font-medium text-[var(--rzp-text)]">
                              <span className="text-lg leading-none">🚚</span>
                              <span>{product.metadata.delivery_days} days</span>
                            </div>
                            <Button variant="ghost" size="sm" className="h-auto p-0 mt-1 text-xs text-[var(--rzp-primary)] justify-start hover:bg-transparent hover:underline" onClick={(e) => { e.stopPropagation(); openModal('SET_DELIVERY', product); }}>
                              Edit SLA
                            </Button>
                          </div>
                        ) : (
                          <div className="flex flex-col">
                            <div className="flex items-center gap-1.5 text-amber-600">
                              <AlertTriangle className="h-4 w-4" />
                              <span className="text-sm font-medium">Not configured</span>
                            </div>
                            <Button variant="ghost" size="sm" className="h-auto p-0 mt-1 text-xs text-[var(--rzp-primary)] justify-start hover:bg-transparent hover:underline" onClick={(e) => { e.stopPropagation(); openModal('SET_DELIVERY', product); }}>
                              Set delivery SLA
                            </Button>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 font-medium whitespace-nowrap">
                        {formatPrice(product.price)}
                      </td>
                      <td className="px-6 py-4">
                        <span className={(product.inventory?.available_quantity || 0) > 0 ? '' : 'text-red-500 font-medium'}>
                          {product.inventory?.available_quantity || 0} in stock
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right relative" onClick={e => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          onClick={(e) => { e.stopPropagation(); setActionMenuOpenId(actionMenuOpenId === product.id ? null : product.id); }}
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                        {actionMenuOpenId === product.id && (
                          <div
                            ref={menuRef}
                            className="absolute right-6 top-10 w-48 bg-white rounded-md shadow-lg border border-[var(--rzp-border)] z-50 text-left overflow-hidden"
                          >
                            <button onClick={() => openModal('EDIT', product)} className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left">Edit Details</button>
                            <button onClick={() => openModal('INVENTORY', product)} className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left">Adjust Inventory</button>
                            {product.is_active ? (
                              <button onClick={() => openModal('DEACTIVATE', product)} className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left border-t border-gray-100">Deactivate</button>
                            ) : (
                              <button onClick={() => openModal('REACTIVATE', product)} className="w-full px-4 py-2 text-sm text-green-600 hover:bg-green-50 text-left border-t border-gray-100">Reactivate</button>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  )})
                )}
              </tbody>
            </table>
          </div>
          <div className="p-4 border-t border-[var(--rzp-border)] bg-[var(--rzp-surface-subtle)] rounded-b-lg flex flex-col sm:flex-row justify-between items-center gap-4">
             <div className="flex items-center text-xs text-[var(--rzp-text-muted)]">
                <ShieldCheck className="h-4 w-4 mr-1.5 text-[var(--rzp-primary)]" />
                Real catalogue data • {totalItems} imported products
             </div>

             {/* Pagination Controls */}
             <div className="flex items-center gap-4">
                <span className="text-xs text-gray-500">
                  Showing {totalItems === 0 ? 0 : (page - 1) * limit + 1}–{Math.min(page * limit, totalItems)} of {totalItems}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(p => p - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page * limit >= totalItems || totalItems === 0}
                    onClick={() => setPage(p => p + 1)}
                  >
                    Next
                  </Button>
                </div>
             </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Catalogue Import Modal */}
      {showImportModal && (
        <ImportCatalogueModal
          onClose={() => setShowImportModal(false)}
          onImportComplete={() => {
            setShowImportModal(false);
            fetchProducts();
          }}
        />
      )}

      {/* Basic Modals (Add, Edit, Inventory, Deactivate) */}
      {modalState.type && modalState.type !== 'DETAIL' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <Card className="w-full max-w-md bg-white shadow-xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-[var(--rzp-border)] shrink-0">
              <h2 className="text-lg font-semibold">
                {modalState.type === 'ADD' && 'Add New Product'}
                {modalState.type === 'EDIT' && 'Edit Product'}
                {modalState.type === 'INVENTORY' && 'Adjust Inventory'}
                {modalState.type === 'DEACTIVATE' && 'Deactivate Product'}
                {modalState.type === 'REACTIVATE' && 'Reactivate Product'}
                {modalState.type === 'SET_DELIVERY' && 'Set Delivery SLA'}
              </h2>
              <Button variant="ghost" size="sm" onClick={closeModal} className="h-8 w-8 p-0 shrink-0 rounded-full hover:bg-gray-100">
                <X className="h-5 w-5 text-gray-500" />
              </Button>
            </div>

            <div className="p-4 overflow-y-auto">
              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-md border border-red-200">
                  {error}
                </div>
              )}

              {(modalState.type === 'ADD' || modalState.type === 'EDIT') && (
                <form id="product-form" onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Name <span className="text-red-500">*</span></label>
                    <Input required value={formData.name || ''} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="e.g., Wireless Earbuds" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Description</label>
                    <textarea
                      className="w-full flex min-h-[80px] rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      value={formData.description || ''}
                      onChange={e => setFormData({...formData, description: e.target.value})}
                      placeholder="Product details..."
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Category <span className="text-red-500">*</span></label>
                      <Input required value={formData.category || ''} onChange={e => setFormData({...formData, category: e.target.value})} placeholder="e.g., Electronics" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Price (INR) <span className="text-red-500">*</span></label>
                      <Input required type="number" step="0.01" min="0" value={formData.price || ''} onChange={e => setFormData({...formData, price: e.target.value})} placeholder="0.00" />
                    </div>
                  </div>
                  {modalState.type === 'ADD' && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Initial Inventory <span className="text-red-500">*</span></label>
                      <Input required type="number" min="0" value={formData.initial_quantity || ''} onChange={e => setFormData({...formData, initial_quantity: e.target.value})} />
                    </div>
                  )}
                </form>
              )}

              {modalState.type === 'INVENTORY' && (
                <form id="product-form" onSubmit={handleSubmit} className="space-y-4">
                  <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 mb-4 border border-gray-200">
                    Target: <strong>{modalState.product?.name}</strong>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Available Quantity</label>
                    <Input required type="number" min="0" value={formData.available_quantity ?? ''} onChange={e => setFormData({...formData, available_quantity: e.target.value})} />
                  </div>
                </form>
              )}

              {modalState.type === 'SET_DELIVERY' && (
                <form id="product-form" onSubmit={handleSubmit} className="space-y-4">
                  <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 mb-4 border border-gray-200">
                    Target: <strong>{modalState.product?.name}</strong>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Delivery SLA (Days)</label>
                    <select
                      required
                      className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      value={formData.delivery_days || ''}
                      onChange={e => setFormData({...formData, delivery_days: e.target.value})}
                    >
                      <option value="" disabled>Select delivery days...</option>
                      <option value="1">1 day (Speed/Express)</option>
                      <option value="2">2 days (Standard)</option>
                      <option value="3">3 days</option>
                      <option value="4">4 days</option>
                      <option value="5">5 days</option>
                      <option value="7">7 days</option>
                    </select>
                    <p className="text-xs text-[var(--rzp-text-muted)] mt-1">This value is evaluated by AI Buyer scenarios (e.g., Speed Priority).</p>
                  </div>
                </form>
              )}

              {(modalState.type === 'DEACTIVATE' || modalState.type === 'REACTIVATE') && (
                <form id="product-form" onSubmit={handleSubmit} className="space-y-4">
                  <p className="text-sm text-gray-700">
                    Are you sure you want to {modalState.type.toLowerCase()} <strong>{modalState.product?.name}</strong>?
                  </p>
                </form>
              )}
            </div>

            <div className="p-4 border-t border-[var(--rzp-border)] flex justify-end gap-3 shrink-0 bg-gray-50 rounded-b-xl">
              <Button type="button" variant="outline" onClick={closeModal} disabled={submitting}>Cancel</Button>
              <Button type="submit" form="product-form" disabled={submitting} className={modalState.type === 'DEACTIVATE' ? 'bg-red-600 hover:bg-red-700 text-white' : ''}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {modalState.type === 'DEACTIVATE' ? 'Deactivate' :
                 modalState.type === 'REACTIVATE' ? 'Reactivate' :
                 modalState.type === 'INVENTORY' ? 'Update Inventory' :
                 modalState.type === 'SET_DELIVERY' ? 'Save Delivery' : 'Save Details'}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* DETAIL MODAL (Completeness / Metadata View) */}
      {modalState.type === 'DETAIL' && modalState.product && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <Card className="w-full max-w-2xl bg-white shadow-xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-[var(--rzp-border)] shrink-0 bg-gray-50">
              <div className="flex flex-col">
                <h2 className="text-lg font-semibold text-[var(--rzp-text)] line-clamp-1" title={modalState.product.name}>{modalState.product.name}</h2>
                <div className="text-xs text-[var(--rzp-text-muted)]">{modalState.product.category} • {formatPrice(modalState.product.price)}</div>
              </div>
              <Button variant="ghost" size="sm" onClick={closeModal} className="h-8 w-8 p-0 shrink-0 rounded-full hover:bg-gray-200">
                <X className="h-5 w-5 text-gray-500" />
              </Button>
            </div>

            <div className="flex border-b border-[var(--rzp-border)] shrink-0 px-4">
              <button
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${activeTab === 'info' ? 'border-[var(--rzp-primary)] text-[var(--rzp-primary)]' : 'border-transparent text-[var(--rzp-text-muted)] hover:text-[var(--rzp-text)]'}`}
                onClick={() => setActiveTab('info')}
              >
                Product Details
              </button>
              <button
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors flex items-center ${activeTab === 'ai' ? 'border-[var(--rzp-primary)] text-[var(--rzp-primary)]' : 'border-transparent text-[var(--rzp-text-muted)] hover:text-[var(--rzp-text)]'}`}
                onClick={() => setActiveTab('ai')}
              >
                <ListChecks className="w-3.5 h-3.5 mr-1.5" /> Completeness & Metadata
              </button>
            </div>

            <div className="overflow-y-auto flex-1 p-0">
              {activeTab === 'info' ? (
                <div className="p-4 space-y-6">
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Description</h3>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {modalState.product.description || <span className="italic text-gray-400">No description provided</span>}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-50 rounded border border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">Inventory</div>
                      <div className="text-sm font-medium">{modalState.product.inventory?.available_quantity || 0} units available</div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded border border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">Status</div>
                      <div className="text-sm font-medium">
                        {modalState.product.is_active ? 'Active (Discoverable)' : 'Draft (Hidden)'}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 space-y-6">
                  {(() => {
                    const completeness = getCompleteness(modalState.product);
                    return (
                      <>
                        <div className="flex items-center gap-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <div className="shrink-0 flex items-center justify-center w-16 h-16 rounded-full bg-white border-4 border-gray-100 relative">
                            <span className="text-xl font-bold">{completeness.score}</span>
                            <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 36 36">
                              <path
                                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                fill="none"
                                stroke={completeness.isReady ? "#10b981" : "#f59e0b"}
                                strokeWidth="4"
                                strokeDasharray={`${completeness.score}, 100`}
                                className="transition-all duration-1000 ease-out"
                              />
                            </svg>
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">Completeness Score</h3>
                            <p className="text-sm text-gray-600">
                              {completeness.isReady ? "This product has excellent metadata, making it highly discoverable by filters and engines." : "This product is lacking crucial descriptive metadata."}
                            </p>
                          </div>
                        </div>

                        {!completeness.isReady && completeness.issues.length > 0 && (
                          <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                            <h4 className="text-xs font-semibold text-amber-800 uppercase tracking-wider mb-2 flex items-center">
                              <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Missing Information
                            </h4>
                            <ul className="list-disc pl-5 text-sm text-amber-700 space-y-1">
                              {completeness.issues.map((issue, i) => (
                                <li key={i}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div>
                          <h4 className="text-sm font-semibold mb-3 flex items-center">
                            Structured Attributes
                            <span className="ml-2 px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600 text-xs font-normal">
                              {completeness.attributeCount} extracted
                            </span>
                          </h4>
                          {Object.keys(modalState.product.metadata?.specifications || {}).length > 0 ? (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                              {Object.entries(modalState.product.metadata?.specifications || {}).map(([key, value]) => (
                                <div key={key} className="flex flex-col border-b border-gray-100 pb-1">
                                  <span className="text-xs text-gray-500">{key}</span>
                                  <span className="text-sm font-medium text-gray-900 line-clamp-1" title={String(value)}>{String(value)}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 italic">No structured specifications found in product metadata.</p>
                          )}
                        </div>

                        <div>
                          <h4 className="text-sm font-semibold mb-3 flex items-center">
                            Core Capabilities & Logistics
                          </h4>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                            <div className="flex flex-col border-b border-gray-100 pb-1">
                              <span className="text-xs text-gray-500">Delivery Days</span>
                              <span className="text-sm font-medium text-gray-900">
                                {modalState.product.metadata?.delivery_days !== undefined
                                  ? `${modalState.product.metadata.delivery_days} days`
                                  : <span className="text-amber-600 italic">Missing</span>}
                              </span>
                            </div>
                            <div className="flex flex-col border-b border-gray-100 pb-1">
                              <span className="text-xs text-gray-500">Return Window</span>
                              <span className="text-sm font-medium text-gray-900">
                                {modalState.product.metadata?.return_days !== undefined
                                  ? `${modalState.product.metadata.return_days} days`
                                  : <span className="text-gray-400 italic">Not specified</span>}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="pt-4 border-t border-[var(--rzp-border)]">
                          <h4 className="text-sm font-semibold mb-3">Deterministic Recommendations</h4>
                          <p className="text-xs text-gray-500 mb-4">Upsell and cross-sell relationships algorithmically calculated based on price tiers and category boundaries across the entire {completenessData?.total_products || totalItems}-item catalogue.</p>

                          {suggestionsLoading ? (
                            <div className="flex items-center justify-center p-6">
                              <Loader2 className="w-6 h-6 animate-spin text-[var(--rzp-primary)]" />
                            </div>
                          ) : suggestions ? (
                            <div className="space-y-4">
                              <div>
                                <h5 className="text-xs font-bold text-gray-700 uppercase mb-2">Upsell Candidates ({suggestions.upsell.length})</h5>
                                {suggestions.upsell.length > 0 ? (
                                  <div className="flex flex-col gap-2">
                                    {suggestions.upsell.map(u => (
                                      <div key={u.product_id} className="text-sm p-2 bg-gray-50 border border-gray-100 rounded flex justify-between items-center">
                                        <div className="truncate pr-4 flex-1 font-medium">{u.name}</div>
                                        <div className="font-medium shrink-0 text-[var(--rzp-primary)]">{formatPrice(u.price)}</div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-sm text-gray-500">No strictly superior alternatives found in same category.</div>
                                )}
                              </div>
                              <div>
                                <h5 className="text-xs font-bold text-gray-700 uppercase mb-2">Cross-sell Candidates ({suggestions.cross_sell.length})</h5>
                                {suggestions.cross_sell.length > 0 ? (
                                  <div className="flex flex-col gap-2">
                                    {suggestions.cross_sell.map(c => (
                                      <div key={c.product_id} className="text-sm p-2 bg-gray-50 border border-gray-100 rounded flex justify-between items-center">
                                        <div className="truncate pr-4 flex-1">{c.name}</div>
                                        <div className="text-xs text-gray-500 shrink-0 border border-gray-200 bg-white px-2 py-0.5 rounded">{c.category}</div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-sm text-gray-500">No complementary items identified.</div>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-red-500">Failed to load recommendations.</div>
                          )}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
