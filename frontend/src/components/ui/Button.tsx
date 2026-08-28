import React from 'react';
import { cn } from '../../utils/cn';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'ai';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';
    
    const variants = {
      primary: 'bg-[var(--rzp-primary)] text-white hover:bg-[var(--rzp-primary-hover)] focus:ring-[var(--rzp-primary)]',
      secondary: 'bg-[var(--rzp-surface-subtle)] text-[var(--rzp-text)] border border-[var(--rzp-border)] hover:bg-gray-100 focus:ring-gray-200',
      outline: 'border border-[var(--rzp-border-strong)] text-[var(--rzp-text)] hover:bg-gray-50 focus:ring-gray-200',
      ghost: 'hover:bg-gray-100 text-[var(--rzp-text-secondary)] hover:text-[var(--rzp-text)] focus:ring-gray-200',
      danger: 'bg-[var(--rzp-danger)] text-white hover:opacity-90 focus:ring-[var(--rzp-danger)]',
      ai: 'bg-[var(--rzp-ai-soft)] text-[var(--rzp-ai)] hover:bg-purple-200 focus:ring-[var(--rzp-ai)] border border-[var(--rzp-ai)]',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 text-sm',
      lg: 'h-12 px-6 text-base',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
