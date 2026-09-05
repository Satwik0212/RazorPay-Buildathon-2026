export type Currency = 'INR' | 'USD';

export interface User {
  id: string;
  name?: string;
  email: string;
  role: 'MERCHANT' | 'BUYER' | 'CUSTOMER' | 'ADMIN';
  is_active?: boolean;
  merchant_id?: string;
  customer_id?: string;
  created_at?: string;
}

export interface Merchant {
  id: string;
  user_id: string;
  business_name: string;
  onboarding_status: string;
  ai_readiness_score: number;
}

export interface Inventory {
  product_id: string;
  available_quantity: number;
  reserved_quantity: number;
}

export interface Product {
  id: string;
  merchant_id: string;
  name: string;
  description?: string;
  price: number; // minor units
  currency: Currency;
  category: string;
  metadata?: Record<string, any>;
  is_active: boolean;
  inventory?: Inventory;
  created_at: string;
  updated_at: string;
}

export interface BuyerIntent {
  id: string;
  session_id: string;
  raw_query: string;
  parsed_intent: Record<string, any>;
  status: 'PENDING' | 'RESOLVED' | 'FAILED';
}

export interface CartItem {
  id: string;
  cart_id: string;
  product_id: string;
  quantity: number;
  product?: Product;
  created_at: string;
  updated_at: string;
}

export interface Cart {
  id: string;
  customer_id: string;
  merchant_id: string;
  status: string;
  items: CartItem[];
  created_at: string;
  updated_at: string;
}

export interface Quote {
  quote_id: string;
  cart_id: string;
  subtotal: number;
  tax: number;
  shipping: number;
  discount: number;
  total: number; // Truth for payment
  currency: Currency;
  quote_hash: string;
  expires_at: string;
  created_at: string;
  line_items_snapshot?: any[];
}

export interface Authorization {
  authorization_id: string;
  quote_id: string;
  customer_id: string;
  amount: number;
  currency: Currency;
  status: 'APPROVED' | 'REVIEW_REQUIRED' | 'BLOCKED';
  created_at: string;
  updated_at: string;
}

export interface CheckoutOrder {
  order_id: string;
  merchant_id: string;
  customer_id: string;
  cart_id: string;
  authorization_id: string;
  razorpay_order_id: string;
  razorpay_key_id?: string;
  amount: number;
  currency: Currency;
  status: string;
  receipt: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: string;
  order_id: string;
  razorpay_payment_id?: string;
  razorpay_order_id?: string;
  razorpay_signature?: string;
  amount: number;
  currency: Currency;
  status: 'PENDING' | 'SUCCESS' | 'FAILED';
}

