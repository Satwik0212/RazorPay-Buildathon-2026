import React from 'react';
import { Search, ArrowUpDown } from 'lucide-react';

export interface RecommendationFilterState {
  search: string;
  status: 'ALL' | 'PROPOSED' | 'APPLIED' | 'REJECTED';
  category: string;
  severity: string;
  sortBy: 'impact_desc' | 'confidence_desc' | 'frictions_desc' | 'newest';
}

interface RecommendationFiltersProps {
  filters: RecommendationFilterState;
  onChange: (filters: RecommendationFilterState) => void;
  counts: {
    all: number;
    proposed: number;
    applied: number;
    rejected: number;
  };
  categories: string[];
}

export const RecommendationFilters: React.FC<RecommendationFiltersProps> = ({
  filters,
  onChange,
  counts,
  categories
}) => {
  const handleStatusChange = (status: RecommendationFilterState['status']) => {
    onChange({ ...filters, status });
  };

  return (
    <div className="bg-white rounded-xl border border-[var(--rzp-border)] p-4 shadow-sm space-y-3.5">
      {/* Top Row: Status Tabs & Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Status Segmented Control */}
        <div className="flex items-center p-1 bg-gray-100/80 rounded-lg border border-gray-200 text-xs font-semibold overflow-x-auto">
          <button
            type="button"
            onClick={() => handleStatusChange('ALL')}
            className={`px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${
              filters.status === 'ALL'
                ? 'bg-white text-[var(--rzp-text)] shadow-xs font-bold'
                : 'text-[var(--rzp-text-muted)] hover:text-[var(--rzp-text)]'
            }`}
          >
            All <span className="ml-1 text-[10px] font-mono px-1.5 py-0.2 bg-gray-200 rounded-full">{counts.all}</span>
          </button>
          <button
            type="button"
            onClick={() => handleStatusChange('PROPOSED')}
            className={`px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${
              filters.status === 'PROPOSED'
                ? 'bg-[var(--rzp-warning-soft)] text-[var(--rzp-warning)] border border-[var(--rzp-warning)] shadow-xs font-bold'
                : 'text-[var(--rzp-text-muted)] hover:text-[var(--rzp-warning)]'
            }`}
          >
            Action Required <span className="ml-1 text-[10px] font-mono px-1.5 py-0.2 bg-amber-100 text-amber-800 rounded-full font-bold">{counts.proposed}</span>
          </button>
          <button
            type="button"
            onClick={() => handleStatusChange('APPLIED')}
            className={`px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${
              filters.status === 'APPLIED'
                ? 'bg-[var(--rzp-success-soft)] text-[var(--rzp-success)] border border-[var(--rzp-success)] shadow-xs font-bold'
                : 'text-[var(--rzp-text-muted)] hover:text-[var(--rzp-success)]'
            }`}
          >
            Applied <span className="ml-1 text-[10px] font-mono px-1.5 py-0.2 bg-green-100 text-green-800 rounded-full font-bold">{counts.applied}</span>
          </button>
          <button
            type="button"
            onClick={() => handleStatusChange('REJECTED')}
            className={`px-3 py-1.5 rounded-md transition-all whitespace-nowrap ${
              filters.status === 'REJECTED'
                ? 'bg-gray-200 text-gray-800 shadow-xs font-bold'
                : 'text-[var(--rzp-text-muted)] hover:text-[var(--rzp-text)]'
            }`}
          >
            Rejected <span className="ml-1 text-[10px] font-mono px-1.5 py-0.2 bg-gray-300 text-gray-700 rounded-full">{counts.rejected}</span>
          </button>
        </div>

        {/* Search Box */}
        <div className="w-full md:w-72 relative">
          <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search recommendations or products..."
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            className="w-full h-9 pl-9 pr-3 text-xs bg-[var(--rzp-surface-subtle)] border border-[var(--rzp-border-strong)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--rzp-primary)] focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Bottom Row: Detailed Dropdown Filters & Sorting */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[var(--rzp-border)] text-xs">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Category Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] font-medium text-[var(--rzp-text-muted)]">Category:</span>
            <select
              value={filters.category}
              onChange={(e) => onChange({ ...filters, category: e.target.value })}
              className="h-8 px-2.5 text-xs bg-white border border-[var(--rzp-border-strong)] rounded-md focus:outline-none focus:ring-1 focus:ring-[var(--rzp-primary)]"
            >
              <option value="ALL">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] font-medium text-[var(--rzp-text-muted)]">Severity:</span>
            <select
              value={filters.severity}
              onChange={(e) => onChange({ ...filters, severity: e.target.value })}
              className="h-8 px-2.5 text-xs bg-white border border-[var(--rzp-border-strong)] rounded-md focus:outline-none focus:ring-1 focus:ring-[var(--rzp-primary)]"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical Blockers</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
            </select>
          </div>
        </div>

        {/* Sort Selector */}
        <div className="flex items-center space-x-1.5">
          <ArrowUpDown className="h-3.5 w-3.5 text-gray-400" />
          <span className="text-[11px] font-medium text-[var(--rzp-text-muted)]">Sort By:</span>
          <select
            value={filters.sortBy}
            onChange={(e) => onChange({ ...filters, sortBy: e.target.value as any })}
            className="h-8 px-2.5 text-xs bg-white border border-[var(--rzp-border-strong)] rounded-md font-medium text-[var(--rzp-text)] focus:outline-none focus:ring-1 focus:ring-[var(--rzp-primary)]"
          >
            <option value="impact_desc">Highest Expected Impact</option>
            <option value="confidence_desc">Highest AI Confidence</option>
            <option value="frictions_desc">Most Friction Events</option>
            <option value="newest">Recently Discovered</option>
          </select>
        </div>
      </div>
    </div>
  );
};
