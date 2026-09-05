import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, AlertTriangle, Lightbulb, CheckCircle2, ArrowRight } from 'lucide-react';

export type PipelineStepId = 'simulation' | 'friction' | 'insight' | 'action';

interface PipelineStep {
  id: PipelineStepId;
  number: number;
  label: string;
  sublabel: string;
  icon: React.ElementType;
  to: string;
  active?: boolean;
}

interface RecommendationPipelineHeaderProps {
  currentStep?: PipelineStepId;
  onStepClick?: (step: PipelineStepId) => void;
}

export const RecommendationPipelineHeader: React.FC<RecommendationPipelineHeaderProps> = ({
  currentStep = 'action',
  onStepClick
}) => {
  const navigate = useNavigate();

  const steps: PipelineStep[] = [
    {
      id: 'simulation',
      number: 1,
      label: 'SIMULATION',
      sublabel: 'Autonomous Persona Runs',
      icon: Bot,
      to: '/simulation?step=simulation',
      active: currentStep === 'simulation'
    },
    {
      id: 'friction',
      number: 2,
      label: 'BUYER FRICTION',
      sublabel: 'Constraint Drop-offs & Penalties',
      icon: AlertTriangle,
      to: '/simulation?step=friction',
      active: currentStep === 'friction'
    },
    {
      id: 'insight',
      number: 3,
      label: 'MERCHANT INSIGHT',
      sublabel: 'Root Cause Diagnostics',
      icon: Lightbulb,
      to: '/optimization?step=insight',
      active: currentStep === 'insight'
    },
    {
      id: 'action',
      number: 4,
      label: 'RECOMMENDED ACTION',
      sublabel: 'Empirical Catalogue Interventions',
      icon: CheckCircle2,
      to: '/optimization?step=action',
      active: currentStep === 'action'
    }
  ];

  const handleStepClick = (step: PipelineStep) => {
    if (onStepClick) {
      onStepClick(step.id);
    } else {
      navigate(step.to);
    }
  };

  return (
    <div className="bg-[var(--rzp-surface)] rounded-xl border border-[var(--rzp-border)] p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--rzp-text-muted)] flex items-center">
          <span className="w-2 h-2 rounded-full bg-[var(--rzp-ai)] mr-1.5 animate-pulse"></span>
          GraahakLens Intelligence Pipeline
        </span>
        <span className="text-xs text-[var(--rzp-text-muted)] font-medium">
          Click any step to switch stages (01 Simulation → 02 Friction → 03 Insight → 04 Action)
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 relative">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isCurrent = step.active;

          return (
            <button
              key={step.id}
              type="button"
              onClick={() => handleStepClick(step)}
              aria-current={isCurrent ? 'step' : undefined}
              className={`p-3 rounded-lg border transition-all flex items-start space-x-3 text-left w-full cursor-pointer focus:outline-none focus:ring-2 focus:ring-[var(--rzp-ai)] ${
                isCurrent
                  ? 'bg-[var(--rzp-ai-soft)] border-[var(--rzp-ai)] shadow-sm ring-1 ring-[var(--rzp-ai)]'
                  : 'bg-[var(--rzp-surface-subtle)] border-[var(--rzp-border)] opacity-85 hover:opacity-100 hover:border-[var(--rzp-ai)] hover:bg-white hover:shadow-xs'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                  isCurrent
                    ? 'bg-[var(--rzp-ai)] text-white shadow-sm'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center space-x-1.5">
                  <span className="text-[10px] font-mono font-bold text-[var(--rzp-text-muted)]">
                    0{step.number}
                  </span>
                  <span
                    className={`text-xs font-bold tracking-tight uppercase ${
                      isCurrent ? 'text-[var(--rzp-ai)]' : 'text-[var(--rzp-text)]'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                <p className="text-[11px] text-[var(--rzp-text-secondary)] mt-0.5 leading-snug line-clamp-1">
                  {step.sublabel}
                </p>
              </div>
              {idx < steps.length - 1 && (
                <ArrowRight className="hidden lg:block h-3.5 w-3.5 text-gray-300 self-center -mr-1 shrink-0" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
