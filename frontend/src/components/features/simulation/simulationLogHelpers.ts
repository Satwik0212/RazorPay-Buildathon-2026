import type { SimulationResultItem, Product, SimulationRanking } from '../../../types';

export interface PersonaMeta {
  baseName: string;
  variantCode: string;
  displayName: string;
  variantLabel: string;
  icon: string;
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
}

export interface IntentSummary {
  maxBudget: number | null;
  maxBudgetText: string;
  requirements: string[];
  deliveryDeadlineDays: number | null;
  deliveryDeadlineToText: string;
  preferences: string[];
  category: string | null;
}

export interface ConstraintCheck {
  id: string;
  name: string;
  status: 'PASSED' | 'FAILED' | 'UNCONSTRAINED';
  summary: string;
  evidence: string;
}

export interface ScoreComponent {
  key: string;
  label: string;
  score: number; // 0.0 - 1.0
  weight: number; // 0.0 - 1.0
  weightedScore: number;
  evidence: string;
}

export interface PositiveSignal {
  title: string;
  description: string;
  category: 'BUDGET' | 'INVENTORY' | 'DELIVERY' | 'QUALITY' | 'RETURNS' | 'METADATA' | 'AFFINITY';
}

export interface FrictionSignal {
  type: 'HARD_BLOCKER' | 'SOFT_PENALTY';
  reason: string;
  title: string;
  description: string;
  affectedProductName?: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
}

export const formatPrice = (priceInMinor?: number | null): string => {
  if (
    priceInMinor === undefined ||
    priceInMinor === null ||
    typeof priceInMinor !== 'number' ||
    isNaN(priceInMinor) ||
    !isFinite(priceInMinor)
  ) {
    return '₹0';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(priceInMinor / 100);
};

export const getPersonaMeta = (personaName: string): PersonaMeta => {
  const parts = (personaName || '').split(':');
  const base = (parts[0] || 'BALANCED').toUpperCase();
  const variant = parts[1] || '';

  const personaMap: Record<string, { displayName: string; icon: string; badgeBg: string; badgeText: string; badgeBorder: string }> = {
    BUDGET: {
      displayName: 'Budget Maximizer',
      icon: '💰',
      badgeBg: 'bg-emerald-50',
      badgeText: 'text-emerald-700',
      badgeBorder: 'border-emerald-200',
    },
    SPEED: {
      displayName: 'Speed Priority',
      icon: '⚡',
      badgeBg: 'bg-amber-50',
      badgeText: 'text-amber-700',
      badgeBorder: 'border-amber-200',
    },
    QUALITY: {
      displayName: 'Quality Focused',
      icon: '⭐',
      badgeBg: 'bg-blue-50',
      badgeText: 'text-blue-700',
      badgeBorder: 'border-blue-200',
    },
    FEATURE: {
      displayName: 'Feature Researcher',
      icon: '🔍',
      badgeBg: 'bg-purple-50',
      badgeText: 'text-purple-700',
      badgeBorder: 'border-purple-200',
    },
    BALANCED: {
      displayName: 'Balanced Shopper',
      icon: '⚖️',
      badgeBg: 'bg-indigo-50',
      badgeText: 'text-indigo-700',
      badgeBorder: 'border-indigo-200',
    },
  };

  const meta = personaMap[base] || {
    displayName: base,
    icon: '🤖',
    badgeBg: 'bg-gray-50',
    badgeText: 'text-gray-700',
    badgeBorder: 'border-gray-200',
  };

  // Humanize variant
  const variantLabel = variant
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase()) || 'Default Scenario';

  return {
    baseName: base,
    variantCode: variant,
    displayName: meta.displayName,
    variantLabel,
    icon: meta.icon,
    badgeBg: meta.badgeBg,
    badgeText: meta.badgeText,
    badgeBorder: meta.badgeBorder,
  };
};

