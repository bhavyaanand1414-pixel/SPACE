import React from 'react';
import { Card } from '../components/Card';
import { Table } from '../components/Table';
import { Badge } from '../components/Badge';

export const ModelsPage = () => {
  const models = [
    {
      name: 'Siamese U-Net (ResNet-50)',
      version: 'v1.0.0',
      dataset: 'LEVIR-CD + S2Looking',
      f1: '0.912',
      iou: '0.845',
      precision: '0.930',
      recall: '0.895',
      status: 'ACTIVE_PRODUCTION',
    },
    {
      name: 'Spectral Baseline Difference',
      version: 'v0.9.0',
      dataset: 'Otsu Morphological',
      f1: '0.764',
      iou: '0.628',
      precision: '0.742',
      recall: '0.789',
      status: 'BASELINE_FALLBACK',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Models & Benchmarks</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            MODEL VERSION REGISTRY, HARDWARE ACCELERATION & VALIDATION METRICS
          </p>
        </div>
      </div>

      <Card title="Registered Change Detection Architectures">
        <Table
          data={models}
          keyExtractor={(item) => item.version}
          columns={[
            {
              header: 'Architecture / Model',
              accessor: (item) => (
                <div>
                  <div className="font-semibold text-white">{item.name}</div>
                  <div className="text-[11px] text-cyan-400 font-mono">{item.version}</div>
                </div>
              ),
            },
            {
              header: 'Training Dataset',
              accessor: (item) => <span className="font-mono text-xs text-slate-300">{item.dataset}</span>,
            },
            {
              header: 'F1 Score',
              accessor: (item) => <span className="font-mono text-emerald-400 font-bold">{item.f1}</span>,
            },
            {
              header: 'IoU Score',
              accessor: (item) => <span className="font-mono text-cyan-400 font-bold">{item.iou}</span>,
            },
            {
              header: 'Status',
              accessor: (item) => (
                <Badge variant={item.status === 'ACTIVE_PRODUCTION' ? 'emerald' : 'gray'}>
                  {item.status}
                </Badge>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default ModelsPage;
