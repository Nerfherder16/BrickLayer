---
name: ui-design-system
description: Full UI design system with code templates — dark-first dashboards, bento grids, glass cards, floating forms, Nivo charts
---

# UI Design System — Code Templates

Reference implementations for Tim's design language. Raw Tailwind, React 19, TypeScript.
Every template uses the retro sunset palette as default — swap CSS custom properties for per-app palettes.

---

## Setup: CSS Custom Properties

Add to your `index.css` or `globals.css` inside `@theme`:

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  /* Backgrounds */
  --bg-page: #0f0d1a;
  --bg-card: #1e1b2e;
  --bg-elevated: #2d2a3e;

  /* Accents — swap these per app */
  --accent-primary: #38bdf8;    /* cyan */
  --accent-secondary: #8b5cf6;  /* violet */
  --accent-hot: #f472b6;        /* rose */
  --accent-warm: #f59e0b;       /* amber */
  --accent-success: #34d399;    /* emerald */
  --accent-danger: #ef4444;     /* red */

  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.05);
  --border-visible: rgba(255, 255, 255, 0.10);

  /* Fonts */
  --font-display: 'Space Grotesk', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

body {
  background-color: var(--bg-page);
  color: var(--text-primary);
  font-family: var(--font-display);
}
```

### Per-App Palette Override

When using a coolors.co palette, override only the accent vars:

```css
/* Example: Tropical app palette */
:root {
  --accent-primary: #06d6a0;
  --accent-secondary: #118ab2;
  --accent-hot: #ef476f;
  --accent-warm: #ffd166;
}
```

---

## Tailwind v4 Config

In `tailwind.config.ts`, extend with the custom properties:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "var(--bg-page)",
        card: "var(--bg-card)",
        elevated: "var(--bg-elevated)",
        accent: {
          DEFAULT: "var(--accent-primary)",
          secondary: "var(--accent-secondary)",
          hot: "var(--accent-hot)",
          warm: "var(--accent-warm)",
          success: "var(--accent-success)",
          danger: "var(--accent-danger)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
};

export default config;
```

---

## Component: Glass Card

```tsx
import { cn } from "../lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
  padding?: "sm" | "md" | "lg";
}

const paddings = {
  sm: "p-3",
  md: "p-5",
  lg: "p-7",
};

export function GlassCard({
  children,
  className,
  glow = false,
  padding = "md",
  ...props
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "rounded-md border border-white/10 bg-white/5 backdrop-blur-xl",
        paddings[padding],
        glow && "shadow-[0_0_20px_rgba(56,189,248,0.08)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
```

---

## Component: Stat / KPI Card

```tsx
import { TrendingUp, TrendingDown } from "lucide-react";

import { cn } from "../lib/utils";
import { GlassCard } from "./GlassCard";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  sparkline?: number[];
}

export function StatCard({ label, value, change, sparkline }: StatCardProps) {
  const isPositive = change && change > 0;

  return (
    <GlassCard className="flex flex-col gap-2">
      <span className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
        {label}
      </span>
      <div className="flex items-end justify-between gap-4">
        <span className="font-display text-4xl font-light text-[var(--text-primary)]">
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
        {sparkline && (
          <svg viewBox="0 0 80 32" className="h-8 w-20 text-accent">
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={sparkline
                .map((v, i) => {
                  const x = (i / (sparkline.length - 1)) * 80;
                  const y = 32 - (v / Math.max(...sparkline)) * 28;
                  return `${x},${y}`;
                })
                .join(" ")}
            />
          </svg>
        )}
      </div>
      {change !== undefined && (
        <div
          className={cn(
            "flex items-center gap-1 text-xs font-medium",
            isPositive ? "text-[var(--accent-success)]" : "text-[var(--accent-danger)]"
          )}
        >
          {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          <span>{isPositive ? "+" : ""}{change}%</span>
          <span className="text-[var(--text-muted)]">vs last period</span>
        </div>
      )}
    </GlassCard>
  );
}
```

---

## Component: Bento Grid Layout

```tsx
import { cn } from "../lib/utils";

interface BentoGridProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function BentoGrid({ children, className, ...props }: BentoGridProps) {
  return (
    <div
      className={cn(
        "grid auto-rows-[minmax(180px,auto)] grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface BentoItemProps extends React.HTMLAttributes<HTMLDivElement> {
  colSpan?: 1 | 2 | 3 | 4;
  rowSpan?: 1 | 2;
}

const colSpans = {
  1: "col-span-1",
  2: "sm:col-span-2",
  3: "sm:col-span-2 lg:col-span-3",
  4: "sm:col-span-2 lg:col-span-4",
};

const rowSpans = {
  1: "row-span-1",
  2: "row-span-2",
};

export function BentoItem({
  children,
  className,
  colSpan = 1,
  rowSpan = 1,
  ...props
}: BentoItemProps) {
  return (
    <div className={cn(colSpans[colSpan], rowSpans[rowSpan], className)} {...props}>
      {children}
    </div>
  );
}
```