export const extractIntentSummary = (item: SimulationResultItem): IntentSummary => {
  const intent = item.intent || {};
  let maxBudget = intent.max_budget ?? null;
  let requirements: string[] = intent.requirements || [];
  let deadlineDays = intent.delivery_deadline_days ?? null;
  const category = intent.category ?? null;
  const preferences: string[] = intent.preferences || [];

  // If intent was not directly on item, infer from scenario variant label
  if (maxBudget === null || maxBudget === undefined) {
    const pName = (item.persona_name || '').toLowerCase();
    if (pName.includes('budget_tight')) maxBudget = 300000;
    else if (pName.includes('budget_moderate')) maxBudget = 600000;
    else if (pName.includes('budget_mid_quality')) { maxBudget = 800000; requirements = ['warranty']; }
    else if (pName.includes('budget_with_deadline')) { maxBudget = 500000; deadlineDays = 3; }
    else if (pName.includes('budget_high_value')) maxBudget = 1000000;
    else if (pName.includes('feature_budget_low')) maxBudget = 500000;
    else if (pName.includes('feature_budget_mid')) maxBudget = 1500000;
    else if (pName.includes('feature_budget_high')) { maxBudget = 3000000; deadlineDays = 5; }
    else if (pName.includes('feature_deadline')) { maxBudget = 2000000; deadlineDays = 3; }
    else if (pName.includes('feature_premium')) { maxBudget = 5000000; requirements = ['warranty']; }
    else if (pName.includes('speed_same_day')) { maxBudget = 2000000; deadlineDays = 1; }
    else if (pName.includes('speed_two_day')) { maxBudget = 1500000; deadlineDays = 2; }
    else if (pName.includes('speed_three_day')) { maxBudget = 2000000; deadlineDays = 3; }
    else if (pName.includes('speed_premium')) { maxBudget = 3000000; requirements = ['warranty']; deadlineDays = 1; }
    else if (pName.includes('speed_budget')) { maxBudget = 800000; deadlineDays = 2; }
    else if (pName.includes('quality_essentials')) maxBudget = 1500000;
    else if (pName.includes('quality_premium')) { maxBudget = 3000000; requirements = ['warranty']; }
    else if (pName.includes('quality_returns')) maxBudget = 2000000;
    else if (pName.includes('quality_complete')) { maxBudget = 4000000; requirements = ['warranty']; }
    else if (pName.includes('quality_balanced')) { maxBudget = 2500000; deadlineDays = 5; }
    else if (pName.includes('balanced_standard')) maxBudget = 1000000;
    else if (pName.includes('balanced_offers')) { maxBudget = 1500000; deadlineDays = 7; }
    else if (pName.includes('balanced_quality')) { maxBudget = 2000000; requirements = ['warranty']; }
    else if (pName.includes('balanced_speed')) { maxBudget = 1200000; deadlineDays = 3; }
    else if (pName.includes('balanced_premium')) maxBudget = 3000000;
  }

  return {
    maxBudget,
    maxBudgetText: maxBudget !== null ? `Under ${formatPrice(maxBudget)}` : 'No strict budget ceiling',
    requirements,
    deliveryDeadlineDays: deadlineDays,
    deliveryDeadlineToText: deadlineDays !== null ? `Must arrive within ≤ ${deadlineDays} day${deadlineDays === 1 ? '' : 's'}` : 'Flexible delivery timeline',
    preferences,
    category,
  };
};

