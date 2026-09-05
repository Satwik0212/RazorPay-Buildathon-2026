import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { cn } from '../utils/cn';
import {
  LayoutDashboard,
  Package,
  Bot,
  TestTube,
  Activity,
  ReceiptText,
  LineChart,
  Settings,
  ShoppingBag,
  Megaphone,
  LogOut,
  Sparkles
} from 'lucide-react';
import { authApi } from '../api/auth';
import type { User } from '../types';

export const AppLayout = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('user_profile');
    if (saved) {
      try { return JSON.parse(saved); } catch {}
    }
    return null;
  });
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const initSession = async () => {
      if (location.pathname.startsWith('/buyer')) {
        // Buyer pages: attempt to get logged-in user profile if available
        try {
          const token = localStorage.getItem('buyer_token') || localStorage.getItem('access_token');
          if (token) {
            const meRes = await authApi.getMe();
            if (meRes.data) {
              setCurrentUser(meRes.data);
              localStorage.setItem('user_profile', JSON.stringify(meRes.data));
            }
          }
        } catch {
          // Not authenticated on buyer path is fine – don't redirect
        }
        setIsInitializing(false);
        return;
      }

      const token = localStorage.getItem('access_token');
      if (!token) {
        // No token at all – redirect to login immediately
        setIsInitializing(false);
        navigate('/login');
        return;
      }

      // Validate existing token by calling /auth/me (authoritative source)
      try {
        const meRes = await authApi.getMe();
        if (meRes.data) {
          setCurrentUser(meRes.data);
          localStorage.setItem('user_profile', JSON.stringify(meRes.data));
        }
      } catch {
        // Token is invalid/expired – clear state and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_profile');
        setCurrentUser(null);
        navigate('/login');
      }
      setIsInitializing(false);
    };
    initSession();
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('buyer_token');
    localStorage.removeItem('user_profile');
    setCurrentUser(null);
    navigate('/login');
  };

  if (isInitializing) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-500">Initializing session...</div>;
  }

  const isBuyer = currentUser?.role === 'CUSTOMER' || currentUser?.role === 'BUYER';

  // Role-gated navigation: Merchant sees management tools, Buyer sees storefront
  const merchantNavItems = [
    { name: 'Overview', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Catalogue', to: '/catalogue', icon: Package },
    { name: 'AI Buyers', to: '/buyer', icon: Bot },
    { name: 'Simulations', to: '/simulation', icon: TestTube },
    { name: 'Optimizations', to: '/optimization', icon: Activity },
    { name: 'Campaigns', to: '/campaigns', icon: Megaphone },
    { name: 'Transactions', to: '/transactions', icon: ReceiptText },
    { name: 'Analytics', to: '/analytics', icon: LineChart },
    { name: 'Settings', to: '/settings', icon: Settings },
  ];

  const buyerNavItems = [
    { name: 'Discover & Shop', to: '/buyer', icon: ShoppingBag },
    { name: 'Product Catalogue', to: '/catalogue', icon: Package },
    { name: 'Account Settings', to: '/settings', icon: Settings },
  ];

  const activeNavItems = isBuyer ? buyerNavItems : merchantNavItems;

  const displayName = currentUser?.name || (isBuyer ? 'Buyer User' : 'Merchant User');
  const displayEmail = currentUser?.email || (isBuyer ? 'buyer@example.com' : 'merchant@example.com');
  const initialLetter = displayName.charAt(0).toUpperCase();

  return (
    <div className="flex h-screen w-full bg-[var(--rzp-bg)]">
      {/* Sidebar */}
      <aside className="w-[260px] bg-[var(--rzp-surface)] border-r border-[var(--rzp-border)] flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-[var(--rzp-border)]">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-[var(--rzp-primary)] rounded-md flex items-center justify-center shadow-xs">
              <span className="text-white font-bold text-lg leading-none">G</span>
            </div>
            <div>
              <span className="font-semibold text-lg tracking-tight block leading-tight">GraahakLens</span>
              <span className="text-[10px] text-[var(--rzp-text-muted)] font-medium">
                {isBuyer ? 'Buyer Experience' : 'Merchant Operations'}
              </span>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
          {activeNavItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              className={({ isActive }) => cn(
                "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--rzp-primary-soft)] text-[var(--rzp-primary)]"
                  : "text-[var(--rzp-text-secondary)] hover:bg-gray-100 hover:text-[var(--rzp-text)]"
              )}
            >
              <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
              {item.name}
            </NavLink>
          ))}

          <div className="pt-8 pb-2">
            <div className="px-3 text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">
              {isBuyer ? 'Merchant View' : 'Demo Flows'}
            </div>
          </div>

          {isBuyer ? (
            <NavLink
              to="/dashboard"
              className={({ isActive }) => cn(
                "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-purple-100 text-purple-700"
                  : "text-[var(--rzp-text-secondary)] hover:bg-gray-100 hover:text-[var(--rzp-text)]"
              )}
            >
              <LayoutDashboard className="mr-3 h-5 w-5 flex-shrink-0" />
              Merchant Console
            </NavLink>
          ) : (
            <NavLink
              to="/buyer"
              className={({ isActive }) => cn(
                "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-purple-100 text-purple-700"
                  : "text-[var(--rzp-text-secondary)] hover:bg-gray-100 hover:text-[var(--rzp-text)]"
              )}
            >
              <ShoppingBag className="mr-3 h-5 w-5 flex-shrink-0" />
              Simulate Buyer
            </NavLink>
          )}
        </nav>

        {/* Dynamic User Profile Footer */}
        <div className="p-4 border-t border-[var(--rzp-border)] bg-[var(--rzp-surface)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center min-w-0">
              <div className={cn(
                "h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0 shadow-xs",
                isBuyer ? "bg-emerald-600" : "bg-[var(--rzp-primary)]"
              )}>
                {initialLetter}
              </div>
              <div className="ml-3 min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="text-sm font-semibold text-[var(--rzp-text)] truncate max-w-[110px]" title={displayName}>
                    {displayName}
                  </p>
                  <span className={cn(
                    "text-[9px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0",
                    isBuyer
                      ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                      : "bg-purple-100 text-purple-700 border border-purple-200"
                  )}>
                    {isBuyer ? 'Buyer' : 'Merchant'}
                  </span>
                </div>
                <p className="text-xs text-[var(--rzp-text-muted)] truncate max-w-[145px]" title={displayEmail}>
                  {displayEmail}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer shrink-0 ml-1"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 flex items-center justify-between px-6 border-b border-[var(--rzp-border)] bg-[var(--rzp-surface)] md:hidden">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-[var(--rzp-primary)] rounded-md flex items-center justify-center">
              <span className="text-white font-bold text-lg leading-none">G</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">GraahakLens</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-xs font-bold uppercase px-2 py-0.5 rounded",
              isBuyer ? "bg-emerald-100 text-emerald-700" : "bg-purple-100 text-purple-700"
            )}>
              {isBuyer ? 'Buyer' : 'Merchant'}
            </span>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 text-gray-400 hover:text-red-600 rounded-md"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-8">
          <div className="mx-auto max-w-[1440px]">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};
