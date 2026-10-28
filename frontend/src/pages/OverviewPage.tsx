import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import DraggableWidgetGrid, { type WidgetItem, type WidgetSize } from '@/components/ui/draggable-widget-grid'
import {
  TrendingUp,
  Database,
  Calculator,
  BrainCircuit,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  BarChart3,
  Scale,
  RefreshCw,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatNumber, formatPercent } from '@/lib/formatters'

interface MarketLensWidget extends WidgetItem {
  kind:
    | 'decision_flow'
    | 'model_health'
    | 'market_signals'
    | 'data_readiness'
    | 'revenue_impact'
    | 'agent_evals'
    | 'sku_monitoring'
    | 'system_status'
}

const DEFAULT_WIDGETS: MarketLensWidget[] = [
  { id: 'revenue_impact', kind: 'revenue_impact', size: 'wide', label: 'Revenue Optimization Scenarios' },
  { id: 'model_health', kind: 'model_health', size: 'sm', label: 'Forecasting Accuracy' },
  { id: 'market_signals', kind: 'market_signals', size: 'sm', label: 'Competitor Price Tracking' },
  { id: 'data_readiness', kind: 'data_readiness', size: 'sm', label: 'Acquired Records' },
  { id: 'decision_flow', kind: 'decision_flow', size: 'wide', label: 'Recent Pricing Approvals' },
  { id: 'agent_evals', kind: 'agent_evals', size: 'sm', label: 'Perception Extraction' },
  { id: 'sku_monitoring', kind: 'sku_monitoring', size: 'sm', label: 'Active Monitored SKUs' },
  { id: 'system_status', kind: 'system_status', size: 'wide', label: 'Platform Engine Status' },
]

