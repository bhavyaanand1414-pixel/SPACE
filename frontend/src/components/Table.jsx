import React from 'react';

export function Table({
  columns = [],
  data = [],
  keyExtractor,
  onRowClick,
  isLoading,
  emptyMessage = 'No records found.',
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-white/5 bg-space-900/50">
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="border-b border-white/10 bg-space-850 text-xs uppercase font-mono tracking-wider text-slate-400">
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} className={`px-4 py-3.5 ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-400">
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                  <span className="text-xs font-mono">Loading data stream...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-400 font-mono text-xs">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item, rowIdx) => (
              <tr
                key={keyExtractor ? keyExtractor(item) : rowIdx}
                onClick={() => onRowClick && onRowClick(item)}
                className={`transition-colors hover:bg-white/[0.03] ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((col, idx) => (
                  <td key={idx} className={`px-4 py-3 ${col.className || ''}`}>
                    {typeof col.accessor === 'function'
                      ? col.accessor(item)
                      : col.accessor
                      ? item[col.accessor]
                      : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