export const evaluateHardConstraints = (
  item: SimulationResultItem,
  intent: IntentSummary,
  selectedProduct?: Product | null
): ConstraintCheck[] => {
  const checks: ConstraintCheck[] = [];
  const hardFrictions = (item.frictions || []).filter(
    (f) =>
      f.type === 'HARD_CONSTRAINT' ||
      (f.reason &&
        [
          'PRICE_MISMATCH',
          'INVENTORY_ISSUE',
          'MISSING_FEATURE',
          'DELIVERY_TOO_SLOW',
          'DELIVERY_UNKNOWN',
        ].includes(f.reason))
  );
  const isSatisfied = Boolean(item.constraints_satisfied && item.selected_product_id);

  // 1. Budget Cap
  if (intent.maxBudget !== null) {
    const hasPriceMismatch = hardFrictions.some((f) => f.reason === 'PRICE_MISMATCH');
    if (selectedProduct && selectedProduct.price !== undefined && selectedProduct.price !== null) {
      const priceFits = selectedProduct.price <= intent.maxBudget;
      checks.push({
        id: 'budget_cap',
        name: 'Budget Ceiling',
        status: priceFits ? 'PASSED' : 'FAILED',
        summary: priceFits
          ? `Within Budget (${formatPrice(selectedProduct.price)} ≤ ${formatPrice(intent.maxBudget)})`
          : `Exceeds Budget (${formatPrice(selectedProduct.price)} > ${formatPrice(intent.maxBudget)})`,
        evidence: `Max budget constraint: ${formatPrice(intent.maxBudget)}. Selected item price: ${formatPrice(selectedProduct.price)}.`,
      });
    } else if (isSatisfied && !hasPriceMismatch) {
      checks.push({
        id: 'budget_cap',
        name: 'Budget Ceiling',
        status: 'PASSED',
        summary: `Within Budget Constraint (≤ ${formatPrice(intent.maxBudget)})`,
        evidence: `Max budget ceiling: ${formatPrice(intent.maxBudget)}. Satisfied by candidate selection.`,
      });
    } else {
      checks.push({
        id: 'budget_cap',
        name: 'Budget Ceiling',
        status: hasPriceMismatch ? 'FAILED' : 'PASSED',
        summary: hasPriceMismatch
          ? `Disqualified: Catalogue items exceed budget cap of ${formatPrice(intent.maxBudget)}`
          : `Budget cap set at ${formatPrice(intent.maxBudget)}`,
        evidence: `Evaluated budget limit of ${formatPrice(intent.maxBudget)}.`,
      });
    }
  } else {
    checks.push({
      id: 'budget_cap',
      name: 'Budget Ceiling',
      status: 'UNCONSTRAINED',
      summary: 'No strict maximum budget constraint specified',
      evidence: 'Buyer evaluated catalogue with unconstrained budget.',
    });
  }

  // 2. Active Stock & Inventory
  const hasInventoryFriction = hardFrictions.some((f) => f.reason === 'INVENTORY_ISSUE');
  if (selectedProduct) {
    const inStock =
      selectedProduct.is_active &&
      (selectedProduct.inventory?.available_quantity === undefined ||
        selectedProduct.inventory.available_quantity > 0);
    checks.push({
      id: 'inventory_status',
      name: 'Catalogue Stock Availability',
      status: inStock ? 'PASSED' : 'FAILED',
      summary: inStock
        ? 'Verified active and available in stock'
        : 'Product is inactive or stock is depleted',
      evidence: `Product active status: ${selectedProduct.is_active}. Available stock: ${selectedProduct.inventory?.available_quantity ?? 'Available'}.`,
    });
  } else if (isSatisfied && !hasInventoryFriction) {
    checks.push({
      id: 'inventory_status',
      name: 'Catalogue Stock Availability',
      status: 'PASSED',
      summary: 'Verified active and available in stock',
      evidence: 'Selected candidate verified active with available inventory.',
    });
  } else {
    checks.push({
      id: 'inventory_status',
      name: 'Catalogue Stock Availability',
      status: hasInventoryFriction ? 'FAILED' : 'PASSED',
      summary: hasInventoryFriction
        ? 'Disqualified: Active stock unavailable'
        : 'Active inventory verified across candidates',
      evidence: 'Requires active catalogue state and positive inventory quantity.',
    });
  }

  // 3. Required Features / Specifications
  if (intent.requirements && intent.requirements.length > 0) {
    const reqNames = intent.requirements.join(', ');
    const hasMissingFeature = hardFrictions.some((f) => f.reason === 'MISSING_FEATURE');
    checks.push({
      id: 'mandatory_features',
      name: 'Mandatory Specification Requirements',
      status: isSatisfied && !hasMissingFeature ? 'PASSED' : 'FAILED',
      summary:
        isSatisfied && !hasMissingFeature
          ? `Confirmed required specifications: ${reqNames}`
          : `Missing required specification: ${reqNames}`,
      evidence: `Intent required: ${reqNames}. Verified in product specifications.`,
    });
  } else {
    checks.push({
      id: 'mandatory_features',
      name: 'Mandatory Specification Requirements',
      status: 'UNCONSTRAINED',
      summary: 'No mandatory blocking feature requirements',
      evidence: 'No disqualifying feature requirements in scenario intent.',
    });
  }

  // 4. Delivery Deadline
  if (intent.deliveryDeadlineDays !== null) {
    const hasDeliverySlow = hardFrictions.some(
      (f) => f.reason === 'DELIVERY_TOO_SLOW' || f.reason === 'DELIVERY_UNKNOWN'
    );
    if (
      selectedProduct?.metadata?.delivery_days !== undefined &&
      selectedProduct.metadata.delivery_days !== null
    ) {
      const deliveryDays = Number(selectedProduct.metadata.delivery_days);
      const passesDeadline = deliveryDays <= intent.deliveryDeadlineDays;
      checks.push({
        id: 'delivery_deadline',
        name: 'Delivery Speed Deadline',
        status: passesDeadline ? 'PASSED' : 'FAILED',
        summary: passesDeadline
          ? `Meets delivery promise (${deliveryDays} day${deliveryDays === 1 ? '' : 's'} ≤ ${intent.deliveryDeadlineDays} days)`
          : `Fails delivery promise (${deliveryDays} days > ${intent.deliveryDeadlineDays} days)`,
        evidence: `Required arrival within ≤ ${intent.deliveryDeadlineDays} days. Product delivery time: ${deliveryDays} days.`,
      });
    } else if (isSatisfied && !hasDeliverySlow) {
      checks.push({
        id: 'delivery_deadline',
        name: 'Delivery Speed Deadline',
        status: 'PASSED',
        summary: `Meets delivery promise (≤ ${intent.deliveryDeadlineDays} day${intent.deliveryDeadlineDays === 1 ? '' : 's'})`,
        evidence: `Required arrival within ≤ ${intent.deliveryDeadlineDays} days. Delivery timeline verified by engine.`,
      });
    } else {
      checks.push({
        id: 'delivery_deadline',
        name: 'Delivery Speed Deadline',
        status: hasDeliverySlow ? 'FAILED' : 'PASSED',
        summary: hasDeliverySlow
          ? `Disqualified: Estimated delivery exceeds deadline (≤ ${intent.deliveryDeadlineDays} days)`
          : `Delivery deadline requirement: ≤ ${intent.deliveryDeadlineDays} days`,
        evidence: `Strict delivery timeline filter for ${intent.deliveryDeadlineDays} day deadline.`,
      });
    }
  } else {
    checks.push({
      id: 'delivery_deadline',
      name: 'Delivery Speed Deadline',
      status: 'UNCONSTRAINED',
      summary: 'Standard delivery acceptable (no urgent deadline)',
      evidence: 'No hard delivery deadline filter applied in this scenario.',
    });
  }

  return checks;
};

