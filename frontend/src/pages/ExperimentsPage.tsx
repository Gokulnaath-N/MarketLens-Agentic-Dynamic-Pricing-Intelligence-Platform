import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import {
  FlaskConical,
  TrendingDown,
  TrendingUp,
  Layers,
  Sparkles,
  CheckCircle2,
  FileText,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts'
import { formatNumber, formatPercent } from '@/lib/formatters'

export const ExperimentsPage: React.FC = () => {
  const { data: experiments, isLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => api.getExperiments(),
  })

  // Format chart data
  const chartData = (experiments || []).map((exp) => ({
    name: exp.ablation_type.replace('_', ' ').toUpperCase(),
    wape: exp.wape * 100,
    mae: exp.mae,
    rmse: exp.rmse,
    delta: exp.delta_wape_vs_baseline * 100,
  }))

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Page Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-teal-500/30 bg-teal-500/10 px-2.5 py-0.5 text-xs font-medium text-teal-300 mb-2">
          <FlaskConical className="size-3.5 text-teal-400" />
          <span>Research & Ablation Study</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
          Phase 5 Feature Ablation Experiments
        </h1>
        <p className="text-sm text-zinc-400 max-w-2xl mt-1">
          Evidence-based evaluation quantifying the marginal forecast accuracy impact of integrating customer review
          sentiment and competitor price signals relative to temporal baselines.
        </p>
      </div>

      {/* Comparison Chart */}
      <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-base font-semibold text-white">
              WAPE Comparison Across Experimental Arms (Lower is Better)
            </h2>
            <p className="text-xs text-zinc-400">
              Evaluated on unified held-out temporal test window with XGBoostRegressor
            </p>
          </div>
          <span className="text-xs font-mono text-zinc-400">Run: phase5_feature_ablation</span>
        </div>

        <div className="h-64 w-full pt-2">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="name"
                  stroke="#71717a"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                />
                <YAxis
                  stroke="#71717a"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  unit="%"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#18181b',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(value: any) => [`${Number(value).toFixed(2)}%`, 'WAPE']}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="wape" fill="#3b82f6" name="WAPE (%)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-zinc-500">
              No ablation experiment records found. Run Phase 5 ablation study from backend.
            </div>
          )}
        </div>
      </div>

      {/* Experiment Run Table */}
      <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Layers className="size-4.5 text-brand-400" />
            Four-Way Ablation Benchmark Matrix
          </h3>
          <span className="text-[11px] font-mono text-zinc-400">
            Sign convention: negative Δ = improvement
          </span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-zinc-400">Loading ablation metrics...</div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Ablation Arm</th>
                  <th className="py-2.5 px-4 font-medium">Feature Set</th>
                  <th className="py-2.5 px-4 font-medium">Features</th>
                  <th className="py-2.5 px-4 font-medium">WAPE</th>
                  <th className="py-2.5 px-4 font-medium">Δ vs Baseline</th>
                  <th className="py-2.5 px-4 font-medium">MAE</th>
                  <th className="py-2.5 px-4 font-medium">RMSE</th>
                  <th className="py-2.5 px-4 font-medium">R²</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                {experiments?.map((exp) => {
                  const isBaseline = exp.ablation_type === 'e0_baseline'
                  const deltaWape = exp.delta_wape_vs_baseline
                  return (
                    <tr key={exp.ablation_type} className="hover:bg-white/[0.02]">
                      <td className="py-2.5 px-4 text-white font-sans font-semibold">
                        {exp.ablation_type.toUpperCase()}
                      </td>
                      <td className="py-2.5 px-4 text-zinc-300 font-sans max-w-[200px] truncate">
                        {exp.description}
                      </td>
                      <td className="py-2.5 px-4 text-zinc-400">{exp.features_count}</td>
                      <td className="py-2.5 px-4 text-brand-400 font-bold">
                        {formatPercent(exp.wape)}
                      </td>
                      <td className="py-2.5 px-4">
                        {isBaseline ? (
                          <span className="text-zinc-500 font-sans">Reference</span>
                        ) : deltaWape < 0 ? (
                          <span className="text-emerald-400 font-bold">
                            {(deltaWape * 100).toFixed(2)}% (Better)
                          </span>
                        ) : (
                          <span className="text-rose-400">
                            +{(deltaWape * 100).toFixed(2)}%
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-zinc-300">{exp.mae.toFixed(4)}</td>
                      <td className="py-2.5 px-4 text-zinc-300">{exp.rmse.toFixed(4)}</td>
                      <td className="py-2.5 px-4 text-zinc-300">{exp.r2.toFixed(4)}</td>
                    </tr>
                  )
                })}
                {(!experiments || experiments.length === 0) && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-zinc-500">
                      No ablation experiments recorded. Run Phase 5 CLI:
                      <br />
                      <code className="text-brand-300 text-[10px] mt-1 inline-block">
                        python -m marketlens.cli forecast ablate --simulate-synthetic
                      </code>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
