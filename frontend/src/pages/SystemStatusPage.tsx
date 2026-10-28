import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, API_BASE_URL } from '@/lib/api-client'
import {
  Activity,
  Server,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Database,
  Cpu,
  Layers,
  Code2,
} from 'lucide-react'
import { formatDateTime } from '@/lib/formatters'

export const SystemStatusPage: React.FC = () => {
  const { data: status, isLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.getSystemStatus(),
    refetchInterval: 10000,
  })

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
  })

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Page Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-300 mb-2">
          <Activity className="size-3.5 text-emerald-400" />
          <span>Operational Diagnostics</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
          System Status & Platform Subsystems
        </h1>
        <p className="text-sm text-zinc-400 max-w-2xl mt-1">
          Real-time health verification for FastAPI backend services, local data persistence, trained forecasting
          models, and experiment tracking registries.
        </p>
      </div>

      {/* Main Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-2">
          <span className="text-xs font-mono uppercase text-zinc-400">Backend API</span>
          <div className="flex items-center gap-2 text-xl font-bold text-white">
            <span className="size-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>{health?.status === 'healthy' ? 'Operational' : 'Connecting'}</span>
          </div>
          <p className="text-xs text-zinc-400 font-mono">
            {API_BASE_URL}
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-2">
          <span className="text-xs font-mono uppercase text-zinc-400">Environment & Version</span>
          <div className="text-xl font-bold text-white font-mono">
            {status?.backend_version || '0.1.0'} ({status?.environment || 'local'})
          </div>
          <p className="text-xs text-zinc-400 font-mono">
            FastAPI + Uvicorn + React 19
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-2">
          <span className="text-xs font-mono uppercase text-zinc-400">Last Synced Timestamp</span>
          <div className="text-sm font-bold text-white font-mono mt-1">
            {formatDateTime(status?.timestamp_utc)}
          </div>
          <span className="text-[11px] text-emerald-400 font-mono">Heartbeat OK</span>
        </div>
      </div>

      {/* Subsystems Matrix */}
      <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Server className="size-4.5 text-brand-400" />
            Integrated Subsystems & Feature Flags
          </h2>
          <span className="text-xs font-mono text-zinc-400">Active Modules</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {status?.modules?.map((m) => (
            <div
              key={m.name}
              className="rounded-xl border border-white/5 bg-white/[0.02] p-4 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white capitalize">
                  {m.name.replace('_', ' ')}
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                    m.available
                      ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                      : 'bg-zinc-800 text-zinc-400'
                  }`}
                >
                  {m.status_label}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                {m.details || 'Module operational.'}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* API Endpoint Documentation Overview */}
      <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Code2 className="size-4.5 text-indigo-400" />
            Verified API Routes & Endpoints
          </h3>
          <span className="text-xs font-mono text-zinc-400">REST v1</span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
              <tr>
                <th className="py-2.5 px-4 font-medium">HTTP Method</th>
                <th className="py-2.5 px-4 font-medium">Path</th>
                <th className="py-2.5 px-4 font-medium">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-[11px]">
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/health</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Liveness probe</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/system/status</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Subsystem diagnostics</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/datasets</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Registry manifest & file checksums</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/datasets/&#123;id&#125;/profile</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Tabular statistical profile</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/forecasts/models</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Evaluated models & test metrics</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-brand-400 font-bold">POST</td>
                <td className="py-2 px-4 text-white">/api/v1/forecasts</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">On-demand demand inference</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/market-intelligence/summary</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Customer sentiment & competitor tracking</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-brand-400 font-bold">POST</td>
                <td className="py-2 px-4 text-white">/api/v1/pricing/optimize</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Constrained price optimization</td>
              </tr>
              <tr className="hover:bg-white/[0.02]">
                <td className="py-2 px-4 text-emerald-400 font-bold">GET</td>
                <td className="py-2 px-4 text-white">/api/v1/experiments</td>
                <td className="py-2 px-4 text-zinc-400 font-sans">Phase 5 feature ablation study results</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
