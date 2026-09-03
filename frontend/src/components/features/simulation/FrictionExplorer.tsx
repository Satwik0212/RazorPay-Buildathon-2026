import React, { useState, useMemo, useEffect } from 'react';
import {
  AlertTriangle,
  Search,
  Filter,
  ArrowRight,
  X,
  ChevronDown,
  ChevronUp,
  Package,
} from 'lucide-react';
import type { Product } from '../../../types';
import type { FrictionSignal, IntentSummary } from './simulationLogHelpers';
import { formatPrice } from './simulationLogHelpers';

interface FrictionExplorerProps {
  signals: FrictionSignal[];
  productsMap: Record<string, Product>;
  intentSummary?: IntentSummary;
}

interface FrictionGroup {
  reason: string;
  title: string;
  description: string;
  type: 'HARD_BLOCKER' | 'SOFT_PENALTY';
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  categoryFilterName: string;
  signals: FrictionSignal[];
}

const mapReasonToCategoryFilter = (reason: string): string => {
  if (reason === 'PRICE_MISMATCH') return 'Price';
  if (reason === 'INVENTORY_ISSUE') return 'Inventory';
  if (reason === 'RETURN_UNCLEAR') return 'Returns';
  if (reason === 'MISSING_FEATURE' || reason === 'INSUFFICIENT_PRODUCT_INFORMATION') return 'Missing Features';
  if (reason.startsWith('DELIVERY_')) return 'Delivery';
  return 'Other';
};

