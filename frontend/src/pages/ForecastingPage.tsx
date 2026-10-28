import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import {
  TrendingUp,
  Cpu,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts'
import { formatCurrency, formatNumber, formatPercent } from '@/lib/formatters'
import type { LiveForecastRequest, LiveForecastResponse } from '@/types/api'

export const ForecastingPage: React.FC = () => {
  const [sku, setSku] = useState('22423')
  const [candidatePrice, setCandidatePrice] = useState(12.75)
  const [horizonWeeks, setHorizonWeeks] = useState(1)
  const [elasticity, setElasticity] = useState(-1.5)
  const [baseDemand, setBaseDemand] = useState(50.0)

  // Load evaluated models & baseline metrics
  const { data: modelsData, isLoading: modelsLoading } = useQuery({
    queryKey: ['forecast-models'],
    queryFn: () => api.getForecastModels(),
  })

  // Live forecast mutation
  const forecastMutation = useMutation({
    mutationFn: (req: LiveForecastRequest) => api.computeLiveForecast(req),
  })

  const handleCompute = (e: React.FormEvent) => {
    e.preventDefault()
    forecastMutation.mutate({
      product_id: sku,
      candidate_price: Number(candidatePrice),
      horizon_weeks: Number(horizonWeeks),
      elasticity: Number(elasticity),
      base_demand: Number(baseDemand),
      reference_price: 12.75,
    })
  }

  // Prepare chart series from predictions preview
  const chartData = (modelsData?.predictions_preview || []).slice(0, 15).map((row, idx) => ({
    time: row.period_start || `W-${idx + 1}`,
    actual: row.units_sold !== undefined ? Number(row.units_sold) : null,
    predicted: row.prediction !== undefined ? Number(row.prediction) : null,
  }))

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Page Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-xs font-medium text-indigo-300 mb-2">
          <TrendingUp className="size-3.5 text-indigo-400" />
          <span>Demand Forecasting Engine</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
          Predictive Demand & Model Evaluation
        </h1>
        <p className="text-sm text-zinc-400 max-w-2xl mt-1">
          Chronologically trained demand forecasting models evaluated strictly on held-out temporal splits,
          protecting against future lookahead leakage.
        </p>
      </div>

      {/* Model Benchmark Cards */}
      <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Cpu className="size-4.5 text-brand-400" />
              Held-Out Test Benchmark Metrics
            </h2>
            <p className="text-xs text-zinc-400">
              Evaluation split: 70% Train, 15% Validation, 15% Test (W-MON Frequency)
            </p>
          </div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
            No Data Leakage
          </span>
        </div>

        {modelsLoading ? (
          <div className="p-8 text-center text-zinc-400">Loading model benchmarks...</div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Model Architecture</th>
                  <th className="py-2.5 px-4 font-medium">MAE</th>
                  <th className="py-2.5 px-4 font-medium">RMSE</th>
                  <th className="py-2.5 px-4 font-medium">WAPE</th>
                  <th className="py-2.5 px-4 font-medium">R² Score</th>
                  <th className="py-2.5 px-4 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                {modelsData?.metrics?.map((m) => (
                  <tr key={m.model_name} className="hover:bg-white/[0.02]">
                    <td className="py-2.5 px-4 font-sans font-medium text-white">
                      {m.model_name}
                    </td>
                    <td className="py-2.5 px-4 text-zinc-300">{m.mae.toFixed(4)}</td>
                    <td className="py-2.5 px-4 text-zinc-300">{m.rmse.toFixed(4)}</td>
                    <td className="py-2.5 px-4 text-brand-400 font-semibold">
                      {formatPercent(m.wape)}
                    </td>
                    <td className="py-2.5 px-4 text-zinc-300">{m.r2.toFixed(4)}</td>
                    <td className="py-2.5 px-4 text-emerald-400 font-sans">
                      <span className="inline-flex items-center gap-1">
                        <CheckCircle2 className="size-3" />
                        Evaluated
                      </span>
                    </td>
                  </tr>
                ))}
                {(!modelsData?.metrics || modelsData.metrics.length === 0) && (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-zinc-500">
                      No baseline models evaluated yet. Run forecast pipeline from backend CLI.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Grid: Actual vs Predicted Chart + Interactive Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recharts Time Series Visualization */}
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">
                Actual vs. Predicted Demand Series
              </h3>
              <p className="text-xs text-zinc-400">
                Weekly units sold on held-out test horizon
              </p>
            </div>
            <span className="text-[11px] font-mono text-zinc-400">Target: units_sold</span>
          </div>

          <div className="h-72 w-full pt-4">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="time"
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
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#18181b',
                      borderColor: 'rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#3b82f6' }}
                    name="Actual Demand"
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#10b981"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={{ r: 3, fill: '#10b981' }}
                    name="Model Predicted"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-zinc-500">
                Evaluation time-series preview not yet generated.
              </div>
            )}
          </div>
        </div>

        {/* Live Forecast Inference Simulator */}
        <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sliders className="size-4 text-brand-400" />
              On-Demand Inference
            </h3>
            <span className="text-[10px] text-zinc-400 font-mono">Live API</span>
          </div>

          <form onSubmit={handleCompute} className="space-y-3.5 text-xs">
            <div>
              <label className="block text-zinc-400 font-medium mb-1">Product SKU</label>
              <input
                type="text"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Candidate Price (£)</label>
                <input
                  type="number"
                  step="0.05"
                  value={candidatePrice}
                  onChange={(e) => setCandidatePrice(parseFloat(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Horizon (Weeks)</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={horizonWeeks}
                  onChange={(e) => setHorizonWeeks(parseInt(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Base Demand</label>
                <input
                  type="number"
                  step="1"
                  value={baseDemand}
                  onChange={(e) => setBaseDemand(parseFloat(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Elasticity (ε)</label>
                <input
                  type="number"
                  step="0.1"
                  max="-0.1"
                  value={elasticity}
                  onChange={(e) => setElasticity(parseFloat(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={forecastMutation.isPending}
              className="w-full rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium py-2 px-4 shadow-lg shadow-brand-500/20 transition-all disabled:opacity-50 flex items-center justify-center gap-1.5 mt-2"
            >
              {forecastMutation.isPending ? 'Simulating...' : 'Run Demand Inference'}
            </button>
          </form>

          {/* Inference Result Box */}
          {forecastMutation.data && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 space-y-2 mt-4">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-300">Expected Demand</span>
                <span className="font-mono text-white text-base font-bold">
                  {forecastMutation.data.predicted_demand} units
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-300">Expected Revenue</span>
                <span className="font-mono text-white text-base font-bold">
                  {formatCurrency(forecastMutation.data.expected_revenue)}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed pt-1 border-t border-emerald-500/20">
                {forecastMutation.data.explanation}
              </p>
            </div>
          )}

          {forecastMutation.isError && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 flex items-center gap-2">
              <AlertCircle className="size-4 shrink-0" />
              <span>{forecastMutation.error.message}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
