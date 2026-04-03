import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        success: "border-transparent bg-metric-positive/15 text-metric-positive",
        warning: "border-transparent bg-metric-warning/15 text-metric-warning",
        danger: "border-transparent bg-metric-negative/15 text-metric-negative",
        info: "border-transparent bg-brand-500/15 text-brand-400",
        // Risk levels
        healthy: "border-transparent bg-risk-healthy/15 text-risk-healthy",
        at_risk: "border-transparent bg-risk-at_risk/15 text-risk-at_risk",
        critical: "border-transparent bg-risk-critical/15 text-risk-critical",
        // Plan tiers
        starter: "border-transparent bg-plan-starter/15 text-plan-starter",
        growth: "border-transparent bg-plan-growth/15 text-plan-growth",
        business: "border-transparent bg-plan-business/15 text-plan-business",
        enterprise: "border-transparent bg-plan-enterprise/15 text-plan-enterprise",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