export const calculateScoreComponents = (
  item: SimulationResultItem,
  intent: IntentSummary,
  product?: Product | null
): ScoreComponent[] => {
  if (!product) return [];

  const metadata = product.metadata || {};
  const price = product.price || 0;
  const pName = (item.persona_name || '').split(':')[0].toUpperCase();

  // Resolve Persona Weights
  const weightsMap: Record<string, Record<string, number>> = {
    BUDGET: { price: 0.50, offers: 0.25, delivery: 0.10, quality: 0.10, returns: 0.05, metadata: 0.00 },
    SPEED: { delivery: 0.55, metadata: 0.20, quality: 0.15, price: 0.10, returns: 0.00, offers: 0.00 },
    QUALITY: { quality: 0.50, metadata: 0.20, returns: 0.15, delivery: 0.10, price: 0.05, offers: 0.00 },
    FEATURE: { metadata: 0.50, quality: 0.25, price: 0.15, delivery: 0.10, returns: 0.00, offers: 0.00 },
    BALANCED: { price: 0.25, quality: 0.25, delivery: 0.20, returns: 0.15, offers: 0.10, metadata: 0.05 },
  };

  const weights = item.persona_weights || weightsMap[pName] || weightsMap.BALANCED;

  // 1. Price Score
  let priceScore = 0.5;
  const maxBudget = intent.maxBudget;
  if (maxBudget && maxBudget > 0) {
    if (price <= maxBudget) {
      const savingsRatio = (maxBudget - price) / maxBudget;
      priceScore = (weights.price || 0) >= 0.3 ? 0.5 + 0.5 * Math.min(Math.max(savingsRatio, 0), 1) : 0.8 + 0.2 * Math.min(Math.max(savingsRatio, 0), 1);
    } else {
      priceScore = Math.max(0, 0.5 - (price - maxBudget) / maxBudget);
    }
  } else {
    priceScore = Math.max(0.1, 1.0 - price / 2000000.0);
  }

  // 2. Delivery Speed Score
  let deliveryScore = 0.3;
  const deliveryDays = metadata.delivery_days;
  if (deliveryDays !== undefined && deliveryDays !== null) {
    const days = Number(deliveryDays);
    if (days <= 1) deliveryScore = 1.0;
    else if (days <= 2) deliveryScore = 0.90;
    else if (days <= 3) deliveryScore = 0.75;
    else if (days <= 5) deliveryScore = 0.55;
    else if (days <= 7) deliveryScore = 0.40;
    else deliveryScore = Math.max(0.1, 1.0 - days / 14.0);
  }

  // 3. Quality & Brand Score
  const rating = metadata.rating !== undefined && metadata.rating !== null ? Number(metadata.rating) : null;
  const ratingScore = rating !== null ? Math.min(Math.max(rating / 5.0, 0), 1.0) * 0.7 : 0.35;
  const hasWarranty = metadata.warranty ? 0.2 : metadata.warranty === undefined ? 0.05 : 0.0;
  const isPremium = metadata.high_quality || metadata.premium ? 0.1 : 0.0;
  const qualityScore = Math.min(1.0, ratingScore + hasWarranty + isPremium);

  // 4. Return Policy Score
  let returnScore = 0.2;
  const returnDays = metadata.return_days;
  if (returnDays !== undefined && returnDays !== null) {
    const rDays = Number(returnDays);
    if (rDays >= 30) returnScore = 1.0;
    else if (rDays >= 14) returnScore = 0.85;
    else if (rDays >= 7) returnScore = 0.60;
    else returnScore = 0.10;
  } else if (metadata.return_policy) {
    returnScore = 0.50;
  }

  // 5. Offers & Discounts
  let offerScore = 0.1;
  const discountPercent = Number(metadata.discount_percent || 0);
  if (discountPercent > 0) {
    offerScore = Math.min(1.0, 0.4 + (discountPercent / 50.0) * 0.6);
  } else if (metadata.has_offer || metadata.has_discount) {
    offerScore = 0.75;
  }

  // 6. Metadata Richness
  const descLength = (product.description || '').length;
  const descScore = Math.min(0.4, (descLength / 500.0) * 0.4);
  const metaCount = Object.keys(metadata).length;
  const metaScore = Math.min(0.6, (metaCount / 15.0) * 0.6);
  const metadataScore = Math.min(1.0, descScore + metaScore);

  const components: ScoreComponent[] = [
    {
      key: 'price',
      label: 'Price Fit & Budget Savings',
      score: Number(priceScore.toFixed(2)),
      weight: weights.price || 0,
      weightedScore: Number((priceScore * (weights.price || 0)).toFixed(3)),
      evidence: maxBudget ? `${formatPrice(price)} vs ${formatPrice(maxBudget)} budget (${price <= maxBudget ? 'Within budget' : 'Over budget'})` : `${formatPrice(price)} standard pricing scale`,
    },
    {
      key: 'delivery',
      label: 'Delivery Speed & Promise',
      score: Number(deliveryScore.toFixed(2)),
      weight: weights.delivery || 0,
      weightedScore: Number((deliveryScore * (weights.delivery || 0)).toFixed(3)),
      evidence: deliveryDays !== undefined ? `${deliveryDays} day estimated delivery` : 'Delivery timeline unverified (neutral default applied)',
    },
    {
      key: 'quality',
      label: 'Quality, Rating & Warranty',
      score: Number(qualityScore.toFixed(2)),
      weight: weights.quality || 0,
      weightedScore: Number((qualityScore * (weights.quality || 0)).toFixed(3)),
      evidence: `${rating !== null ? `${rating}/5 stars` : 'Standard default rating'}${metadata.warranty ? ' • Warranty covered' : ''}${isPremium ? ' • Premium tier' : ''}`,
    },
    {
      key: 'returns',
      label: 'Return Window Terms',
      score: Number(returnScore.toFixed(2)),
      weight: weights.returns || 0,
      weightedScore: Number((returnScore * (weights.returns || 0)).toFixed(3)),
      evidence: returnDays !== undefined ? `${returnDays}-day return window` : metadata.return_policy ? 'Standard return policy documented' : 'No return terms specified in metadata',
    },
    {
      key: 'offers',
      label: 'Discounts & Promotional Offers',
      score: Number(offerScore.toFixed(2)),
      weight: weights.offers || 0,
      weightedScore: Number((offerScore * (weights.offers || 0)).toFixed(3)),
      evidence: discountPercent > 0 ? `${discountPercent}% active discount` : metadata.has_offer ? 'Promotional offer active' : 'Standard listed price (no active promotion)',
    },
    {
      key: 'metadata',
      label: 'Specification & Detail Depth',
      score: Number(metadataScore.toFixed(2)),
      weight: weights.metadata || 0,
      weightedScore: Number((metadataScore * (weights.metadata || 0)).toFixed(3)),
      evidence: `${metaCount} specification fields • ${descLength} character product description`,
    },
  ];

  return components.filter((c) => c.weight > 0 || c.score > 0.4);
};

