import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from './ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--rzp-bg)] p-4">
          <div className="max-w-md w-full bg-[var(--rzp-surface)] rounded-xl border border-[var(--rzp-border)] p-6 shadow-sm text-center">
            <AlertCircle className="h-12 w-12 text-[var(--rzp-danger)] mx-auto mb-4" />
            <h2 className="text-xl font-bold text-[var(--rzp-text)] mb-2">Something went wrong</h2>
            <p className="text-sm text-[var(--rzp-text-muted)] mb-6">
              {this.state.error?.message || "An unexpected runtime error occurred."}
            </p>
            <Button onClick={() => window.location.reload()} variant="primary" className="w-full">
              Reload Application
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