Usage:
```tsx
<BentoGrid>
  <BentoItem colSpan={2} rowSpan={2}>
    <GlassCard className="h-full"><AreaChart /></GlassCard>
  </BentoItem>
  <BentoItem>
    <StatCard label="Users" value={54081} change={8.2} />
  </BentoItem>
  <BentoItem>
    <StatCard label="Revenue" value="$12,875" change={-2.1} />
  </BentoItem>
  <BentoItem colSpan={2}>
    <GlassCard className="h-full"><DonutChart /></GlassCard>
  </BentoItem>
</BentoGrid>
```

---

## Component: Icon Sidebar

```tsx
import { useState } from "react";

import {
  LayoutDashboard, BarChart3, Users, Settings,
  CreditCard, Share2, FileText,
} from "lucide-react";

import { cn } from "../lib/utils";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: BarChart3, label: "Analytics", href: "/analytics" },
  { icon: Users, label: "Users", href: "/users" },
  { icon: CreditCard, label: "Billing", href: "/billing" },
  { icon: FileText, label: "Reports", href: "/reports" },
  { icon: Share2, label: "Integrations", href: "/integrations" },
];

interface SidebarProps {
  activePath: string;
}

export function IconSidebar({ activePath }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-16 flex-col items-center border-r border-white/5 bg-[var(--bg-card)] py-6">
      {/* Logo */}
      <div className="mb-8 flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
        <LayoutDashboard className="h-5 w-5 text-accent" />
      </div>

      {/* Nav items */}
      <nav className="flex flex-1 flex-col items-center gap-2">
        {navItems.map((item) => {
          const isActive = activePath === item.href;
          return (
            <a
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex h-10 w-10 items-center justify-center rounded-lg transition-all duration-200",
                isActive
                  ? "bg-accent/10 text-accent shadow-[0_0_12px_rgba(56,189,248,0.1)]"
                  : "text-[var(--text-muted)] hover:bg-white/5 hover:text-[var(--text-secondary)]"
              )}
            >
              <item.icon className="h-5 w-5" />
              {/* Tooltip */}
              <span className="pointer-events-none absolute left-full ml-3 whitespace-nowrap rounded-md bg-[var(--bg-elevated)] px-2.5 py-1 text-xs font-medium text-[var(--text-primary)] opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                {item.label}
              </span>
              {/* Active indicator */}
              {isActive && (
                <span className="absolute -left-[1.1rem] h-5 w-0.5 rounded-full bg-accent" />
              )}
            </a>
          );
        })}
      </nav>

      {/* Bottom settings */}
      <a
        href="/settings"
        className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--text-muted)] transition-colors hover:bg-white/5 hover:text-[var(--text-secondary)]"
      >
        <Settings className="h-5 w-5" />
      </a>
    </aside>
  );
}
```

---

## Component: Data Table

```tsx
import { cn } from "../lib/utils";

interface Column<T> {
  key: keyof T;
  label: string;
  align?: "left" | "right" | "center";
  render?: (value: T[keyof T], row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
}

export function DataTable<T extends { id: string | number }>({
  columns,
  data,
  onRowClick,
}: DataTableProps<T>) {
  return (
    <div className="overflow-x-auto rounded-md border border-white/10 bg-white/5 backdrop-blur-xl">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/5">
            {columns.map((col) => (
              <th
                key={String(col.key)}
                className={cn(
                  "sticky top-0 bg-[var(--bg-elevated)] px-4 py-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]",
                  col.align === "right" && "text-right",
                  col.align === "center" && "text-center"
                )}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              className={cn(
                "border-b border-white/[0.03] transition-colors duration-150",
                "hover:bg-white/[0.04]",
                onRowClick && "cursor-pointer"
              )}
            >
              {columns.map((col) => (
                <td
                  key={String(col.key)}
                  className={cn(
                    "px-4 py-3 text-[var(--text-secondary)]",
                    col.align === "right" && "text-right",
                    col.align === "center" && "text-center"
                  )}
                >
                  {col.render ? col.render(row[col.key], row) : String(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Component: Floating Label Input

```tsx
import { useState, useId } from "react";