export const getPositiveSignals = (
  item: SimulationResultItem,
  intent: IntentSummary,
  product?: Product | null
): PositiveSignal[] => {
  const signals: PositiveSignal[] = [];
  const isSatisfied = Boolean(item.constraints_satisfied && item.selected_product_id);
  if (!isSatisfied) return signals;

  if (product) {
    const metadata = product.metadata || {};

    // Inventory
    if (product.is_active) {
      const qty = product.inventory?.available_quantity;
      signals.push({
        title: 'Active In-Stock Inventory',
        description:
          qty !== undefined && qty !== null
            ? `Verified active status with ${qty} units in stock`
            : 'Catalogue item is active and ready for simulated checkout',
        category: 'INVENTORY',
      });
    }

    // Budget
    if (
      intent.maxBudget &&
      product.price !== undefined &&
      product.price !== null &&
      product.price <= intent.maxBudget
    ) {
      const savings = intent.maxBudget - product.price;
      signals.push({
        title: 'Price Within Target Budget',
        description: `${formatPrice(product.price)} is within the ${formatPrice(intent.maxBudget)} ceiling${savings > 0 ? ` (${formatPrice(savings)} headroom)` : ''}`,
        category: 'BUDGET',
      });
    }

    // Delivery
    if (
      metadata.delivery_days !== undefined &&
      metadata.delivery_days !== null &&
      Number(metadata.delivery_days) <= 3
    ) {
      signals.push({
        title: 'Fast Delivery Promise',
        description: `Dispatched quickly with estimated delivery in ${metadata.delivery_days} day${Number(metadata.delivery_days) === 1 ? '' : 's'}`,
        category: 'DELIVERY',
      });
    }

    // Rating
    if (
      metadata.rating !== undefined &&
      metadata.rating !== null &&
      Number(metadata.rating) >= 4.0
    ) {
      signals.push({
        title: 'Strong Customer Rating',
        description: `Verified high customer satisfaction rating of ${metadata.rating} / 5.0 stars`,
        category: 'QUALITY',
      });
    }

    // Warranty
    if (metadata.warranty) {
      signals.push({
        title: 'Warranty Protection Included',
        description: 'Manufacturer warranty verified in catalogue metadata',
        category: 'QUALITY',
      });
    }

    // Returns
    if (
      metadata.return_days !== undefined &&
      metadata.return_days !== null &&
      Number(metadata.return_days) >= 7
    ) {
      signals.push({
        title: 'Generous Return Policy',
        description: `${metadata.return_days}-day return window provides strong buyer confidence`,
        category: 'RETURNS',
      });
    }
  } else {
    // When product details are not in client cache, provide truthful signals from simulation outcome
    signals.push({
      title: 'Hard Constraints Satisfied',
      description:
        'Candidate item passed all hard budget, inventory, and specification gatekeeper checks.',
      category: 'BUDGET',
    });
  }

  // High Persona Affinity
  if (item.score >= 0.75) {
    signals.push({
      title: 'High Persona Match Affinity',
      description: `Overall composite score of ${(item.score * 100).toFixed(0)}% exceeds high affinity threshold`,
      category: 'AFFINITY',
    });
  }

  return signals;
};

