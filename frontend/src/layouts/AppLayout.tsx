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
  Megaphone
} from 'lucide-react';
import { authApi } from '../api/auth';

export const AppLayout = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const initSession = async () => {
      if (location.pathname.startsWith('/buyer')) {
        setIsInitializing(false);
        return;
      }
      
      const token = localStorage.getItem('access_token');
      if (!token) {
        await authApi.getOrInitMerchantId();
      } else {
        // Validate if the current token belongs to the demo merchant.
        // If it's a stale test user from a previous session, re-initialize the demo.
        try {
          const me = await authApi.getMe();
          if (me.data.email !== 'merchant@demo.com') {
             localStorage.removeItem('access_token');
             await authApi.getOrInitMerchantId();
          }
        } catch {
          localStorage.removeItem('access_token');
          await authApi.getOrInitMerchantId();
        }
      }
      setIsInitializing(false);
    };
    initSession();
  }, [location.pathname]);

  if (isInitializing) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-500">Initializing session...</div>;
  }

  const navItems = [
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

  return (
    <div className="flex h-screen w-full bg-[var(--rzp-bg)]">
      {/* Sidebar */}
      <aside className="w-[260px] bg-[var(--rzp-surface)] border-r border-[var(--rzp-border)] flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-[var(--rzp-border)]">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-[var(--rzp-primary)] rounded-md flex items-center justify-center">
              <span className="text-white font-bold text-lg leading-none">R</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">AI Commerce</span>
          </div>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
          {navItems.map((item) => (
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
              Demo Flows
            </div>
          </div>
          
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
        </nav>
        
        <div className="p-4 border-t border-[var(--rzp-border)]">
          <div className="flex items-center">
            <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium">
              M
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-[var(--rzp-text)]">Merchant User</p>
              <p className="text-xs text-[var(--rzp-text-muted)]">merchant@example.com</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 flex items-center justify-between px-8 border-b border-[var(--rzp-border)] bg-[var(--rzp-surface)] md:hidden">
            <span className="font-semibold text-lg tracking-tight">AI Commerce</span>
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