import { cn } from "../lib/utils";

interface FloatingInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function FloatingInput({ label, error, className, ...props }: FloatingInputProps) {
  const id = useId();
  const [focused, setFocused] = useState(false);
  const hasValue = props.value !== undefined && props.value !== "";

  return (
    <div className="relative">
      <input
        id={id}
        {...props}
        onFocus={(e) => { setFocused(true); props.onFocus?.(e); }}
        onBlur={(e) => { setFocused(false); props.onBlur?.(e); }}
        placeholder=" "
        className={cn(
          "peer w-full rounded-md border bg-white/5 px-4 pb-2 pt-5 text-sm text-[var(--text-primary)] outline-none transition-all duration-200",
          focused || hasValue
            ? "border-accent/50 shadow-[0_0_0_2px_rgba(56,189,248,0.1)]"
            : "border-white/10",
          error && "border-[var(--accent-danger)]/50",
          className
        )}
      />
      <label
        htmlFor={id}
        className={cn(
          "pointer-events-none absolute left-4 transition-all duration-200",
          focused || hasValue
            ? "top-1.5 text-[10px] font-medium uppercase tracking-wide text-accent"
            : "top-3.5 text-sm text-[var(--text-muted)]"
        )}
      >
        {label}
      </label>
      {error && (
        <p className="mt-1 text-xs text-[var(--accent-danger)]">{error}</p>
      )}
    </div>
  );
}
```

---

## Component: Nivo Chart Wrapper (Area)

```tsx
import { ResponsiveLine } from "@nivo/line";

interface ChartDataPoint {
  x: string | number;
  y: number;
}

interface AreaChartProps {
  data: { id: string; data: ChartDataPoint[] }[];
  height?: number;
}

export function AreaChart({ data, height = 300 }: AreaChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveLine
        data={data}
        margin={{ top: 20, right: 20, bottom: 40, left: 50 }}
        xScale={{ type: "point" }}
        yScale={{ type: "linear", min: "auto", max: "auto" }}
        curve="monotoneX"
        enableArea={true}
        areaOpacity={0.15}
        colors={["var(--accent-primary)", "var(--accent-secondary)", "var(--accent-hot)"]}
        lineWidth={2}
        pointSize={0}
        enableGridX={false}
        gridYValues={5}
        theme={{
          background: "transparent",
          text: { fill: "var(--text-muted)", fontSize: 11 },
          grid: { line: { stroke: "rgba(255,255,255,0.05)" } },
          axis: {
            ticks: { text: { fill: "var(--text-muted)", fontSize: 11 } },
          },
          crosshair: { line: { stroke: "var(--accent-primary)", strokeWidth: 1 } },
          tooltip: {
            container: {
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              borderRadius: "6px",
              border: "1px solid rgba(255,255,255,0.1)",
              fontSize: 12,
            },
          },
        }}
        animate={true}
        motionConfig="gentle"
        defs={[
          {
            id: "gradient-primary",
            type: "linearGradient",
            colors: [
              { offset: 0, color: "var(--accent-primary)", opacity: 0.4 },
              { offset: 100, color: "var(--accent-primary)", opacity: 0 },
            ],
          },
        ]}
        fill={[{ match: { id: data[0]?.id }, id: "gradient-primary" }]}
      />
    </div>
  );
}
```

---

## Component: Toast System

```tsx
// contexts/ToastContext.tsx
import { createContext, useContext, useState, useCallback, useRef } from "react";

import { X, CheckCircle2, AlertCircle, Info } from "lucide-react";

import { cn } from "../lib/utils";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

