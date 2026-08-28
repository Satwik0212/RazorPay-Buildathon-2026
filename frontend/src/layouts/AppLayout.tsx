import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
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
  ShoppingBag
} from 'lucide-react';

export const AppLayout = () => {
  const navItems = [
    { name: 'Overview', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Catalogue', to: '/catalogue', icon: Package },
    { name: 'AI Buyers', to: '/buyer', icon: Bot },
    { name: 'Simulations', to: '/simulation', icon: TestTube },
    { name: 'Optimizations', to: '/optimization', icon: Activity },
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
