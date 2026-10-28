import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import {
  Calculator,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  Scale,
  ShieldCheck,
  TrendingUp,
  DollarSign,
  Percent,
} from 'lucide-react'
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts'
import { formatCurrency, formatNumber, formatPercent } from '@/lib/formatters'
import type { OptimizationObjective, OptimizationRequest } from '@/types/api'

export const PriceOptimizerPage: React.FC = () => {
  const [productId, setProductId] = useState('22423')
  const [currentPrice, setCurrentPrice] = useState(12.75)
  const [priceMin, setPriceMin] = useState(9.5)
  const [priceMax, setPriceMax] = useState(16.5)
  const [candidatesCount, setCandidatesCount] = useState(21)
  const [objective, setObjective] = useState<OptimizationObjective>('revenue')
  const [unitCost, setUnitCost] = useState<number | undefined>(6.5)
  const [minMargin, setMinMargin] = useState<number | undefined>(0.2)
  const [maxChangePct, setMaxChangePct] = useState<number | undefined>(0.25)
  const [isApproved, setIsApproved] = useState(false)

  const optimizeMutation = useMutation({
    mutationFn: (req: OptimizationRequest) => api.optimizePricing(req),
    onSuccess: () => {
      setIsApproved(false)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    optimizeMutation.mutate({
      product_id: productId,
      current_price: Number(currentPrice),
      price_min: Number(priceMin),
      price_max: Number(priceMax),
      num_candidates: Number(candidatesCount),
      objective,
      unit_cost: objective === 'profit' || unitCost ? Number(unitCost) : undefined,
      min_gross_margin: minMargin !== undefined ? Number(minMargin) : undefined,
      max_price_change_pct: maxChangePct !== undefined ? Number(maxChangePct) : undefined,
      currency: 'GBP',
      demand_context: {
        base_demand: 50.0,
        elasticity: -1.5,
      },
    })
  }

  const result = optimizeMutation.data

  // Chart data from evaluated candidates
  const chartData = (result?.candidates || []).map((c) => ({
    price: `£${c.candidate_price.toFixed(2)}`,
    rawPrice: c.candidate_price,
    revenue: c.expected_revenue,
    profit: c.estimated_profit || 0,
    demand: c.predicted_demand,
    isRecommended: c.candidate_price === result?.recommended_price,
    isFeasible: c.is_feasible,
  }))

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-300 mb-2">
          <Calculator className="size-3.5 text-emerald-400" />
          <span>Constrained Optimization Engine</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
          Price Scenario Evaluation & Guardrails
        </h1>
        <p className="text-sm text-zinc-400 max-w-2xl mt-1">
          Explore discrete price candidates, evaluate expected revenue and gross margin floors, and review
          model extrapolation guardrails with human supervision.
        </p>
      </div>

      {/* Main Grid: Form Controls + Optimization Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Column */}
        <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Sliders className="size-4.5 text-brand-400" />
              Optimization Controls
            </h3>
            <span className="text-[10px] text-zinc-400 font-mono">Bound Check</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-zinc-400 font-medium mb-1">Target Product SKU</label>
              <input
                type="text"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Current Price (£)</label>
                <input
                  type="number"
                  step="0.05"
                  value={currentPrice}
                  onChange={(e) => setCurrentPrice(parseFloat(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Objective</label>
                <select
                  value={objective}
                  onChange={(e) => setObjective(e.target.value as OptimizationObjective)}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-sans"
                >
                  <option value="revenue">Maximize Revenue</option>
                  <option value="profit">Maximize Profit</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Min Price (£)</label>
                <input
                  type="number"
                  step="0.05"
                  value={priceMin}
                  onChange={(e) => setPriceMin(parseFloat(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Max Price (£)</label>
                <input
                  type="number"
                  step="0.05"
                  value={priceMax}
                  onChange={(e) => setPriceMax(parseFloat(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Unit Cost (£ COGS)</label>
                <input
                  type="number"
                  step="0.05"
                  value={unitCost || ''}
                  onChange={(e) => setUnitCost(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  placeholder="Required for profit"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Min Margin Floor</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="0.95"
                  value={minMargin ?? ''}
                  onChange={(e) => setMinMargin(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  placeholder="e.g. 0.20 (20%)"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-zinc-400 font-medium mb-1">Max Price Change %</label>
                <input
                  type="number"
                  step="0.05"
                  value={maxChangePct ?? ''}
                  onChange={(e) => setMaxChangePct(e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                  placeholder="e.g. 0.25 (25%)"
                />
              </div>

              <div>
                <label className="block text-zinc-400 font-medium mb-1">Grid Candidates</label>
                <input
                  type="number"
                  min="3"
                  max="51"
                  value={candidatesCount}
                  onChange={(e) => setCandidatesCount(parseInt(e.target.value))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-brand-500 font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={optimizeMutation.isPending}
              className="w-full rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium py-2.5 px-4 shadow-lg shadow-brand-500/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-4"
            >
              {optimizeMutation.isPending ? 'Optimizing...' : 'Run Pricing Optimization'}
            </button>
          </form>

          {/* Safety Notice */}
          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 text-[11px] text-zinc-400 space-y-1">
            <div className="flex items-center gap-1.5 text-zinc-300 font-medium">
              <ShieldCheck className="size-3.5 text-emerald-400" />
              Decision-Support Protocol
            </div>
            <p className="leading-relaxed">
              Optimization results require explicit human review. Automatic store price publication is prohibited.
            </p>
          </div>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <>
              {/* Recommendation Banner */}
              <div className="rounded-2xl border border-brand-500/30 bg-gradient-to-r from-brand-950/40 via-[#121217] to-[#121217] p-6 space-y-4 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs font-mono uppercase text-brand-400 tracking-wider">
                      Optimal Candidate Recommendation
                    </span>
                    <div className="flex items-baseline gap-3 mt-1">
                      <span className="text-4xl font-bold text-white font-mono">
                        {formatCurrency(result.recommended_price, result.currency)}
                      </span>
                      <span className="text-sm font-semibold text-emerald-400">
                        {result.recommended_price && currentPrice
                          ? `${(((result.recommended_price - currentPrice) / currentPrice) * 100).toFixed(1)}% vs current`
                          : ''}
                      </span>
                    </div>
                  </div>

                  {/* Human Approval Action */}
                  <div className="flex items-center gap-2">
                    {isApproved ? (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3.5 py-1.5 text-xs text-emerald-300 font-medium">
                        <CheckCircle2 className="size-4" />
                        Human Approved (Decision Recorded)
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setIsApproved(true)}
                        className="rounded-xl border border-white/20 bg-white/5 hover:bg-emerald-500/20 hover:border-emerald-500/40 hover:text-emerald-300 text-white px-4 py-2 text-xs font-semibold transition-all flex items-center gap-1.5"
                      >
                        <CheckCircle2 className="size-4 text-emerald-400" />
                        Approve Recommendation
                      </button>
                    )}
                  </div>
                </div>

                {/* Stat Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-[10px] text-zinc-400 uppercase font-mono">Expected Demand</span>
                    <div className="text-lg font-bold text-white font-mono mt-0.5">
                      {formatNumber(result.predicted_demand, 1)} units
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-[10px] text-zinc-400 uppercase font-mono">Expected Revenue</span>
                    <div className="text-lg font-bold text-brand-400 font-mono mt-0.5">
                      {formatCurrency(result.expected_revenue, result.currency)}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-[10px] text-zinc-400 uppercase font-mono">Estimated Profit</span>
                    <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">
                      {result.estimated_profit ? formatCurrency(result.estimated_profit, result.currency) : 'N/A'}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-[10px] text-zinc-400 uppercase font-mono">Gross Margin</span>
                    <div className="text-lg font-bold text-white font-mono mt-0.5">
                      {result.gross_margin ? formatPercent(result.gross_margin) : 'N/A'}
                    </div>
                  </div>
                </div>

                <p className="text-xs text-zinc-300 leading-relaxed border-t border-white/5 pt-3">
                  {result.explanation}
                </p>
              </div>

              {/* Candidate Curve Chart */}
              <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-white">
                    Candidate Price vs. Expected Financial Outcome
                  </h3>
                  <span className="text-xs text-zinc-400 font-mono">
                    Feasible: {result.feasible_candidates}/{result.total_candidates}
                  </span>
                </div>

                <div className="h-64 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis
                        dataKey="price"
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
                      <Bar dataKey="revenue" fill="#3b82f6" name="Expected Revenue (£)" opacity={0.8} />
                      {objective === 'profit' && (
                        <Line
                          type="monotone"
                          dataKey="profit"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={{ r: 3 }}
                          name="Estimated Profit (£)"
                        />
                      )}
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Candidates Detail Table */}
              <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
                <h3 className="text-base font-semibold text-white">
                  Discrete Candidate Grid Evaluations
                </h3>

                <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
                      <tr>
                        <th className="py-2.5 px-3 font-medium">Candidate Price</th>
                        <th className="py-2.5 px-3 font-medium">Predicted Demand</th>
                        <th className="py-2.5 px-3 font-medium">Revenue</th>
                        <th className="py-2.5 px-3 font-medium">Profit</th>
                        <th className="py-2.5 px-3 font-medium">Margin</th>
                        <th className="py-2.5 px-3 font-medium">Feasibility</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                      {result.candidates.map((c, idx) => {
                        const isRecommended = c.candidate_price === result.recommended_price
                        return (
                          <tr
                            key={idx}
                            className={`hover:bg-white/[0.02] ${
                              isRecommended ? 'bg-brand-500/10 font-bold' : ''
                            }`}
                          >
                            <td className="py-2 px-3 text-white">
                              {formatCurrency(c.candidate_price, result.currency)}
                              {isRecommended && (
                                <span className="ml-2 text-[10px] text-brand-400 font-sans font-semibold">
                                  (Selected)
                                </span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-zinc-300">
                              {c.predicted_demand.toFixed(1)}
                            </td>
                            <td className="py-2 px-3 text-brand-300">
                              {formatCurrency(c.expected_revenue, result.currency)}
                            </td>
                            <td className="py-2 px-3 text-emerald-300">
                              {c.estimated_profit ? formatCurrency(c.estimated_profit, result.currency) : '-'}
                            </td>
                            <td className="py-2 px-3 text-zinc-400">
                              {c.gross_margin ? formatPercent(c.gross_margin) : '-'}
                            </td>
                            <td className="py-2 px-3">
                              {c.is_feasible ? (
                                <span className="text-emerald-400">Feasible</span>
                              ) : (
                                <span className="text-rose-400" title={c.rejection_reasons.join(', ')}>
                                  Violated
                                </span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-[#121217] p-12 text-center text-zinc-400 flex flex-col items-center justify-center space-y-3">
              <Calculator className="size-12 text-zinc-600 stroke-1" />
              <div className="space-y-1">
                <h3 className="text-base font-semibold text-white">Ready for Optimization</h3>
                <p className="text-xs text-zinc-400 max-w-sm">
                  Configure target SKU parameters and bounds on the left, then click "Run Pricing Optimization".
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