const icons: Record<ToastType, React.ElementType> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const colors: Record<ToastType, string> = {
  success: "border-l-[var(--accent-success)] text-[var(--accent-success)]",
  error: "border-l-[var(--accent-danger)] text-[var(--accent-danger)]",
  info: "border-l-accent text-accent",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const addToast = useCallback((message: string, type: ToastType = "info") => {
    const id = ++idRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      <div className="fixed right-4 top-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <div
              key={t.id}
              className={cn(
                "flex items-center gap-3 rounded-md border-l-4 bg-[var(--bg-elevated)] px-4 py-3 shadow-lg backdrop-blur-xl",
                "animate-[slideIn_200ms_ease-out]",
                colors[t.type]
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="text-sm text-[var(--text-primary)]">{t.message}</span>
              <button
                onClick={() => dismiss(t.id)}
                className="ml-auto text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
```

Add the slide-in keyframe to your CSS:
```css
@keyframes slideIn {
  from { opacity: 0; transform: translateX(1rem); }
  to { opacity: 1; transform: translateX(0); }
}
```

---

## Component: Skeleton Loader

```tsx
import { cn } from "../lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-white/5",
        className
      )}
    />
  );
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-md border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
      <Skeleton className="mb-3 h-3 w-20" />
      <Skeleton className="mb-2 h-10 w-32" />
      <Skeleton className="h-3 w-24" />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/5 backdrop-blur-xl">
      <div className="border-b border-white/5 px-4 py-3">
        <div className="flex gap-8">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-16" />
        </div>
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="border-b border-white/[0.03] px-4 py-3">
          <div className="flex gap-8">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## Component: Badge / Pill (cva pattern)

```tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-white/10 text-[var(--text-secondary)]",
        success: "bg-[var(--accent-success)]/10 text-[var(--accent-success)]",
        warning: "bg-[var(--accent-warm)]/10 text-[var(--accent-warm)]",
        danger: "bg-[var(--accent-danger)]/10 text-[var(--accent-danger)]",
        info: "bg-accent/10 text-accent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ children, variant, className, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {children}
    </span>
  );
}
```

---

## Component: Empty State

```tsx
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white/5">
        <Icon className="h-8 w-8 text-[var(--text-muted)]" />
      </div>
      <h3 className="mb-1 text-lg font-semibold text-[var(--text-primary)]">{title}</h3>
      <p className="mb-6 max-w-sm text-sm text-[var(--text-muted)]">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-[var(--bg-page)] transition-all duration-200 hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(56,189,248,0.2)]"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
```

---

## Page Template: Dashboard

Putting it all together — the standard dashboard layout:

```tsx
import { IconSidebar } from "../components/IconSidebar";
import { BentoGrid, BentoItem } from "../components/BentoGrid";
import { GlassCard } from "../components/GlassCard";
import { StatCard } from "../components/StatCard";
import { AreaChart } from "../components/AreaChart";
import { DataTable } from "../components/DataTable";

export function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-[var(--bg-page)]">
      <IconSidebar activePath="/" />

      <main className="ml-16 flex-1 p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold text-[var(--text-primary)]">
              Dashboard
            </h1>
            <p className="text-sm text-[var(--text-muted)]">
              Overview for the last 7 days
            </p>
          </div>
        </div>

        {/* KPI Row */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Users" value={54081} change={8.2} sparkline={[20, 25, 30, 28, 35, 40, 38]} />
          <StatCard label="Revenue" value="$12,875" change={-2.1} sparkline={[30, 28, 25, 27, 22, 20, 23]} />
          <StatCard label="Sessions" value="1m 2s" />
          <StatCard label="Bounce Rate" value="74.88%" change={0.13} />
        </div>

        {/* Bento Content */}
        <BentoGrid>
          <BentoItem colSpan={2} rowSpan={2}>
            <GlassCard className="h-full">
              <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
                Sales Analytics
              </h3>
              <AreaChart data={[/* your nivo data */]} height={280} />
            </GlassCard>
          </BentoItem>
          <BentoItem colSpan={2}>
            <GlassCard className="h-full">
              <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
                Recent Activity
              </h3>
              <DataTable columns={[/* columns */]} data={[/* rows */]} />
            </GlassCard>
          </BentoItem>
        </BentoGrid>
      </main>
    </div>
  );
}
```

---

## Utility: cn()

Required by all components. Install `clsx` and `tailwind-merge`:

```bash
npm install clsx tailwind-merge
```

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

---

## Component: Nivo Bar Chart

```tsx
import { ResponsiveBar } from "@nivo/bar";

interface BarChartProps {
  data: Record<string, string | number>[];
  keys: string[];
  indexBy: string;
  height?: number;
  layout?: "vertical" | "horizontal";
}

export function BarChart({
  data,
  keys,
  indexBy,
  height = 300,
  layout = "vertical",
}: BarChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveBar
        data={data}
        keys={keys}
        indexBy={indexBy}
        layout={layout}
        margin={{ top: 20, right: 20, bottom: 40, left: 50 }}
        padding={0.3}
        colors={["var(--accent-primary)", "var(--accent-secondary)", "var(--accent-hot)", "var(--accent-warm)"]}
        borderRadius={4}
        borderWidth={0}
        enableLabel={false}
        enableGridX={layout === "horizontal"}
        enableGridY={layout === "vertical"}
        gridYValues={5}
        theme={{
          background: "transparent",
          text: { fill: "var(--text-muted)", fontSize: 11 },
          grid: { line: { stroke: "rgba(255,255,255,0.05)" } },
          axis: {
            ticks: { text: { fill: "var(--text-muted)", fontSize: 11 } },
          },
          tooltip: {
            container: {
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              borderRadius: "6px",
              border: "1px solid rgba(255,255,255,0.1)",
              fontSize: 12,
            },
          },
        }}
        animate={true}
        motionConfig="gentle"
      />
    </div>
  );
}
```

Usage:
```tsx
<BarChart
  data={[
    { month: "Jan", sales: 120, returns: 15 },
    { month: "Feb", sales: 180, returns: 22 },
    { month: "Mar", sales: 150, returns: 18 },
  ]}
  keys={["sales", "returns"]}
  indexBy="month"
/>
```

---

## Component: Nivo Pie Chart

```tsx
import { ResponsivePie } from "@nivo/pie";

interface PieDataPoint {
  id: string;
  label: string;
  value: number;
  color?: string;
}

interface PieChartProps {
  data: PieDataPoint[];
  height?: number;
  donut?: boolean;
}

export function PieChart({ data, height = 300, donut = true }: PieChartProps) {
  return (
    <div style={{ height }}>
      <ResponsivePie
        data={data}
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        innerRadius={donut ? 0.6 : 0}
        padAngle={1}
        cornerRadius={4}
        activeOuterRadiusOffset={4}
        colors={["var(--accent-primary)", "var(--accent-secondary)", "var(--accent-hot)", "var(--accent-warm)", "var(--accent-success)"]}
        borderWidth={0}
        enableArcLabels={false}
        enableArcLinkLabels={true}
        arcLinkLabelsSkipAngle={10}
        arcLinkLabelsTextColor="var(--text-secondary)"
        arcLinkLabelsThickness={1}
        arcLinkLabelsColor="rgba(255,255,255,0.15)"
        theme={{
          background: "transparent",
          text: { fill: "var(--text-muted)", fontSize: 11 },
          tooltip: {
            container: {
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              borderRadius: "6px",
              border: "1px solid rgba(255,255,255,0.1)",
              fontSize: 12,
            },
          },
        }}
        animate={true}
        motionConfig="gentle"
      />
    </div>
  );
}
```

Usage:
```tsx
<PieChart
  data={[
    { id: "desktop", label: "Desktop", value: 65 },
    { id: "mobile", label: "Mobile", value: 28 },
    { id: "tablet", label: "Tablet", value: 7 },
  ]}
  donut={true}
/>
```

---

## Component: Modal / Dialog

```tsx
import { useEffect, useRef, useCallback } from "react";

import { X } from "lucide-react";

import { cn } from "../lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizes = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
};

export function Modal({
  open,
  onClose,
  title,
  children,
  size = "md",
  className,
}: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (open) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-[fadeIn_150ms_ease-out]"
    >
      <div
        className={cn(
          "w-full rounded-md border border-white/10 bg-[var(--bg-card)] p-6 shadow-2xl",
          "animate-[slideUp_200ms_cubic-bezier(0.4,0,0.2,1)]",
          sizes[size],
          className
        )}
      >
        {/* Header */}
        {title && (
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold text-[var(--text-primary)]">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--text-muted)] transition-colors hover:bg-white/5 hover:text-[var(--text-primary)]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Content */}
        {children}
      </div>
    </div>
  );
}
```

Add these keyframes to your CSS:
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(1rem); }
  to { opacity: 1; transform: translateY(0); }
}
```

Usage:
```tsx
const [open, setOpen] = useState(false);

<Modal open={open} onClose={() => setOpen(false)} title="Confirm Action" size="sm">
  <p className="mb-4 text-sm text-[var(--text-secondary)]">
    Are you sure you want to proceed?
  </p>
  <div className="flex justify-end gap-2">
    <button
      onClick={() => setOpen(false)}
      className="rounded-md px-4 py-2 text-sm text-[var(--text-muted)] hover:bg-white/5"
    >
      Cancel
    </button>
    <button
      onClick={handleConfirm}
      className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-[var(--bg-page)] hover:brightness-110"
    >
      Confirm
    </button>
  </div>
</Modal>
```

---

## NPM Dependencies

Core packages for this design system:

```bash
npm install clsx tailwind-merge class-variance-authority lucide-react @phosphor-icons/react @nivo/core @nivo/line @nivo/bar @nivo/pie
```
