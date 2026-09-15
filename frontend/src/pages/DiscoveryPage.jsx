import React, { useState, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const DiscoveryPage = () => {
  const [clusters, setClusters] = useState([]);
  const [similarResults, setSimilarResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [clusterMethod, setClusterMethod] = useState('hdbscan');
  const [totalTiles, setTotalTiles] = useState(0);
  const [error, setError] = useState(null);
  const [selectedTileId, setSelectedTileId] = useState('');
  const [activeTab, setActiveTab] = useState('clusters'); // clusters | similar

  const loadClusters = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/discover/clusters?method=${clusterMethod}&min_cluster_size=5`);
      if (!res.ok) throw new Error(`Clustering failed: ${res.status}`);
      const data = await res.json();
      setClusters(data.clusters || []);
      setTotalTiles(data.total_tiles || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [clusterMethod]);

  const findSimilar = useCallback(async () => {
    if (!selectedTileId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/discover/similar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tile_id: selectedTileId.trim(), k: 20 }),
      });
      if (!res.ok) throw new Error(`Find similar failed: ${res.status}`);
      const data = await res.json();
      setSimilarResults(data.results || []);
      setActiveTab('similar');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedTileId]);

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
          Discovery & Clustering
        </h1>
        <p className="mt-2 text-slate-400 text-sm">
          Discover patterns across the archive — group similar sites automatically or find comparable locations from a single example.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-800/50 p-1 rounded-xl w-fit">
        <button
          onClick={() => setActiveTab('clusters')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'clusters' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Cluster Analysis
        </button>
        <button
          onClick={() => setActiveTab('similar')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'similar' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Find Similar Sites
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Cluster Analysis Tab */}
      {activeTab === 'clusters' && (
        <div>
          <div className="flex gap-3 mb-6">
            <select
              value={clusterMethod}
              onChange={(e) => setClusterMethod(e.target.value)}
              className="px-3 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-slate-300"
            >
              <option value="hdbscan">HDBSCAN (Density-based)</option>
              <option value="kmeans">K-Means</option>
            </select>
            <button
              id="cluster-btn"
              onClick={loadClusters}
              disabled={loading}
              className="px-5 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium text-sm hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 transition-all shadow-lg shadow-emerald-500/20"
            >
              {loading ? 'Clustering...' : 'Run Clustering'}
            </button>
            {totalTiles > 0 && (
              <span className="flex items-center text-sm text-slate-400">
                {totalTiles} tiles indexed
              </span>
            )}
          </div>

          {/* Cluster Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {clusters.map((c) => (
              <div key={c.cluster_id} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:border-emerald-500/40 transition-all">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-emerald-400 font-semibold">Cluster #{c.cluster_id}</h3>
                  <span className="px-2 py-0.5 bg-emerald-500/15 text-emerald-400 rounded text-xs font-mono">
                    {c.member_count} tiles
                  </span>
                </div>
                <div className="space-y-2">
                  <div className="text-xs text-slate-500">Representatives:</div>
                  <div className="flex flex-wrap gap-1">
                    {c.representative_tile_ids?.slice(0, 3).map((tid, i) => (
                      <button
                        key={i}
                        onClick={() => { setSelectedTileId(tid); setActiveTab('similar'); }}
                        className="px-2 py-1 bg-slate-700/50 rounded text-xs text-slate-300 hover:bg-emerald-500/20 hover:text-emerald-400 transition-colors font-mono truncate max-w-[140px]"
                        title={`Find similar to ${tid}`}
                      >
                        {tid.length > 16 ? tid.substring(0, 16) + '...' : tid}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {clusters.length === 0 && !loading && (
            <div className="text-center py-16 text-slate-500">
              <p className="text-lg mb-1">No clusters generated yet</p>
              <p className="text-sm">Click "Run Clustering" to group similar tiles across the archive</p>
            </div>
          )}
        </div>
      )}

      {/* Find Similar Tab */}
      {activeTab === 'similar' && (
        <div>
          <div className="flex gap-3 mb-6">
            <input
              id="similar-input"
              type="text"
              value={selectedTileId}
              onChange={(e) => setSelectedTileId(e.target.value)}
              placeholder="Enter a Tile ID to find similar sites..."
              className="flex-1 px-4 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              id="similar-btn"
              onClick={findSimilar}
              disabled={loading || !selectedTileId.trim()}
              className="px-5 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-medium text-sm hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 transition-all"
            >
              Find Similar
            </button>
          </div>

          {/* Similar Results */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {similarResults.map((r, i) => (
              <div key={r.tile_id || i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 hover:border-emerald-500/30 transition-all">
                <div className="aspect-video bg-gradient-to-br from-slate-700 to-slate-800 rounded-lg mb-2 flex items-center justify-center">
                  <span className="text-slate-500 text-xs font-mono">{r.tile_id?.substring(0, 12)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-mono">Score: {(r.similarity_score * 100).toFixed(1)}%</span>
                  <button
                    onClick={() => setSelectedTileId(r.tile_id)}
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    Find similar →
                  </button>
                </div>
              </div>
            ))}
          </div>

          {similarResults.length === 0 && !loading && (
            <div className="text-center py-16 text-slate-500">
              <p className="text-lg mb-1">Find similar sites</p>
              <p className="text-sm">Enter a tile ID or click a representative tile from the cluster view</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DiscoveryPage;
