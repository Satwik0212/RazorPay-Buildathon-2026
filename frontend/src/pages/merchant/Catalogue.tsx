import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Plus, Search, MoreVertical, ShieldCheck } from 'lucide-react';
import { apiClient } from '../../api/client';
import type { Product } from '../../types';

export const Catalogue = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await apiClient.get('/products');
        setProducts(res.data.items || []);
      } catch (err) {
        console.error('Failed to fetch products');
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(price / 100);
  };

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) || 
    p.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--rzp-text)]">Catalogue</h1>
          <p className="text-sm text-[var(--rzp-text-muted)]">Manage products and optimize them for AI buyers.</p>
        </div>
        <Button className="flex-shrink-0">
          <Plus className="h-4 w-4 mr-2" /> Add Product
        </Button>
      </div>

      <div className="bg-[var(--rzp-surface-subtle)] p-3 rounded-lg border border-[var(--rzp-border)] flex items-start text-sm">
        <ShieldCheck className="h-5 w-5 text-[var(--rzp-primary)] mr-2 shrink-0" />
        <p className="text-[var(--rzp-text-secondary)]">
          <strong>Data Source:</strong> Products are loaded from the backend canonical `/api/v1/products` endpoint.
        </p>
      </div>

      <Card>
        <div className="p-4 border-b border-[var(--rzp-border)] flex items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--rzp-text-muted)]" />
            <Input 
              className="pl-9" 
              placeholder="Search products..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-[var(--rzp-text-secondary)] uppercase bg-[var(--rzp-surface-subtle)] border-b border-[var(--rzp-border)]">
                <tr>
                  <th className="px-6 py-4 font-medium">Product</th>
                  <th className="px-6 py-4 font-medium">Price</th>
                  <th className="px-6 py-4 font-medium">Inventory</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-[var(--rzp-text-muted)]">
                      Loading products...
                    </td>
                  </tr>
                ) : filteredProducts.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-[var(--rzp-text-muted)]">
                      No products found.
                    </td>
                  </tr>
                ) : (
                  filteredProducts.map((product) => (
                    <tr key={product.id} className="border-b border-[var(--rzp-border)] hover:bg-gray-50/50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-[var(--rzp-text)]">{product.name}</div>
                        <div className="text-[var(--rzp-text-muted)] capitalize">{product.category}</div>
                      </td>
                      <td className="px-6 py-4 font-medium">
                        {formatPrice(product.price)}
                      </td>
                      <td className="px-6 py-4">
                        {product.inventory?.available_quantity || 0} in stock
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${product.is_active ? 'bg-[var(--rzp-success-soft)] text-[var(--rzp-success)]' : 'bg-gray-100 text-gray-600'}`}>
                          {product.is_active ? 'Active' : 'Draft'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
