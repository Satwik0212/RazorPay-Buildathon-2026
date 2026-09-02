import type { Recommendation, Product } from '../../../types';

export type RecommendationSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM';

export interface PersonaMapping {
  name: string;
  code: string;
  icon: string;
  description: string;
}

export const getRecommendationCategory = (rec: Recommendation): {
  category: string;
  colorClass: string;
  bgClass: string;
  borderClass: string;
  frictionType: string;
} => {
  const type = (rec.type || '').toUpperCase();
  const fType = (rec.action_data?.friction_type || '').toUpperCase();

  if (type.includes('INVENTORY') || fType.includes('INVENTORY')) {
    return {
      category: 'Inventory Restoration',
      colorClass: 'text-red-700',
      bgClass: 'bg-red-50',
      borderClass: 'border-red-200',
      frictionType: 'INVENTORY_ISSUE'
    };
  }
  if (type.includes('PRICE') || fType.includes('PRICE')) {
    return {
      category: 'Price Competitiveness',
      colorClass: 'text-blue-700',
      bgClass: 'bg-blue-50',
      borderClass: 'border-blue-200',
      frictionType: 'PRICE_MISMATCH'
    };
  }
  if (type.includes('DELIVERY') || fType.includes('DELIVERY')) {
    return {
      category: 'Delivery Speed SLA',
      colorClass: 'text-purple-700',
      bgClass: 'bg-purple-50',
      borderClass: 'border-purple-200',
      frictionType: 'DELIVERY_UNCLEAR'
    };
  }
  if (type.includes('RETURN') || fType.includes('RETURN')) {
    return {
      category: 'Return & Refund Policy',
      colorClass: 'text-emerald-700',
      bgClass: 'bg-emerald-50',
      borderClass: 'border-emerald-200',
      frictionType: 'RETURN_UNCLEAR'
    };
  }
  if (type.includes('CATALOGUE') || type.includes('ENRICHMENT') || fType.includes('PRODUCT_INFORMATION')) {
    return {
      category: 'Catalogue Enrichment',
      colorClass: 'text-amber-700',
      bgClass: 'bg-amber-50',
      borderClass: 'border-amber-200',
      frictionType: 'INSUFFICIENT_PRODUCT_INFORMATION'
    };
  }

  return {
    category: rec.type || 'Catalogue Optimization',
    colorClass: 'text-gray-700',
    bgClass: 'bg-gray-50',
    borderClass: 'border-gray-200',
    frictionType: fType || 'GENERAL_FRICTION'
  };
};

export const getRecommendationSeverity = (rec: Recommendation, product?: Product): {
  severity: RecommendationSeverity;
  label: string;
  badgeClass: string;
} => {
  const type = (rec.type || '').toUpperCase();
  const fType = (rec.action_data?.friction_type || '').toUpperCase();

  if (type.includes('INVENTORY') || fType.includes('INVENTORY') || (product && product.inventory && product.inventory.available_quantity <= 0)) {
    return {
      severity: 'CRITICAL',
      label: 'Critical Blocker',
      badgeClass: 'bg-red-100 text-red-800 border-red-300'
    };
  }

  if (rec.expected_simulated_impact >= 0.25 || type.includes('PRICE') || fType.includes('PRICE')) {
    return {
      severity: 'HIGH',
      label: 'High Priority',
      badgeClass: 'bg-amber-100 text-amber-800 border-amber-300'
    };
  }

  if (rec.expected_simulated_impact >= 0.20 || type.includes('DELIVERY')) {
    return {
      severity: 'HIGH',
      label: 'High Priority',
      badgeClass: 'bg-purple-100 text-purple-800 border-purple-300'
    };
  }

  return {
    severity: 'MEDIUM',
    label: 'Medium Priority',
    badgeClass: 'bg-blue-100 text-blue-800 border-blue-300'
  };
};

export const getTargetPersonas = (rec: Recommendation): PersonaMapping[] => {
  const fType = (rec.action_data?.friction_type || rec.type || '').toUpperCase();
  const reason = (rec.reason || '').toLowerCase();

  if (fType.includes('INVENTORY')) {
    return [
      { name: 'All Buyer Personas', code: 'ALL', icon: '👥', description: 'Stockout blocks 100% of candidate conversions' }
    ];
  }
  if (fType.includes('PRICE') || reason.includes('budget') || reason.includes('price')) {
    return [
      { name: 'Budget-Conscious Buyers', code: 'BUDGET', icon: '💰', description: 'Hard price ceiling and strict discount preference' }
    ];
  }
  if (fType.includes('DELIVERY') || reason.includes('speed') || reason.includes('delivery')) {
    return [
      { name: 'Speed-Focused Buyers', code: 'SPEED', icon: '⚡', description: 'Strict SLA deadline and express delivery requirement' }
    ];
  }
  if (fType.includes('RETURN') || reason.includes('quality') || reason.includes('return') || reason.includes('refund')) {
    return [
      { name: 'Quality & Warranty Buyers', code: 'QUALITY', icon: '⭐', description: 'Requires verified return guarantee and warranty' }
    ];
  }
  if (fType.includes('INFORMATION') || reason.includes('feature') || reason.includes('spec')) {
    return [
      { name: 'Feature & Tech Buyers', code: 'FEATURE', icon: '🔍', description: 'Requires structured specifications and deep attributes' }
    ];
  }

  return [
    { name: 'Balanced Consumers', code: 'BALANCED', icon: '⚖️', description: 'Evaluates overall value equation across all attributes' }
  ];
};
