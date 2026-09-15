import React from 'react';
import { Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Badge } from '../components/Badge';

export const HistoryPage = () => {
  const historyList = [
    {
      id: 'AN-2026-0801',
      title: 'Guwahati Urban Sprawl & Infrastructure',
      dates: '2020-01-15 → 2026-01-15',
      sensor: 'Sentinel-2 MSI',
      changedArea: '5.24 km²',
      status: 'Completed',
      created: '2026-08-30',
    },
    {
      id: 'AN-2026-0802',
      title: 'Brahmaputra Flood Plain & River Course Shift',
      dates: '2025-06-10 → 2025-08-20',
      sensor: 'Sentinel-1 SAR',
      changedArea: '18.60 km²',
      status: 'Completed',
      created: '2026-08-25',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Analysis History</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            LOG OF ALL PERSISTED SATELLITE COMPARISON RUNS IN POSTGIS
          </p>
        </div>
      </div>

      <Card title="Stored Telemetry Records">
        <Table
          data={historyList}
          keyExtractor={(item) => item.id}
          columns={[
            {
              header: 'Analysis ID / Title',
              accessor: (item) => (
                <div>
                  <div className="font-semibold text-white">{item.title}</div>
                  <div className="text-[11px] text-cyan-400 font-mono">{item.id}</div>
                </div>
              ),
            },
            {
              header: 'Observation Interval',
              accessor: (item) => <span className="font-mono text-xs text-slate-300">{item.dates}</span>,
            },
            {
              header: 'Sensor',
              accessor: (item) => <Badge variant="indigo">{item.sensor}</Badge>,
            },
            {
              header: 'Changed Area',
              accessor: (item) => (
                <span className="font-mono text-amber-400 font-semibold">{item.changedArea}</span>
              ),
            },
            {
              header: 'Status',
              accessor: () => <Badge variant="emerald">COMPLETED</Badge>,
            },
            {
              header: 'Actions',
              accessor: () => (
                <div className="flex gap-2">
                  <Link to="/results">
                    <Button variant="outline" size="sm" icon={Eye}>
                      Inspect
                    </Button>
                  </Link>
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default HistoryPage;