export const getFrictionSignals = (
  item: SimulationResultItem,
  intent: IntentSummary
): FrictionSignal[] => {
  const signals: FrictionSignal[] = [];

  const reasonLabels: Record<string, { title: string; description: string; type: 'HARD_BLOCKER' | 'SOFT_PENALTY'; severity: 'HIGH' | 'MEDIUM' | 'LOW' }> = {
    PRICE_MISMATCH: {
      title: 'Price Exceeds Maximum Budget',
      description: intent.maxBudget ? `Item price exceeds the buyer's maximum budget ceiling of ${formatPrice(intent.maxBudget)}.` : 'Price violates budget ceiling constraint.',
      type: 'HARD_BLOCKER',
      severity: 'HIGH',
    },
    INVENTORY_ISSUE: {
      title: 'Catalogue Availability / Inactive Item',
      description: 'Product is marked inactive or has 0 available inventory units in the warehouse.',
      type: 'HARD_BLOCKER',
      severity: 'HIGH',
    },
    DELIVERY_TOO_SLOW: {
      title: 'Delivery Timeline Exceeds Deadline',
      description: intent.deliveryDeadlineDays ? `Estimated delivery days exceed the buyer's required deadline of ${intent.deliveryDeadlineDays} days.` : 'Delivery speed is too slow for scenario requirements.',
      type: 'HARD_BLOCKER',
      severity: 'HIGH',
    },
    DELIVERY_UNKNOWN: {
      title: 'Unverified Delivery Timeline',
      description: 'Estimated delivery days are not published in catalogue metadata, violating urgent delivery requirements.',
      type: 'HARD_BLOCKER',
      severity: 'HIGH',
    },
    MISSING_FEATURE: {
      title: 'Required Specification Not Found',
      description: intent.requirements && intent.requirements.length > 0 ? `Mandatory required feature (${intent.requirements.join(', ')}) could not be confirmed in product specifications.` : 'Required product feature was not found in metadata.',
      type: 'HARD_BLOCKER',
      severity: 'HIGH',
    },
    DELIVERY_UNCLEAR: {
      title: 'Missing Delivery Speed Information',
      description: 'Speed-sensitive buyer encountered uncertainty because delivery duration is absent from metadata.',
      type: 'SOFT_PENALTY',
      severity: 'MEDIUM',
    },
    RETURN_UNCLEAR: {
      title: 'Missing Return Policy Terms',
      description: 'Buyer persona penalized ranking score due to lack of explicit return days in catalogue data.',
      type: 'SOFT_PENALTY',
      severity: 'MEDIUM',
    },
    INSUFFICIENT_PRODUCT_INFORMATION: {
      title: 'Sparse Product Specifications / Description',
      description: 'Feature researcher persona received inadequate detail due to brief description or minimal metadata attributes.',
      type: 'SOFT_PENALTY',
      severity: 'LOW',
    },
    NO_SUITABLE_PRODUCT: {
      title: 'No Matching Catalogue Products',
      description: 'All evaluated products in the merchant catalogue failed hard disqualification criteria.',
      type: 'HARD_BLOCKER',
      severity: 'HIGH',
    },
  };

  (item.frictions || []).forEach((f) => {
    const reasonKey = f.reason || f.type || 'UNKNOWN';
    const mapped = reasonLabels[reasonKey] || {
      title: reasonKey.replace(/_/g, ' '),
      description: f.description || 'Observed friction during evaluation',
      type: f.type === 'HARD_CONSTRAINT' ? 'HARD_BLOCKER' : 'SOFT_PENALTY',
      severity: f.type === 'HARD_CONSTRAINT' ? 'HIGH' : 'MEDIUM',
    };

    signals.push({
      type: mapped.type,
      reason: reasonKey,
      title: mapped.title,
      description: mapped.description,
      affectedProductName: f.product_name,
      severity: mapped.severity,
    });
  });

  return signals;
};
