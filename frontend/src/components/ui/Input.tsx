import React from 'react';
import { cn } from '../../utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="flex flex-col space-y-1.5 w-full">
        {label && (
          <label className="text-sm font-medium text-[var(--rzp-text)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded-lg border border-[var(--rzp-border-strong)] bg-white px-3 py-2 text-sm placeholder:text-[var(--rzp-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--rzp-primary)] focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-[var(--rzp-danger)] focus:ring-[var(--rzp-danger)]',
            className
          )}
          {...props}
        />
        {error && <span className="text-xs text-[var(--rzp-danger)]">{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
