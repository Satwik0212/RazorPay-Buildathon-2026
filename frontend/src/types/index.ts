export type Currency = 'INR' | 'USD';

export interface User {
  id: string;
  email: string;
  role: 'MERCHANT' | 'BUYER' | 'ADMIN';
  created_at: string;
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
  amount: number;
  currency: Currency;
  status: string;
  receipt: string;
  razorpay_key_id?: string;
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

export interface SimulationResult {
  id: string;
  merchant_id: string;
  persona_id: string;
  scenario: Record<string, any>;
  outcome: 'PURCHASE' | 'ABANDON' | 'ERROR';
  friction_points: string[];
  decision_time_ms: number;
}
