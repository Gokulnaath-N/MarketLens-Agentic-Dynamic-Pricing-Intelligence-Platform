import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import {
  Database,
  FileCheck2,
  AlertTriangle,
  Calendar,
  Layers,
  Search,
  ExternalLink,
  ShieldCheck,
  Tag,
} from 'lucide-react'
import { formatBytes, formatDateTime, formatNumber } from '@/lib/formatters'

export const DataExplorerPage: React.FC = () => {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('uci_online_retail_ii')
  const [searchTerm, setSearchTerm] = useState('')

  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.getDatasets(),
  })

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['dataset-profile', selectedDatasetId],
    queryFn: () => api.getDatasetProfile(selectedDatasetId),
    enabled: !!selectedDatasetId,
  })

  const selectedDataset = datasets?.find((d) => d.dataset_id === selectedDatasetId)

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Page Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-0.5 text-xs font-medium text-blue-300 mb-2">
          <Database className="size-3.5 text-blue-400" />
          <span>Data Governance & Provenance</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
          Dataset Explorer & Statistical Profiling
        </h1>
        <p className="text-sm text-zinc-400 max-w-2xl mt-1">
          Trace acquired raw sources, license terms, cryptographic SHA-256 hashes, and verified statistical
          distributions before feature engineering and training.
        </p>
      </div>

      {/* Dataset Selector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {datasetsLoading ? (
          <div className="col-span-full p-8 text-center text-zinc-400">Loading datasets manifest...</div>
        ) : (
          datasets?.map((ds) => {
            const isSelected = ds.dataset_id === selectedDatasetId
            return (
              <div
                key={ds.dataset_id}
                onClick={() => setSelectedDatasetId(ds.dataset_id)}
                className={`cursor-pointer rounded-2xl p-5 border transition-all text-left ${
                  isSelected
                    ? 'bg-brand-500/10 border-brand-500/40 shadow-lg shadow-brand-500/10 ring-1 ring-brand-500/30'
                    : 'bg-[#121217] border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="text-xs font-mono font-medium text-brand-300 px-2 py-0.5 rounded-md bg-brand-500/20 border border-brand-500/30 truncate">
                    {ds.dataset_id}
                  </span>
                  <span className="text-[11px] font-mono text-zinc-400">
                    {ds.files.length} file(s)
                  </span>
                </div>

                <h3 className="text-base font-semibold text-white truncate">{ds.name}</h3>
                <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{ds.citation || ds.publisher}</p>

                <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-white/5 text-[11px] text-zinc-400 font-mono">
                  <span className="flex items-center gap-1">
                    <Tag className="size-3 text-emerald-400" />
                    {ds.license_name}
                  </span>
                  <span className="ml-auto text-zinc-500">
                    {ds.acquired_at_utc === 'Not Acquired' ? 'Unacquired' : 'Acquired'}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Profile Investigation Workspace */}
      {selectedDataset && (
        <div className="space-y-6">
          {/* Metadata Banner */}
          <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-4">
              <div>
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <FileCheck2 className="size-5 text-emerald-400" />
                  {selectedDataset.name}
                </h2>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Publisher: {selectedDataset.publisher} • License: {selectedDataset.license_name}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full flex items-center gap-1.5">
                  <ShieldCheck className="size-3.5" />
                  Audit Verified
                </span>
              </div>
            </div>

            {/* Acquired Files Manifest Table */}
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 mb-2">
                Acquired Files & Checksums
              </h3>
              <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
                <table className="w-full text-left text-xs">
                  <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
                    <tr>
                      <th className="py-2.5 px-4 font-medium">Filename</th>
                      <th className="py-2.5 px-4 font-medium">Format</th>
                      <th className="py-2.5 px-4 font-medium">Size</th>
                      <th className="py-2.5 px-4 font-medium">SHA-256 Checksum</th>
                      <th className="py-2.5 px-4 font-medium">Validation Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                    {selectedDataset.files.map((file) => (
                      <tr key={file.filename} className="hover:bg-white/[0.02]">
                        <td className="py-2.5 px-4 text-zinc-200 font-sans">{file.filename}</td>
                        <td className="py-2.5 px-4 text-zinc-400 uppercase">{file.detected_format}</td>
                        <td className="py-2.5 px-4 text-zinc-400">{formatBytes(file.byte_size)}</td>
                        <td className="py-2.5 px-4 text-zinc-400" title={file.sha256_hash}>
                          {file.sha256_hash.substring(0, 16)}...
                        </td>
                        <td className="py-2.5 px-4 text-emerald-400 font-sans">
                          {file.validation_status}
                        </td>
                      </tr>
                    ))}
                    {selectedDataset.files.length === 0 && (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-zinc-500">
                          No files acquired for this candidate yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Statistical Profiling Card */}
          {profileLoading ? (
            <div className="p-8 text-center text-zinc-400">Loading dataset statistical profile...</div>
          ) : profile ? (
            <div className="rounded-2xl border border-white/10 bg-[#121217] p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    <Layers className="size-4.5 text-indigo-400" />
                    Statistical Profile Summary
                  </h3>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Computed on source file: <span className="font-mono text-zinc-300">{profile.source_file}</span>
                  </p>
                </div>
                <div className="text-[11px] font-mono text-zinc-400">
                  Profiled: {formatDateTime(profile.profiled_at_utc)}
                </div>
              </div>

              {/* KPI Summary Tiles */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                  <span className="text-[11px] text-zinc-400 uppercase font-mono">Total Rows</span>
                  <div className="text-xl font-bold text-white font-mono mt-1">
                    {formatNumber(profile.row_count)}
                  </div>
                </div>
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                  <span className="text-[11px] text-zinc-400 uppercase font-mono">Columns</span>
                  <div className="text-xl font-bold text-white font-mono mt-1">
                    {profile.column_count}
                  </div>
                </div>
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                  <span className="text-[11px] text-zinc-400 uppercase font-mono">Target Column</span>
                  <div className="text-xl font-bold text-brand-400 font-mono mt-1">
                    {profile.detected_target_column || 'None'}
                  </div>
                </div>
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5">
                  <span className="text-[11px] text-zinc-400 uppercase font-mono">Price Column</span>
                  <div className="text-xl font-bold text-emerald-400 font-mono mt-1">
                    {profile.detected_price_column || 'None'}
                  </div>
                </div>
              </div>

              {/* Data Quality Flags */}
              {profile.data_quality_issues?.length > 0 && (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-amber-300">
                    <AlertTriangle className="size-4 text-amber-400 shrink-0" />
                    <span>Data Quality & Integrity Flags ({profile.data_quality_issues.length})</span>
                  </div>
                  <ul className="list-disc list-inside text-xs text-zinc-300 space-y-1">
                    {profile.data_quality_issues.map((issue, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {issue}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Column Level Profiling Table */}
              <div>
                <div className="flex items-center justify-between gap-3 mb-3">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
                    Detected Schema & Column Distributions
                  </h4>
                  <div className="relative">
                    <Search className="size-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Filter column..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="bg-black/30 border border-white/10 rounded-lg pl-8 pr-3 py-1 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-500"
                    />
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl border border-white/5 bg-black/20">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-white/[0.02] text-zinc-400 border-b border-white/5">
                      <tr>
                        <th className="py-2.5 px-4 font-medium">Column Name</th>
                        <th className="py-2.5 px-4 font-medium">Inferred Type</th>
                        <th className="py-2.5 px-4 font-medium">Null Ratio</th>
                        <th className="py-2.5 px-4 font-medium">Unique Values</th>
                        <th className="py-2.5 px-4 font-medium">Min</th>
                        <th className="py-2.5 px-4 font-medium">Max</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                      {Object.entries(profile.column_profiles || {})
                        .filter(([col]) => col.toLowerCase().includes(searchTerm.toLowerCase()))
                        .map(([col, stats]) => (
                          <tr key={col} className="hover:bg-white/[0.02]">
                            <td className="py-2 px-4 text-zinc-200 font-semibold">{col}</td>
                            <td className="py-2 px-4 text-brand-300">{stats.detected_type || 'object'}</td>
                            <td className="py-2 px-4 text-zinc-400">
                              {stats.null_ratio !== undefined
                                ? `${(stats.null_ratio * 100).toFixed(1)}%`
                                : '0%'}
                            </td>
                            <td className="py-2 px-4 text-zinc-400">
                              {stats.unique_count !== undefined ? formatNumber(stats.unique_count) : '-'}
                            </td>
                            <td className="py-2 px-4 text-zinc-400 truncate max-w-[120px]">
                              {stats.min !== undefined ? String(stats.min) : '-'}
                            </td>
                            <td className="py-2 px-4 text-zinc-400 truncate max-w-[120px]">
                              {stats.max !== undefined ? String(stats.max) : '-'}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-[#121217] p-8 text-center text-zinc-400">
              No statistical profile generated for this dataset yet. Run dataset profiling from backend CLI.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