export interface BuyerPersona {
  id: string;
  name: string;
  description: string;
  budget_min: number;
  budget_max: number;
  priorities: string[];
  urgency: string;
  weights: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface SimulationFriction {
  severity?: 'LOW' | 'MEDIUM' | 'HIGH';
  reason: string;
  description?: string;
  confidence?: number;
  [key: string]: any;
}

export interface SimulationRanking {
  product_id: string;
  product_name?: string;
  score: number;
  rank: number;
  frictions?: string[];
  passed?: boolean;
  price?: number;
  category?: string;
  score_breakdown?: Record<string, number>;
}

export interface SimulationResultItem {
  persona_name: string;
  selected_product_id: string | null;
  score: number;
  constraints_satisfied: boolean;
  reason_codes: string[];
  frictions: SimulationFriction[];
  rankings: SimulationRanking[];
  explanation: string;
  intent?: {
    max_budget?: number;
    requirements?: string[];
    delivery_deadline_days?: number;
    category?: string;
    preferences?: string[];
    [key: string]: any;
  };
  persona_weights?: Record<string, number>;
  /** Total products evaluated before rankings were truncated for response size */
  total_products_evaluated?: number;
  /** Total products that passed all hard constraints (before truncation) */
  total_eligible?: number;
  /** Total products that failed at least one hard constraint (before truncation) */
  total_disqualified?: number;
  /** Exact deterministic component score breakdown computed by ProductScorer */
  score_breakdown?: Record<string, number>;
  selected_product_name?: string;
  selected_product_price?: number;
  selected_product_category?: string;
}

export interface SimulationSummaryMetrics {
  buyers_simulated: number;
  successful_matches: number;
  failed_matches: number;
  constraint_satisfaction_rate: number;
  average_score: number;
  friction_distribution?: Record<string, number>;
  persona_success_rates?: Record<string, number>;
  metric_type?: string;
  custom_buyer_name?: string;
}

/** Merchant-defined custom buyer for the "Create Your Own Simulation" feature. */
export interface CustomBuyerConfig {
  name: string;                                // Display name, e.g. "Weekend Audio Buyer"
  max_budget?: number;                         // Rupees (₹), converted to paise server-side
  delivery_deadline_days?: number;             // Days 1–365
  requirements: string[];                      // Feature keywords, e.g. ["warranty", "bluetooth"]
  weights: {
    quality: number;
    metadata: number;
    returns: number;
    delivery: number;
    price: number;
  };                                           // Must sum to 1.0 (100%)
  scenario_count: number;                      // 1 | 5 | 10 | 20
}

export interface SimulationResponse {
  simulation_id: string;
  merchant_id: string;
  status: string;
  scenario_count: number;
  buyer_profiles: string[];
  summary_metrics: SimulationSummaryMetrics;
  results: SimulationResultItem[];
  created_at: string;
}


export interface Recommendation {
  id: string;
  merchant_id: string;
  simulation_run_id?: string | null;
  product_id?: string | null;
  type: string;
  title: string;
  reason: string;
  action_data: Record<string, any>;
  expected_simulated_impact: number;
  confidence: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WhatIfRequest {
  hypothesis: string;
  modifications: {
    product_id?: string;
    price?: number;
    delivery_days?: number;
    return_days?: number;
    metadata?: Record<string, any>;
    [key: string]: any;
  };
}

export interface WhatIfMetrics {
  simulated_selection_rate?: number;
  average_score?: number;
  matches?: number;
  total_scenarios?: number;
  conversion_rate?: number;
  average_order_value?: number;
  metric_type?: string;
  [key: string]: any;
}

export interface WhatIfTargetMetrics {
  product_id: string;
  baseline_avg_score: number;
  proposed_avg_score: number;
  score_delta: number;
  score_delta_pct: number;
  baseline_eligible_rate: number;
  proposed_eligible_rate: number;
  eligibility_delta: number;
  scenarios_evaluated: number;
  note: string;
}

export interface WhatIfResponse {
  id: string;
  merchant_id: string;
  hypothesis: string;
  modifications: Record<string, any>;
  baseline_metrics: WhatIfMetrics;
  simulated_metrics: WhatIfMetrics;
  delta_percentage: number;
  created_at: string;
  /** Present only when a specific product_id is targeted. Product-level scores, not catalogue-wide. */
  target_product_metrics?: WhatIfTargetMetrics;
}

export interface MerchantOverviewAnalytics {
  total_products: number;
  active_products: number;
  total_inventory: number;
  total_categories: number;
  total_personas: number;
  total_recommendations: number;
}


export interface PersonaPerformance {
  persona_name: string;
  total_simulations: number;
  matches: number;
  rejections: number;
  average_score: number;
  top_frictions: string[];
}

export interface FrictionBreakdown {
  friction_type: string;
  count: number;
}

export interface ProductIntelligence {
  product_id: string;
  product_name: string;
  problem: string;
  evidence: string;
  recommended_action: string;
  recommendation_id: string;
}

export interface RecommendationLifecycle {
  proposed: number;
  applied: number;
  rejected: number;
}

export interface MerchantIntelligenceAnalytics {
  overview: MerchantOverviewAnalytics;
  persona_performance: PersonaPerformance[];
  friction_breakdown: FrictionBreakdown[];
  product_intelligence: ProductIntelligence[];
  recommendation_lifecycle: RecommendationLifecycle;
}

export interface UpsellSuggestion {
  product_id: string;
  name: string;
  price: number;
  category: string;
  score: number;
  explanation?: string;
  recommendation_type: 'UPSELL' | 'CROSS_SELL';
  ai_confidence?: number;
}

export interface UpsellResponse {
  upsell: UpsellSuggestion[];
  cross_sell: UpsellSuggestion[];
  anchor_product_ids: string[];
  data_source: string;
  ai_powered: boolean;
}

export type CampaignStatus = "PROPOSED" | "ACTIVE" | "PAUSED" | "ENDED";

export interface Campaign {
  id: string;
  merchant_id: string;
  name: string;
  objective: string;
  campaign_type: string;
  target_persona_id?: string;
  target_product_id?: string;
  trigger_signal: string;
  trigger_evidence: Record<string, any>;
  message_content: string;
  status: CampaignStatus;
  activated_at?: string;
  ended_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CampaignStatusUpdate {
  status: CampaignStatus;
}

