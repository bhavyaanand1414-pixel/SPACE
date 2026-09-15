import React, { useState, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/* ── Reusable sub-components ───────────────────────────────────────── */

const Badge = ({ children, color = 'cyan' }) => (
  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${color}-500/20 text-${color}-400 border border-${color}-500/30`}
    style={{ background: `rgba(var(--${color}, 0, 200, 255), 0.12)`, color: `rgb(var(--${color}, 100, 220, 255))`, borderColor: `rgba(var(--${color}, 0, 200, 255), 0.25)` }}>
    {children}
  </span>
);

const SimilarityBar = ({ score }) => {
  const pct = Math.round(score * 100);
  const hue = score > 0.7 ? 140 : score > 0.4 ? 50 : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: `hsl(${hue}, 70%, 55%)` }} />
      </div>
      <span className="text-slate-400 font-mono w-10 text-right">{pct}%</span>
    </div>
  );
};

/* ── Main Search Page ──────────────────────────────────────────────── */

export const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [latency, setLatency] = useState(null);
  const [searchType, setSearchType] = useState('text');
  const [error, setError] = useState(null);
  const [totalResults, setTotalResults] = useState(0);

  // Filters
  const [satellite, setSatellite] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const handleTextSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const body = {
        query: query.trim(),
        limit: 50,
        filters: {},
      };
      if (satellite) body.filters.satellite = satellite;
      if (dateFrom) body.filters.date_from = dateFrom;
      if (dateTo) body.filters.date_to = dateTo;

      const res = await fetch(`${API_BASE}/search/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`Search failed: ${res.status}`);
      const data = await res.json();
      setResults(data.results || []);
      setTotalResults(data.total_results || 0);
      setLatency(data.latency_ms);
      setSearchType('text');
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, satellite, dateFrom, dateTo]);

  const handleImageSearch = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('limit', '50');
      if (satellite) formData.append('satellite', satellite);

      const res = await fetch(`${API_BASE}/search/image`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error(`Image search failed: ${res.status}`);
      const data = await res.json();
      setResults(data.results || []);
      setTotalResults(data.total_results || 0);
      setLatency(data.latency_ms);
      setSearchType('image');
      setQuery(`[Image: ${file.name}]`);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [satellite]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleTextSearch();
  };

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
          Semantic Search
        </h1>
        <p className="mt-2 text-slate-400 text-sm">
          Search the satellite imagery archive by meaning — enter a natural-language query or upload an image to find visually similar tiles.
        </p>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              id="search-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder='e.g. "newly built structures near a river" or "large vehicle concentrations on open ground"'
              className="w-full px-4 py-3 bg-slate-800/80 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all text-sm"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs">
              ⏎ Enter
            </div>
          </div>
          <button
            id="search-btn"
            onClick={handleTextSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl font-medium text-sm hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/20"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                Searching...
              </span>
            ) : 'Search'}
          </button>
        </div>

        {/* Image Search Upload */}
        <div className="mt-3 flex items-center gap-4">
          <label className="flex items-center gap-2 px-4 py-2 bg-slate-800/60 border border-dashed border-slate-600 rounded-lg cursor-pointer hover:border-cyan-500/50 transition-colors text-sm text-slate-400 hover:text-cyan-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            Image Search
            <input type="file" accept="image/*" className="hidden" onChange={handleImageSearch} />
          </label>

          {/* Filters */}
          <select
            value={satellite}
            onChange={(e) => setSatellite(e.target.value)}
            className="px-3 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="">All Sensors</option>
            <option value="sentinel-2">Sentinel-2</option>
            <option value="sentinel-1">Sentinel-1 SAR</option>
            <option value="landsat">Landsat 8/9</option>
          </select>

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="px-3 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            placeholder="From"
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="px-3 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            placeholder="To"
          />
        </div>
      </div>

      {/* Results Meta */}
      {(results.length > 0 || latency !== null) && (
        <div className="flex items-center gap-4 mb-4 text-sm text-slate-400">
          <span>{totalResults} results</span>
          {latency !== null && <span>· {latency.toFixed(1)} ms</span>}
          <Badge>{searchType === 'text' ? 'Text Search' : 'Image Search'}</Badge>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {results.map((r, i) => (
          <div key={r.tile_id || i} id={`result-${i}`} className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden hover:border-cyan-500/40 transition-all group cursor-pointer">
            {/* Tile thumbnail */}
            <div className="aspect-square bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center relative overflow-hidden">
              {r.thumbnail_url ? (
                <img 
                  src={r.thumbnail_url.startsWith('http') ? r.thumbnail_url : `http://localhost:8000${r.thumbnail_url}`} 
                  alt={`Tile ${r.tile_id}`} 
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
              ) : (
                <div className="text-slate-500 text-xs font-mono">{r.tile_id?.split(':')[1] ? `Tile #${r.tile_id.split(':')[1]}` : r.tile_id?.substring(0, 8)}</div>
              )}
              <div className="absolute top-2 right-2">
                <span className="px-2 py-0.5 bg-black/60 rounded text-xs font-mono text-cyan-400">
                  #{i + 1}
                </span>
              </div>
            </div>
            {/* Metadata */}
            <div className="p-3 space-y-2">
              <SimilarityBar score={r.similarity_score} />
              <div className="flex flex-wrap gap-1.5">
                {r.satellite && <Badge>{r.satellite}</Badge>}
                {r.acquisition_date && <Badge color="purple">{r.acquisition_date?.substring(0, 10)}</Badge>}
              </div>
              <div className="text-xs text-slate-500 font-mono truncate" title={r.scene_id}>
                Scene: {r.scene_id?.substring(0, 12)}...
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {results.length === 0 && !loading && !error && (
        <div className="text-center py-20 text-slate-500">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <p className="text-lg mb-1">Search the satellite archive</p>
          <p className="text-sm">Enter a natural-language query or upload an image to discover matching tiles</p>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