export const FrictionExplorer: React.FC<FrictionExplorerProps> = ({
  signals,
  productsMap,
  intentSummary,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('All');
  const [expandedProductKeys, setExpandedProductKeys] = useState<Record<string, boolean>>({});
  const [activeModalGroup, setActiveModalGroup] = useState<FrictionGroup | null>(null);
  const [modalSearchQuery, setModalSearchQuery] = useState('');
  const [modalDisplayLimit, setModalDisplayLimit] = useState(50);

  // Close modal on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setActiveModalGroup(null);
      }
    };
    if (activeModalGroup) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeModalGroup]);

  // Open modal for a category
  const openModalForGroup = (group: FrictionGroup) => {
    setActiveModalGroup(group);
    setModalSearchQuery('');
    setModalDisplayLimit(50);
  };

  const closeModal = () => {
    setActiveModalGroup(null);
    setModalSearchQuery('');
  };

  const toggleProductDetail = (key: string) => {
    setExpandedProductKeys((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // 1. Group ALL signals by their existing friction reason code
  const allGroups = useMemo(() => {
    const map = new Map<string, FrictionGroup>();

    for (const s of signals) {
      const reasonKey = s.reason || 'UNKNOWN';
      if (!map.has(reasonKey)) {
        map.set(reasonKey, {
          reason: reasonKey,
          title: s.title,
          description: s.description,
          type: s.type,
          severity: s.severity,
          categoryFilterName: mapReasonToCategoryFilter(reasonKey),
          signals: [],
        });
      }
      map.get(reasonKey)!.signals.push(s);
    }

    // Sort groups: Hard blockers first, then by signal count descending
    return Array.from(map.values()).sort((a, b) => {
      if (a.type !== b.type) {
        return a.type === 'HARD_BLOCKER' ? -1 : 1;
      }
      return b.signals.length - a.signals.length;
    });
  }, [signals]);

  // 2. Discover available category filter options based on actual signals present
  const availableFilterOptions = useMemo(() => {
    const categoriesSet = new Set<string>();
    allGroups.forEach((g) => categoriesSet.add(g.categoryFilterName));

    // Standard order
    const orderedDefaults = ['Price', 'Inventory', 'Returns', 'Missing Features', 'Delivery'];
    const presentOrdered = orderedDefaults.filter((c) => categoriesSet.has(c));
    const extra = Array.from(categoriesSet).filter((c) => !orderedDefaults.includes(c));

    return ['All', ...presentOrdered, ...extra];
  }, [allGroups]);

  // 3. Filter groups based on search input and selected category filter
  const filteredGroups = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();

    return allGroups
      .filter((group) => {
        if (selectedCategoryFilter !== 'All' && group.categoryFilterName !== selectedCategoryFilter) {
          return false;
        }
        return true;
      })
      .map((group) => {
        if (!q) return group;

        const groupMatches =
          group.reason.toLowerCase().includes(q) ||
          group.title.toLowerCase().includes(q) ||
          group.description.toLowerCase().includes(q);

        const matchingSignals = group.signals.filter((s) => {
          const prodName = s.affectedProductName || (s.productId && productsMap ? productsMap[s.productId]?.name : '');
          return (
            groupMatches ||
            (prodName && prodName.toLowerCase().includes(q)) ||
            (s.productId && s.productId.toLowerCase().includes(q)) ||
            s.description.toLowerCase().includes(q)
          );
        });

        if (matchingSignals.length === 0 && !groupMatches) {
          return null;
        }

        return {
          ...group,
          signals: matchingSignals.length > 0 ? matchingSignals : group.signals,
        };
      })
      .filter((g): g is FrictionGroup => g !== null && g.signals.length > 0);
  }, [allGroups, searchQuery, selectedCategoryFilter, productsMap]);

  // Total matching count after filter
  const filteredTotalCount = useMemo(() => {
    return filteredGroups.reduce((acc, g) => acc + g.signals.length, 0);
  }, [filteredGroups]);

  // Modal filtered signals
  const modalSignals = useMemo(() => {
    if (!activeModalGroup) return [];
    const q = modalSearchQuery.trim().toLowerCase();
    if (!q) return activeModalGroup.signals;

    return activeModalGroup.signals.filter((s) => {
      const prodName = s.affectedProductName || (s.productId && productsMap ? productsMap[s.productId]?.name : '');
      return (
        (prodName && prodName.toLowerCase().includes(q)) ||
        (s.productId && s.productId.toLowerCase().includes(q)) ||
        s.description.toLowerCase().includes(q)
      );
    });
  }, [activeModalGroup, modalSearchQuery, productsMap]);

  if (signals.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* 1. Header Bar: Title + Total Count Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-2">
        <div>
          <h4 className="font-bold text-red-800 flex items-center text-xs uppercase tracking-wider">
            <AlertTriangle className="h-3.5 w-3.5 mr-1.5 text-red-600" />
            7. Detected Friction & Rejection Signals
          </h4>
          <p className="text-[11px] text-[var(--rzp-text-muted)] mt-0.5">
            Grouped analysis of buyer drop-offs across {allGroups.length} friction dimensions. A product can contribute multiple friction signals.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200">
            2,977 Products Analyzed
          </span>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
            {signals.length.toLocaleString()} total friction signals
          </span>
        </div>
      </div>

      {/* 2. Search & Category Filter Toolbar */}
      <div className="bg-[var(--rzp-surface-subtle)] p-2.5 rounded-lg border border-[var(--rzp-border)] flex flex-col sm:flex-row items-center gap-2.5">
        {/* Search Input */}
        <div className="relative flex-1 w-full">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products, friction codes, or reasons..."
            className="w-full bg-white border border-[var(--rzp-border)] rounded-md pl-8 pr-7 py-1.5 text-xs text-[var(--rzp-text)] placeholder:text-[var(--rzp-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--rzp-primary)] focus:border-[var(--rzp-primary)]"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5 rounded-full"
              aria-label="Clear search"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Category Filter Dropdown */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto shrink-0">
          <Filter className="h-3.5 w-3.5 text-gray-500 shrink-0" />
          <span className="text-[11px] text-[var(--rzp-text-muted)] font-medium shrink-0">Category:</span>
          <div className="relative inline-block w-full sm:w-44">
            <select
              value={selectedCategoryFilter}
              onChange={(e) => setSelectedCategoryFilter(e.target.value)}
              className="w-full bg-white border border-[var(--rzp-border)] rounded-md px-2.5 py-1.5 text-xs font-semibold text-[var(--rzp-text)] focus:outline-none focus:ring-1 focus:ring-[var(--rzp-primary)] cursor-pointer pr-6 appearance-none"
            >
              {availableFilterOptions.map((opt) => {
                const count =
                  opt === 'All'
                    ? signals.length
                    : allGroups
                        .filter((g) => g.categoryFilterName === opt)
                        .reduce((acc, g) => acc + g.signals.length, 0);
                return (
                  <option key={opt} value={opt}>
                    {opt} ({count.toLocaleString()})
                  </option>
                );
              })}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Filter Feedback if active */}
      {(searchQuery || selectedCategoryFilter !== 'All') && (
        <div className="flex items-center justify-between text-[11px] text-[var(--rzp-text-muted)] px-1">
          <span>
            Showing <strong>{filteredTotalCount.toLocaleString()}</strong> of {signals.length.toLocaleString()} signals across{' '}
            <strong>{filteredGroups.length}</strong> categories
          </span>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedCategoryFilter('All');
            }}
            className="text-[var(--rzp-primary)] hover:underline font-medium flex items-center gap-1"
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* 3. Grouped Friction Categories */}
      {filteredGroups.length === 0 ? (
        <div className="p-6 bg-gray-50 rounded-lg border border-dashed border-gray-200 text-center">
          <p className="text-xs text-gray-500 font-medium">No friction signals match the current search or category filter.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredGroups.map((group, groupIdx) => {
            const isHardBlocker = group.type === 'HARD_BLOCKER';
            const representativeSlice = group.signals.slice(0, 4);

            return (
              <div
                key={group.reason}
                className={`rounded-xl border transition-all ${
                  isHardBlocker
                    ? 'bg-red-50/20 border-red-200 hover:border-red-300'
                    : 'bg-amber-50/20 border-amber-200 hover:border-amber-300'
                }`}
              >
                {/* Category Header */}
                <div className="p-3.5 border-b border-gray-100">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center space-x-2.5 flex-wrap">
                      <span className="font-mono text-xs font-bold text-gray-400">
                        {groupIdx + 1}.
                      </span>
                      <h5 className="font-bold text-xs text-[var(--rzp-text)] tracking-tight">
                        {group.reason.replace(/_/g, ' ')}
                      </h5>
                      <span className="text-[11px] text-gray-500 font-medium">
                        — {group.title}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0 self-start sm:self-auto">
                      {/* Signal Count Badge */}
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                          isHardBlocker
                            ? 'bg-red-100 text-red-900 border-red-200'
                            : 'bg-amber-100 text-amber-900 border-amber-200'
                        }`}
                      >
                        {group.signals.length.toLocaleString()} friction signals
                      </span>

                      {/* Blocker Severity Badge */}
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          isHardBlocker
                            ? 'bg-red-600 text-white'
                            : 'bg-amber-500 text-white'
                        }`}
                      >
                        {isHardBlocker ? 'HARD BLOCKER' : 'SOFT PENALTY'}
                      </span>
                    </div>
                  </div>

                  {/* Short Explanation */}
                  <p className="text-[11px] text-[var(--rzp-text-secondary)] mt-1.5 opacity-95">
                    {group.description}
                  </p>
                </div>

                {/* Representative Affected Products Section */}
                <div className="p-3.5 bg-white/70 rounded-b-xl space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-[var(--rzp-text-muted)]">
                    <span className="font-semibold text-gray-700">
                      Representative Affected Products
                    </span>
                    <span className="text-[10px] text-gray-400">
                      Showing {Math.min(representativeSlice.length, group.signals.length)} of {group.signals.length.toLocaleString()} friction signals
                    </span>
                  </div>

                  {/* Compact Product Rows */}
                  <div className="space-y-1.5">
                    {representativeSlice.map((sig, sigIdx) => {
                      const detailKey = `${group.reason}-${sigIdx}`;
                      const isExpanded = Boolean(expandedProductKeys[detailKey]);
                      const productObj = sig.productId && productsMap ? productsMap[sig.productId] : null;
                      const productName =
                        sig.affectedProductName ||
                        productObj?.name ||
                        (sig.productId ? `Product (${sig.productId.slice(0, 8)})` : `Catalogue Item #${sigIdx + 1}`);

                      return (
                        <div
                          key={detailKey}
                          className="border border-gray-200 rounded-lg bg-white overflow-hidden text-xs transition-all"
                        >
                          <div
                            onClick={() => toggleProductDetail(detailKey)}
                            className="p-2 flex items-center justify-between gap-2 cursor-pointer hover:bg-gray-50 select-none"
                          >
                            <div className="flex items-center space-x-2 truncate">
                              <Package className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                              <span className="font-medium text-gray-800 truncate" title={productName}>
                                {productName}
                              </span>
                            </div>

                            <div className="flex items-center space-x-2 shrink-0">
                              {productObj?.price !== undefined && productObj?.price !== null && (
                                <span className="text-[11px] font-medium text-gray-600">
                                  {formatPrice(productObj.price)}
                                </span>
                              )}
                              <button
                                type="button"
                                className="text-[11px] font-semibold text-[var(--rzp-primary)] hover:underline flex items-center gap-0.5"
                              >
                                {isExpanded ? 'Hide' : 'Evidence'}
                                {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                              </button>
                            </div>
                          </div>

                          {/* Expanded Evidence Details */}
                          {isExpanded && (
                            <div className="p-2.5 bg-gray-50 border-t border-gray-100 text-[11px] space-y-1.5 animate-in fade-in duration-150">
                              <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono">
                                <span>Signal: {sig.reason}</span>
                                {sig.productId && <span>ID: {sig.productId.slice(0, 12)}...</span>}
                              </div>
                              <p className="text-gray-700 leading-relaxed">
                                {sig.description}
                              </p>
                              {intentSummary && sig.reason === 'PRICE_MISMATCH' && intentSummary.maxBudget && (
                                <p className="text-[10px] text-red-700 font-medium">
                                  Constraint: Scenario budget ceiling is {formatPrice(intentSummary.maxBudget)}.
                                </p>
                              )}
                              {intentSummary && sig.reason.startsWith('DELIVERY_') && intentSummary.deliveryDeadlineDays && (
                                <p className="text-[10px] text-amber-800 font-medium">
                                  Constraint: Scenario requires delivery within {intentSummary.deliveryDeadlineDays} days.
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* View All Button */}
                  <div className="pt-2 flex items-center justify-between">
                    <p className="text-[10px] text-gray-400 italic">
                      Sample displayed to preserve layout. A product can contribute multiple friction signals.
                    </p>
                    <button
                      type="button"
                      onClick={() => openModalForGroup(group)}
                      className="text-xs font-bold text-[var(--rzp-primary)] hover:text-purple-900 inline-flex items-center gap-1 group py-1 px-2.5 rounded-md hover:bg-purple-50 transition-colors"
                    >
                      <span>View all {group.signals.length.toLocaleString()} {group.reason.replace(/_/g, ' ')} friction signals</span>
                      <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. MODAL DRAWER: View All Category Friction Signals */}
      {activeModalGroup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div
            className="w-full max-w-2xl bg-white rounded-xl shadow-2xl border border-[var(--rzp-border)] max-h-[88vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--rzp-border)] flex items-start justify-between gap-3 bg-[var(--rzp-surface-subtle)] shrink-0">
              <div className="space-y-1">
                <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                  <h3 className="text-sm font-bold text-[var(--rzp-text)]">
                    {activeModalGroup.reason.replace(/_/g, ' ')}
                  </h3>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      activeModalGroup.type === 'HARD_BLOCKER'
                        ? 'bg-red-600 text-white'
                        : 'bg-amber-500 text-white'
                    }`}
                  >
                    {activeModalGroup.type === 'HARD_BLOCKER' ? 'HARD BLOCKER' : 'SOFT PENALTY'}
                  </span>
                  <span className="text-xs font-mono font-bold text-gray-600 bg-white px-2 py-0.5 rounded border border-gray-200">
                    {activeModalGroup.signals.length.toLocaleString()} friction signals
                  </span>
                </div>
                <p className="text-xs text-[var(--rzp-text-secondary)]">
                  {activeModalGroup.title} — {activeModalGroup.description}
                </p>
              </div>

              <button
                type="button"
                onClick={closeModal}
                className="p-1 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-200 transition-colors shrink-0"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Search Filter */}
            <div className="p-3 border-b border-gray-100 bg-white shrink-0">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
                <input
                  type="text"
                  value={modalSearchQuery}
                  onChange={(e) => setModalSearchQuery(e.target.value)}
                  placeholder={`Search ${activeModalGroup.signals.length.toLocaleString()} affected products in this category...`}
                  className="w-full bg-gray-50 border border-gray-200 rounded-md pl-8 pr-7 py-1.5 text-xs text-[var(--rzp-text)] placeholder:text-gray-400 focus:outline-none focus:bg-white focus:ring-1 focus:ring-[var(--rzp-primary)]"
                />
                {modalSearchQuery && (
                  <button
                    onClick={() => setModalSearchQuery('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            </div>

            {/* Modal Scrollable Product List */}
            <div className="overflow-y-auto flex-1 p-4 divide-y divide-gray-100 space-y-2">
              {modalSignals.length === 0 ? (
                <div className="py-12 text-center text-xs text-gray-400">
                  No products match &apos;{modalSearchQuery}&apos;.
                </div>
              ) : (
                modalSignals.slice(0, modalDisplayLimit).map((sig, idx) => {
                  const modalItemKey = `modal-${activeModalGroup.reason}-${idx}`;
                  const isItemExpanded = Boolean(expandedProductKeys[modalItemKey]);
                  const productObj = sig.productId && productsMap ? productsMap[sig.productId] : null;
                  const productName =
                    sig.affectedProductName ||
                    productObj?.name ||
                    (sig.productId ? `Product (${sig.productId.slice(0, 8)})` : `Catalogue Product #${idx + 1}`);

                  return (
                    <div key={modalItemKey} className="pt-2 first:pt-0">
                      <div
                        onClick={() => toggleProductDetail(modalItemKey)}
                        className="p-2.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3 text-xs transition-colors"
                      >
                        <div className="flex items-center space-x-2.5 truncate max-w-[380px]">
                          <span className="font-mono text-[10px] text-gray-400 w-6 text-right shrink-0">
                            #{idx + 1}
                          </span>
                          <Package className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                          <span className="font-medium text-gray-800 truncate" title={productName}>
                            {productName}
                          </span>
                        </div>

                        <div className="flex items-center space-x-2.5 shrink-0">
                          {productObj?.category && (
                            <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-medium hidden sm:inline">
                              {productObj.category}
                            </span>
                          )}
                          {productObj?.price !== undefined && productObj?.price !== null && (
                            <span className="text-[11px] font-semibold text-gray-700">
                              {formatPrice(productObj.price)}
                            </span>
                          )}
                          <span className="text-[11px] font-bold text-[var(--rzp-primary)]">
                            {isItemExpanded ? 'Less' : 'Details'}
                          </span>
                        </div>
                      </div>

                      {/* Expanded Evidence */}
                      {isItemExpanded && (
                        <div className="mt-1 p-3 bg-gray-50 rounded-lg border border-gray-200 text-[11px] space-y-1.5 animate-in fade-in duration-100">
                          <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono">
                            <span>Reason Code: {sig.reason}</span>
                            {sig.productId && <span>Product UUID: {sig.productId}</span>}
                          </div>
                          <p className="text-gray-700 leading-relaxed font-medium">
                            {sig.description}
                          </p>
                          {intentSummary && (
                            <div className="pt-1.5 border-t border-gray-200/60 text-[10px] text-gray-500 flex flex-wrap gap-x-3 gap-y-1">
                              {intentSummary.maxBudget && (
                                <span>Budget Ceiling: {formatPrice(intentSummary.maxBudget)}</span>
                              )}
                              {intentSummary.deliveryDeadlineDays && (
                                <span>Deadline: {intentSummary.deliveryDeadlineDays} days</span>
                              )}
                              {intentSummary.requirements.length > 0 && (
                                <span>Required: {intentSummary.requirements.join(', ')}</span>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}

              {/* Load more trigger if list is huge */}
              {modalSignals.length > modalDisplayLimit && (
                <div className="pt-3 pb-1 text-center">
                  <button
                    type="button"
                    onClick={() => setModalDisplayLimit((prev) => prev + 50)}
                    className="px-4 py-1.5 text-xs font-semibold text-[var(--rzp-primary)] bg-purple-50 hover:bg-purple-100 rounded-md border border-purple-200 transition-colors"
                  >
                    Load More ({modalSignals.length - modalDisplayLimit} remaining)
                  </button>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-gray-200 bg-[var(--rzp-surface-subtle)] flex items-center justify-between text-xs shrink-0">
              <span className="text-[11px] text-[var(--rzp-text-muted)]">
                Showing {Math.min(modalSignals.length, modalDisplayLimit)} of {modalSignals.length.toLocaleString()} matching items ({activeModalGroup.signals.length.toLocaleString()} total friction signals in category)
              </span>
              <button
                type="button"
                onClick={closeModal}
                className="px-3 py-1 bg-white border border-[var(--rzp-border)] hover:bg-gray-50 rounded-md text-xs font-medium text-gray-700 shadow-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
