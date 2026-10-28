import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Database,
  TrendingUp,
  BrainCircuit,
  Calculator,
  FlaskConical,
  Activity,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  onNavigateMobile?: () => void
}

const navItems = [
  { name: 'Overview', to: '/', icon: LayoutDashboard },
  { name: 'Data Explorer', to: '/data', icon: Database },
  { name: 'Demand Forecasting', to: '/forecasting', icon: TrendingUp },
  { name: 'Market Intelligence', to: '/market-intelligence', icon: BrainCircuit },
  { name: 'Price Optimizer', to: '/pricing', icon: Calculator },
  { name: 'Experiments', to: '/experiments', icon: FlaskConical },
  { name: 'System Status', to: '/system', icon: Activity },
]

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  onNavigateMobile,
}) => {
  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-white/10 bg-[#0d0d12]/95 backdrop-blur-xl transition-all duration-300 z-30 h-screen sticky top-0',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
        <NavLink
          to="/"
          className="flex items-center gap-3 overflow-hidden focus:outline-none"
          onClick={onNavigateMobile}
        >
          <div className="relative flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 via-brand-500 to-indigo-500 shadow-lg shadow-brand-500/25">
            <Sparkles className="size-5 text-white" />
            <span className="absolute -top-1 -right-1 size-2 rounded-full bg-emerald-400 ring-2 ring-[#0d0d12]" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-tight text-white flex items-center gap-1.5">
                MarketLens <span className="text-brand-400">AI</span>
              </span>
              <span className="text-[10px] tracking-wide text-zinc-400 uppercase font-mono">
                Pricing Intelligence
              </span>
            </div>
          )}
        </NavLink>

        <button
          type="button"
          onClick={onToggle}
          className="hidden md:flex size-7 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="size-4" /> : <ChevronLeft className="size-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigateMobile}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-medium transition-all group relative',
                  isActive
                    ? 'bg-brand-500/15 text-brand-300 border border-brand-500/30 shadow-[0_0_20px_-5px_rgba(59,130,246,0.4)]'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/[0.04]'
                )
              }
              title={collapsed ? item.name : undefined}
            >
              <Icon className="size-4.5 shrink-0 transition-transform group-hover:scale-110" />
              {!collapsed && <span className="truncate">{item.name}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Safety & Protocol Footer */}
      {!collapsed && (
        <div className="p-3 m-3 rounded-xl border border-white/5 bg-gradient-to-b from-white/[0.03] to-transparent">
          <div className="flex items-center gap-2 text-[11px] text-zinc-300 font-medium mb-1">
            <ShieldCheck className="size-4 text-emerald-400 shrink-0" />
            <span>Human-in-the-Loop</span>
          </div>
          <p className="text-[10px] text-zinc-500 leading-relaxed">
            Decision-support prototype. Live store execution is disabled by design.
          </p>
        </div>
      )}
    </aside>
  )
}