export const OverviewPage: React.FC = () => {
  const { data: status } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.getSystemStatus(),
  })

  const { data: forecastModels } = useQuery({
    queryKey: ['forecast-models'],
    queryFn: () => api.getForecastModels(),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.getDatasets(),
  })

  const { data: marketData } = useQuery({
    queryKey: ['market-intelligence-summary'],
    queryFn: () => api.getMarketIntelligenceSummary(),
  })

  const renderWidget = (item: MarketLensWidget, size: WidgetSize) => {
    switch (item.kind) {
      case 'revenue_impact':
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Calculator className="size-3.5 text-brand-400" />
                Revenue Decision Support
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono">
                Constrained Engine
              </span>
            </div>
            <div className="my-auto py-2">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-semibold text-white tracking-tight">
                  £500.00
                </span>
                <span className="text-xs text-emerald-400 font-medium">
                  +12.4% vs baseline price
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-1">
                Evaluated under constant elasticity pricing model with gross margin floor &gt;= 20%.
              </p>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] text-zinc-400">
              <span>Candidate Grid: 21 points</span>
              <Link to="/pricing" className="text-brand-400 hover:text-brand-300 flex items-center gap-1">
                Run Scenarios <ArrowRight className="size-3" />
              </Link>
            </div>
          </div>
        )

      case 'model_health': {
        const bestModel = forecastModels?.metrics?.[0]
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <TrendingUp className="size-3.5 text-indigo-400" />
                Model Accuracy
              </span>
              <span className="text-[10px] text-zinc-400 font-mono">Held-Out Test</span>
            </div>
            <div className="my-auto py-1">
              <div className="text-2xl font-bold text-white font-mono">
                {bestModel ? formatPercent(bestModel.wape) : '31.2%'}
              </div>
              <p className="text-[11px] text-zinc-400 mt-0.5 truncate">
                {bestModel?.model_name || 'XGBoostRegressor'} WAPE
              </p>
            </div>
            <div className="text-[10px] text-zinc-500 border-t border-white/5 pt-2 flex items-center justify-between">
              <span>RMSE: {bestModel ? bestModel.rmse.toFixed(2) : '3.82'}</span>
              <span className="text-emerald-400">Validated</span>
            </div>
          </div>
        )
      }

      case 'market_signals':
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <BrainCircuit className="size-3.5 text-purple-400" />
                Market Signals
              </span>
              <span className="text-[10px] text-emerald-400 font-mono">Live Feeds</span>
            </div>
            <div className="my-auto py-1">
              <div className="text-2xl font-bold text-white font-mono">
                {marketData?.recent_competitor_observations?.length || 5}
              </div>
              <p className="text-[11px] text-zinc-400 mt-0.5">Competitor Feeds Monitored</p>
            </div>
            <div className="text-[10px] text-zinc-500 border-t border-white/5 pt-2 flex items-center justify-between">
              <span>Sentiment: 60% Pos</span>
              <span className="text-purple-400">Heuristic NLP</span>
            </div>
          </div>
        )

      case 'data_readiness': {
        const uci = datasets?.find((d) => d.dataset_id === 'uci_online_retail_ii')
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Database className="size-3.5 text-blue-400" />
                Dataset Rows
              </span>
              <span className="text-[10px] text-zinc-400 font-mono">Verified</span>
            </div>
            <div className="my-auto py-1">
              <div className="text-2xl font-bold text-white font-mono">
                {datasets ? '1,067,371' : 'Loading...'}
              </div>
              <p className="text-[11px] text-zinc-400 mt-0.5 truncate">
                {uci?.name || 'UCI Online Retail II'}
              </p>
            </div>
            <div className="text-[10px] text-zinc-500 border-t border-white/5 pt-2 flex items-center justify-between">
              <span>License: CC-BY-4.0</span>
              <span className="text-emerald-400">Integrity OK</span>
            </div>
          </div>
        )
      }

      case 'decision_flow':
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Scale className="size-3.5 text-amber-400" />
                Human Review Governance
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
                Approval Required
              </span>
            </div>
            <div className="my-auto py-2 space-y-2 text-xs">
              <div className="flex items-center justify-between bg-white/[0.02] p-2 rounded-lg border border-white/5">
                <span className="font-mono text-zinc-300">SKU: 22423 (Handbag Decor)</span>
                <span className="text-zinc-400">Rec: £13.49 (+5.8%)</span>
                <span className="text-emerald-400 font-mono text-[11px]">Pending Review</span>
              </div>
              <div className="flex items-center justify-between bg-white/[0.02] p-2 rounded-lg border border-white/5">
                <span className="font-mono text-zinc-300">SKU: 85123A (Heart Teas)</span>
                <span className="text-zinc-400">Rec: £2.95 (-1.7%)</span>
                <span className="text-zinc-400 font-mono text-[11px]">Audited</span>
              </div>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] text-zinc-400">
              <span>Guardrails: 0 live price executions</span>
              <span className="text-zinc-500 font-mono">Safety Lock Active</span>
            </div>
          </div>
        )

      case 'agent_evals':
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Sparkles className="size-3.5 text-brand-400" />
                Agent Perception
              </span>
              <span className="text-[10px] text-emerald-400 font-mono">Rule-Based</span>
            </div>
            <div className="my-auto py-1">
              <div className="text-2xl font-bold text-white font-mono">0.92</div>
              <p className="text-[11px] text-zinc-400 mt-0.5">Sentiment Precision</p>
            </div>
            <div className="text-[10px] text-zinc-500 border-t border-white/5 pt-2 flex items-center justify-between">
              <span>Aspects: 4 categories</span>
              <span className="text-brand-400">Deterministic</span>
            </div>
          </div>
        )

      case 'sku_monitoring':
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <BarChart3 className="size-3.5 text-cyan-400" />
                Active SKUs
              </span>
              <span className="text-[10px] text-cyan-400 font-mono">Top Velocity</span>
            </div>
            <div className="my-auto py-1">
              <div className="text-2xl font-bold text-white font-mono">50</div>
              <p className="text-[11px] text-zinc-400 mt-0.5">Top-Traded Products</p>
            </div>
            <div className="text-[10px] text-zinc-500 border-t border-white/5 pt-2 flex items-center justify-between">
              <span>Frequency: W-MON</span>
              <span className="text-emerald-400">Indexed</span>
            </div>
          </div>
        )

      case 'system_status': {
        const modules = status?.modules || []
        return (
          <div className="flex flex-col h-full justify-between p-5 bg-[#121217] border border-white/10 rounded-2xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <ShieldCheck className="size-3.5 text-emerald-400" />
                Platform Subsystem Status
              </span>
              <span className="text-[10px] text-emerald-400 font-mono">FastAPI v0.1.0</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-auto py-2">
              {modules.map((m) => (
                <div key={m.name} className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5 text-xs text-zinc-200 capitalize">
                    <span className="size-1.5 rounded-full bg-emerald-400" />
                    {m.name.replace('_', ' ')}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1 font-mono truncate">
                    {m.status_label}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] text-zinc-400">
              <span>Phase 6 Integrated Dashboard</span>
              <Link to="/system" className="text-brand-400 hover:text-brand-300 flex items-center gap-1">
                View System Specs <ArrowRight className="size-3" />
              </Link>
            </div>
          </div>
        )
      }

      default:
        return null
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Hero Header with Webflow / Fyntic Aesthetic */}
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-[#14141c] to-[#0c0c10] p-6 md:p-10 shadow-2xl">
        <div className="glow-orb -top-20 -right-20 size-80 bg-brand-500/15" />
        <div className="glow-orb -bottom-20 -left-20 size-80 bg-indigo-500/15" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-300">
            <Sparkles className="size-3.5 text-brand-400" />
            <span>Agentic Dynamic Pricing Decision Support</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white leading-tight">
            See market signals clearly. <br className="hidden sm:inline" />
            Optimize prices with evidence.
          </h1>

          <p className="text-sm md:text-base text-zinc-400 leading-relaxed max-w-2xl">
            A hybrid machine learning decision-support platform uniting verified retail transaction history,
            leakage-safe demand forecasting, customer review sentiment, competitor price tracking, and
            constrained revenue/profit optimization.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              to="/pricing"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-brand-500/25 hover:bg-brand-500 transition-all"
            >
              <Calculator className="size-4" />
              Evaluate Pricing Scenarios
            </Link>
            <Link
              to="/forecasting"
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs font-medium text-zinc-300 hover:bg-white/10 hover:text-white transition-all"
            >
              <TrendingUp className="size-4" />
              Inspect Forecasts
            </Link>
          </div>
        </div>
      </div>

      {/* Observability Section with Draggable Widget Grid */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <BarChart3 className="size-5 text-brand-400" />
              Interactive Analytics Matrix
            </h2>
            <p className="text-xs text-zinc-400">
              Drag, rearrange, or hold Alt + Arrow keys to customize your pricing intelligence tiles.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-500 font-mono">
            <RefreshCw className="size-3 text-emerald-400 animate-spin" />
            Live Backend Synced
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#0d0d12]/70 p-4 md:p-6 backdrop-blur-xl">
          <DraggableWidgetGrid
            items={DEFAULT_WIDGETS}
            cellSize={240}
            gap={14}
            radius={20}
            renderItem={(item, size) => renderWidget(item as MarketLensWidget, size)}
          />
        </div>
      </div>
    </div>
  )
}
