import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import {
  BrainCircuit,
  MessageSquare,
  TrendingDown,
  TrendingUp,
  Sparkles,
  ShoppingBag,
  Clock,
  CheckCircle,
  Tag,
  ShieldCheck,
} from 'lucide-react'
import { formatCurrency, formatDateTime } from '@/lib/formatters'

export const MarketIntelligencePage: React.FC = () => {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['market-intelligence-summary'],
    queryFn: () => api.getMarketIntelligenceSummary(),
  })

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-purple-500/30 bg-purple-500/10 px-2.5 py-0.5 text-xs font-medium text-purple-300 mb-2">
          <BrainCircuit className="size-3.5 text-purple-400" />
          <span>Agentic Market Intelligence</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
          Customer Sentiment & Competitor Tracking
        </h1>
        <p className="text-sm text-zinc-400 max-w-2xl mt-1">
          Automated extraction of customer perception aspects (quality, shipping, pricing) and
          authorized competitor price observation feeds.
        </p>
      </div>

      {/* Overview Stat Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-1">
          <span className="text-xs font-mono uppercase text-zinc-400">Reviews Analyzed</span>
          <div className="text-2xl font-bold text-white font-mono">
            {summary?.total_reviews_analyzed || 0}
          </div>
          <span className="text-[11px] text-emerald-400 font-mono">Rule-Based NLP</span>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-1">
          <span className="text-xs font-mono uppercase text-zinc-400">Positive Sentiment</span>
          <div className="text-2xl font-bold text-emerald-400 font-mono">
            {summary?.sentiment_breakdown?.positive || 0}
          </div>
          <span className="text-[11px] text-zinc-400 font-mono">60% of total volume</span>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-1">
          <span className="text-xs font-mono uppercase text-zinc-400">Negative Signals</span>
          <div className="text-2xl font-bold text-rose-400 font-mono">
            {summary?.sentiment_breakdown?.negative || 0}
          </div>
          <span className="text-[11px] text-zinc-400 font-mono">Shipping & packaging</span>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#121217] p-5 space-y-1">
          <span className="text-xs font-mono uppercase text-zinc-400">Competitors Tracked</span>
          <div className="text-2xl font-bold text-brand-400 font-mono">
            {summary?.competitors_monitored?.length || 0}
          </div>
          <span className="text-[11px] text-zinc-400 font-mono">Active Price Feeds</span>
        </div>
      </div>

      {/* Grid: Extracted Aspects & Competitor Observations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Perception Aspects */}
        <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Sparkles className="size-4 text-purple-400" />
              Perception Aspects
            </h3>
            <span className="text-xs font-mono text-zinc-400">Mentions</span>
          </div>

          <div className="space-y-3">
            {summary?.top_aspects?.map((aspect) => (
              <div
                key={aspect.aspect}
                className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5 text-xs"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`size-2 rounded-full ${
                      aspect.sentiment === 'positive' ? 'bg-emerald-400' : 'bg-rose-400'
                    }`}
                  />
                  <span className="font-medium text-zinc-200 capitalize">
                    {aspect.aspect.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded ${
                      aspect.sentiment === 'positive'
                        ? 'bg-emerald-500/10 text-emerald-300'
                        : 'bg-rose-500/10 text-rose-300'
                    }`}
                  >
                    {aspect.sentiment}
                  </span>
                  <span className="font-mono text-zinc-400 font-bold">{aspect.mentions}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/20 text-[11px] text-purple-200 leading-relaxed">
            Perception signals help identify willingness-to-pay elasticity shifts without subjective bias.
          </div>
        </div>

        {/* Competitor Price Feeds */}
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <ShoppingBag className="size-4 text-brand-400" />
                Competitor Selling Price Observations
              </h3>
              <p className="text-xs text-zinc-400">
                Authorized, traceable price observations for benchmark SKUs
              </p>
            </div>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
              Fresh Signals
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Product SKU</th>
                  <th className="py-2.5 px-4 font-medium">Competitor Merchant</th>
                  <th className="py-2.5 px-4 font-medium">Observed Price</th>
                  <th className="py-2.5 px-4 font-medium">Source Type</th>
                  <th className="py-2.5 px-4 font-medium">Observed Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                {summary?.recent_competitor_observations?.map((comp, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.02]">
                    <td className="py-2.5 px-4 text-zinc-200 font-semibold">{comp.product_id}</td>
                    <td className="py-2.5 px-4 text-white font-sans">{comp.competitor_name}</td>
                    <td className="py-2.5 px-4 text-brand-400 font-bold text-sm">
                      {formatCurrency(comp.observed_price, comp.currency)}
                    </td>
                    <td className="py-2.5 px-4 text-zinc-400 font-sans capitalize">
                      {comp.source_type.replace('_', ' ')}
                    </td>
                    <td className="py-2.5 px-4 text-zinc-400">{comp.observed_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Customer Review Deep-Dive Cards */}
      <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <MessageSquare className="size-4 text-emerald-400" />
              Analyzed Customer Review Records
            </h3>
            <p className="text-xs text-zinc-400">
              Traceable extractions with grounding excerpts and sentiment scores (-1.0 to +1.0)
            </p>
          </div>
          <span className="text-xs font-mono text-zinc-400">Grounded Extractions</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {summary?.recent_reviews?.map((rev) => {
            const isPos = rev.sentiment_label === 'positive'
            return (
              <div
                key={rev.review_id}
                className="rounded-xl border border-white/5 bg-white/[0.02] p-4 flex flex-col justify-between space-y-3 text-xs"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-zinc-400 text-[11px]">{rev.review_id}</span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase ${
                        isPos
                          ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                      }`}
                    >
                      {rev.sentiment_label} ({rev.sentiment_score > 0 ? `+${rev.sentiment_score}` : rev.sentiment_score})
                    </span>
                  </div>

                  <p className="text-zinc-200 leading-relaxed italic text-[11px]">
                    "{rev.summary}"
                  </p>
                </div>

                <div className="space-y-2 pt-2 border-t border-white/5">
                  <div className="flex flex-wrap gap-1">
                    {rev.aspects.map((aspect) => (
                      <span
                        key={aspect}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-zinc-300"
                      >
                        #{aspect}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono">
                    <span>SKU: {rev.product_id}</span>
                    <span>Rating: {rev.rating || 5}.0 / 5.0</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
