import type { Recommendation, Product } from '../../../types';

export type RecommendationSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM';

export interface PersonaMapping {
  name: string;
  code: string;
  icon: string;
  description: string;
}

export interface RecommendationFieldDetails {
  productName: string;
  field: string;
  fieldLabel: string;
  beforeValue: string;
  buyerRequirement: string;
  simulationResult: string;
  actionSummary: string;
  afterValue: string;
  auditEventType: string;
  actionType: string;
}

export const formatPriceInINR = (priceMinor: number): string => {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(priceMinor / 100);
};

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
      { name: 'All Buyer Personas', code: 'ALL', icon: '👥', description: 'Stockout blocks candidate conversions' }
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

export const getRecommendationFieldDetails = (
  rec: Recommendation,
  product?: Product
): RecommendationFieldDetails => {
  const fType = (rec.action_data?.friction_type || rec.type || '').toUpperCase();
  const prodName = product ? product.name : (rec.title || 'Target Product');

  if (fType.includes('DELIVERY') || rec.type.includes('DELIVERY')) {
    // Prefer the semantic description captured at simulation time (not live product field,
    // which may already show the target value making BEFORE == AFTER appear).
    const currentVal = rec.action_data?.before_state_description
      ?? (product?.metadata?.delivery_days !== undefined
          ? `${product.metadata.delivery_days} days`
          : 'Unknown / Missing');
    const targetVal = rec.action_data?.new_delivery_days !== undefined
      ? `${rec.action_data.new_delivery_days} days`
      : '2 days';

    return {
      productName: prodName,
      field: 'delivery_days',
      fieldLabel: 'Delivery Speed SLA',
      beforeValue: currentVal,
      buyerRequirement: '<= 2 days SLA (Speed & Deadline Personas)',
      simulationResult: rec.reason || 'Delivery SLA could not be verified / friction detected',
      actionSummary: rec.action_data?.suggested_change || `Set delivery_days = ${targetVal}`,
      afterValue: targetVal,
      auditEventType: 'RECOMMENDATION_APPLIED',
      actionType: 'UPDATE_DELIVERY_DAYS'
    };
  }

  if (fType.includes('PRICE') || rec.type.includes('PRICE')) {
    const currentPrice = product ? formatPriceInINR(product.price) : 'Current Catalogue Price';
    const newPrice = rec.action_data?.new_price !== undefined
      ? formatPriceInINR(rec.action_data.new_price)
      : 'Discounted Price';

    return {
      productName: prodName,
      field: 'price',
      fieldLabel: 'Product Price',
      beforeValue: currentPrice,
      buyerRequirement: rec.action_data?.new_price ? `<= ${newPrice} (Within persona budget ceiling)` : 'Within persona budget ceiling',
      simulationResult: rec.reason || 'Price exceeded buyer budget threshold in simulation',
      actionSummary: rec.action_data?.suggested_change || `Adjust price to ${newPrice}`,
      afterValue: newPrice,
      auditEventType: 'RECOMMENDATION_APPLIED',
      actionType: 'UPDATE_PRICE'
    };
  }

  if (fType.includes('RETURN') || rec.type.includes('RETURN')) {
    // Prefer semantic description captured at simulation time
    const currentReturn = rec.action_data?.before_state_description
      ?? (product?.metadata?.return_days !== undefined
          ? `${product.metadata.return_days} days`
          : 'Unknown / Not specified');
    const targetReturn = rec.action_data?.new_return_days !== undefined
      ? `${rec.action_data.new_return_days} days`
      : '14 days';

    return {
      productName: prodName,
      field: 'return_days',
      fieldLabel: 'Return Policy Window',
      beforeValue: currentReturn,
      buyerRequirement: '>= 14 days verified return window (Quality Personas)',
      simulationResult: rec.reason || 'Return policy unspecified / failed warranty constraint',
      actionSummary: rec.action_data?.suggested_change || `Set return_days = ${targetReturn}`,
      afterValue: targetReturn,
      auditEventType: 'RECOMMENDATION_APPLIED',
      actionType: 'UPDATE_RETURN_DAYS'
    };
  }

  if (fType.includes('INVENTORY') || rec.type.includes('INVENTORY')) {
    const currentStock = product?.inventory?.available_quantity !== undefined
      ? `${product.inventory.available_quantity} in stock`
      : '0 in stock (Stockout)';
    const newStock = rec.action_data?.new_inventory_count !== undefined
      ? `${rec.action_data.new_inventory_count} units`
      : '50 units';

    return {
      productName: prodName,
      field: 'available_quantity',
      fieldLabel: 'Inventory Stock',
      beforeValue: currentStock,
      buyerRequirement: 'Available stock required for buyer candidate checkout',
      simulationResult: rec.reason || 'Product stockout caused 100% persona constraint failure',
      actionSummary: rec.action_data?.suggested_change || `Restock inventory to ${newStock}`,
      afterValue: newStock,
      auditEventType: 'RECOMMENDATION_APPLIED',
      actionType: 'UPDATE_INVENTORY'
    };
  }

  // Fallback
  return {
    productName: prodName,
    field: 'metadata',
    fieldLabel: 'Product Metadata & Attributes',
    beforeValue: 'Incomplete attribute set',
    buyerRequirement: 'Structured specifications required for matching',
    simulationResult: rec.reason || 'Constraint checks penalised missing specifications',
    actionSummary: rec.action_data?.suggested_change || rec.title,
    afterValue: 'Enriched specification set',
    auditEventType: 'RECOMMENDATION_APPLIED',
    actionType: 'ENRICH_METADATA'
  };
};
