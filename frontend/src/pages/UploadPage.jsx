import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  ShieldAlert,
  Info,
  X,
  FileCheck,
  AlertTriangle,
  HelpCircle,
  ArrowRight,
  Sparkles,
  Zap,
  Database,
  RotateCcw,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Badge } from '../components/Badge';
import {
  uploadSatelliteImage,
  validateAnalysisPair,
} from '../services/api';

const DEMO_PRESETS = [
  {
    id: 'guwahati-sprawl',
    name: 'Guwahati Urban Sprawl',
    region: 'Kamrup Metro, Assam',
    sensor: 'sentinel2',
    description: 'Rapid commercial corridor expansion (2020 vs 2024)',
    slot1: {
      image_id: 'S2A_MSIL2A_20200214_GUWAHATI_T1',
      filename: 'S2A_MSIL2A_20200214_GUWAHATI_T1.tif',
      file_size_bytes: 48920400,
      format: 'GeoTIFF',
      is_georeferenced: true,
      checksum_sha256: 'a4f91d8e6c70281b37f48102d9cba4839201f8472918e7b39201847192837482',
      metadata: {
        width: 2048,
        height: 2048,
        crs: 'WGS 84 / UTM zone 46N',
        epsg_code: 32646,
        resolution_x: 10.0,
        resolution_y: 10.0,
        band_count: 4,
        dtype: 'uint16',
        acquisition_date: '2020-02-14',
        acquisition_time: '04:32:18 UTC',
      },
    },
    slot2: {
      image_id: 'S2B_MSIL2A_20240218_GUWAHATI_T2',
      filename: 'S2B_MSIL2A_20240218_GUWAHATI_T2.tif',
      file_size_bytes: 51240320,
      format: 'GeoTIFF',
      is_georeferenced: true,
      checksum_sha256: '9f81a74d283719e7401928472918472910385729104829104829184729184721',
      metadata: {
        width: 2048,
        height: 2048,
        crs: 'WGS 84 / UTM zone 46N',
        epsg_code: 32646,
        resolution_x: 10.0,
        resolution_y: 10.0,
        band_count: 4,
        dtype: 'uint16',
        acquisition_date: '2024-02-18',
        acquisition_time: '04:35:02 UTC',
      },
    },
    validation: {
      data_quality_score: 94,
      recommendation: 'READY_FOR_INFERENCE',
      compatible: true,
      crs_match: true,
      resolution_match: true,
      extent_overlap_pct: 99.4,
      temporal_baseline_days: 1465,
      checks_matrix: [
        {
          name: 'Coordinate Reference System (CRS)',
          status: 'PASS',
          message: 'Both rasters project into WGS 84 / UTM zone 46N (EPSG:32646)',
        },
        {
          name: 'Spatial Extent Intersection',
          status: 'PASS',
          message: '99.4% spatial overlap — optimal bounding envelope for change detection',
        },
        {
          name: 'Ground Sampling Resolution (GSD)',
          status: 'PASS',
          message: 'Identical 10.0 m/pixel resolution across observation pair',
        },
        {
          name: 'Multi-Temporal Baseline Window',
          status: 'PASS',
          message: '1,465 days baseline window (2020-02-14 to 2024-02-18)',
        },
      ],
    },
  },
  {
    id: 'brahmaputra-flood',
    name: 'Brahmaputra Flood Dynamics',
    region: 'Kaziranga Buffer, Assam',
    sensor: 'sentinel1',
    description: 'Monsoon riverbed inundation & sediment shifting (Pre vs Post Monsoon)',
    slot1: {
      image_id: 'S1A_IW_GRDH_20230412_BRAHMAPUTRA_PRE',
      filename: 'S1A_IW_GRDH_20230412_BRAHMAPUTRA_PRE.tif',
      file_size_bytes: 62491820,
      format: 'GeoTIFF',
      is_georeferenced: true,
      checksum_sha256: 'c827391037482910482910482910482910482910482910482910482910482910',
      metadata: {
        width: 2400,
        height: 2400,
        crs: 'WGS 84 / UTM zone 46N',
        epsg_code: 32646,
        resolution_x: 10.0,
        resolution_y: 10.0,
        band_count: 2,
        dtype: 'float32',
        acquisition_date: '2023-04-12',
        acquisition_time: '23:45:10 UTC',
      },
    },
    slot2: {
      image_id: 'S1A_IW_GRDH_20230820_BRAHMAPUTRA_PEAK',
      filename: 'S1A_IW_GRDH_20230820_BRAHMAPUTRA_PEAK.tif',
      file_size_bytes: 64182900,
      format: 'GeoTIFF',
      is_georeferenced: true,
      checksum_sha256: 'e109284729184729104829104829104829104829104829104829104829104829',
      metadata: {
        width: 2400,
        height: 2400,
        crs: 'WGS 84 / UTM zone 46N',
        epsg_code: 32646,
        resolution_x: 10.0,
        resolution_y: 10.0,
        band_count: 2,
        dtype: 'float32',
        acquisition_date: '2023-08-20',
        acquisition_time: '23:45:14 UTC',
      },
    },
    validation: {
      data_quality_score: 91,
      recommendation: 'READY_FOR_INFERENCE',
      compatible: true,
      crs_match: true,
      resolution_match: true,
      extent_overlap_pct: 98.7,
      temporal_baseline_days: 130,
      checks_matrix: [
        {
          name: 'C-Band SAR Modality',
          status: 'PASS',
          message: 'Both rasters are dual-pol VV+VH Sentinel-1 GRDH scenes',
        },
        {
          name: 'Spatial Extent Intersection',
          status: 'PASS',
          message: '98.7% spatial overlap across Kaziranga flood channel buffer',
        },
        {
          name: 'Pixel Ground Sampling',
          status: 'PASS',
          message: 'Matched 10.0 m/px spatial pixel grid',
        },
        {
          name: 'Monsoon Dynamic Delta',
          status: 'PASS',
          message: 'Pre-monsoon (April) vs Peak-monsoon (August) 130 days baseline',
        },
      ],
    },
  },
  {
    id: 'assam-forest',
    name: 'Karbi Anglong Forest Canopy',
    region: 'Diphu Foothills, Assam',
    sensor: 'sentinel2',
    description: 'Canopy density alteration & deforestation monitoring (2021 vs 2024)',
    slot1: {
      image_id: 'S2A_MSIL2A_20210105_KARBI_CANOPY_T1',
      filename: 'S2A_MSIL2A_20210105_KARBI_CANOPY_T1.tif',
      file_size_bytes: 47291800,
      format: 'GeoTIFF',
      is_georeferenced: true,
      checksum_sha256: '5a10948291048291048291048291048291048291048291048291048291048291',
      metadata: {
        width: 2048,
        height: 2048,
        crs: 'WGS 84 / UTM zone 46N',
        epsg_code: 32646,
        resolution_x: 10.0,
        resolution_y: 10.0,
        band_count: 4,
        dtype: 'uint16',
        acquisition_date: '2021-01-05',
        acquisition_time: '04:31:40 UTC',
      },
    },
    slot2: {
      image_id: 'S2B_MSIL2A_20240110_KARBI_CANOPY_T2',
      filename: 'S2B_MSIL2A_20240110_KARBI_CANOPY_T2.tif',
      file_size_bytes: 49830200,
      format: 'GeoTIFF',
      is_georeferenced: true,
      checksum_sha256: '7b20948291048291048291048291048291048291048291048291048291048292',
      metadata: {
        width: 2048,
        height: 2048,
        crs: 'WGS 84 / UTM zone 46N',
        epsg_code: 32646,
        resolution_x: 10.0,
        resolution_y: 10.0,
        band_count: 4,
        dtype: 'uint16',
        acquisition_date: '2024-01-10',
        acquisition_time: '04:33:12 UTC',
      },
    },
    validation: {
      data_quality_score: 96,
      recommendation: 'READY_FOR_INFERENCE',
      compatible: true,
      crs_match: true,
      resolution_match: true,
      extent_overlap_pct: 100.0,
      temporal_baseline_days: 1100,
      checks_matrix: [
        {
          name: 'Optical Band Alignment',
          status: 'PASS',
          message: 'B2, B3, B4, B8 spectral alignment verified for NDVI differencing',
        },
        {
          name: 'Canopy Ortho Rectification',
          status: 'PASS',
          message: '100.0% footprint overlap in Diphu hills',
        },
        {
          name: 'Spatial GSD Resolution',
          status: 'PASS',
          message: '10.0 m/px Sentinel-2 standard band resolution',
        },
        {
          name: 'Multi-Year Canopy Baseline',
          status: 'PASS',
          message: '1,100 days multi-temporal vegetative baseline',
        },
      ],
    },
  },
];

export const UploadPage = () => {
  const [selectedSensor, setSelectedSensor] = useState('sentinel2');

  const [slot1, setSlot1] = useState({
    file: null,
    isDragging: false,
    progress: 0,
    isUploading: false,
    error: null,
    result: null,
  });

  const [slot2, setSlot2] = useState({
    file: null,
    isDragging: false,
    progress: 0,
    isUploading: false,
    error: null,
    result: null,
  });

  const [activePreset, setActivePreset] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [validationError, setValidationError] = useState(null);

  const fileInputRef1 = useRef(null);
  const fileInputRef2 = useRef(null);

  const handleLoadPreset = (preset) => {
    setActivePreset(preset.id);
    setSelectedSensor(preset.sensor);
    setValidationError(null);

    const slot1File = {
      name: preset.slot1.filename || `${preset.slot1.image_id}.tif`,
      size: preset.slot1.file_size_bytes,
      type: 'image/tiff',
    };

    const slot2File = {
      name: preset.slot2.filename || `${preset.slot2.image_id}.tif`,
      size: preset.slot2.file_size_bytes,
      type: 'image/tiff',
    };

    setSlot1({
      file: slot1File,
      isDragging: false,
      progress: 100,
      isUploading: false,
      error: null,
      result: {
        ...preset.slot1,
        filename: slot1File.name,
      },
    });

    setSlot2({
      file: slot2File,
      isDragging: false,
      progress: 100,
      isUploading: false,
      error: null,
      result: {
        ...preset.slot2,
        filename: slot2File.name,
      },
    });

    setValidationResult(preset.validation);
  };

  const handleResetAll = () => {
    setActivePreset(null);
    setSlot1({ file: null, isDragging: false, progress: 0, isUploading: false, error: null, result: null });
    setSlot2({ file: null, isDragging: false, progress: 0, isUploading: false, error: null, result: null });
    setValidationResult(null);
    setValidationError(null);
    if (fileInputRef1.current) fileInputRef1.current.value = '';
    if (fileInputRef2.current) fileInputRef2.current.value = '';
  };

  const validateFile = (file) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const allowed = ['.tif', '.tiff', '.jpg', '.jpeg', '.png'];
    if (!allowed.includes(ext)) {
      return `Unsupported file format '${ext}'. Please upload GeoTIFF (.tif, .tiff) or Demo image (.jpg, .png).`;
    }
    if (file.size < 1024) {
      return 'File is too small (< 1 KB) — file appears empty or corrupted.';
    }
    if (file.size > 2 * 1024 * 1024 * 1024) {
      return 'File exceeds maximum upload limit of 2 GB.';
    }
    return null;
  };

  const handleFileSelection = async (file, slotNum) => {
    const error = validateFile(file);
    const setSlot = slotNum === 1 ? setSlot1 : setSlot2;

    if (error) {
      setSlot((prev) => ({
        ...prev,
        file: null,
        error,
        result: null,
        progress: 0,
        isUploading: false,
      }));
      return;
    }

    setSlot((prev) => ({
      ...prev,
      file,
      error: null,
      result: null,
      progress: 0,
      isUploading: true,
    }));

    setValidationResult(null);
    setValidationError(null);

    try {
      const response = await uploadSatelliteImage(
        file,
        selectedSensor,
        (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setSlot((prev) => ({ ...prev, progress: percent }));
          }
        }
      );

      setSlot((prev) => ({
        ...prev,
        isUploading: false,
        progress: 100,
        result: response,
        error: null,
      }));
    } catch (err) {
      const message =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        'Upload failed. Check backend connection.';
      setSlot((prev) => ({
        ...prev,
        isUploading: false,
        progress: 0,
        error: message,
      }));
    }
  };

  const handleValidatePair = async () => {
    if (!slot1.result || !slot2.result) return;

    setIsValidating(true);
    setValidationError(null);

    try {
      const response = await validateAnalysisPair(
        slot1.result.filename,
        slot2.result.filename,
        selectedSensor
      );
      setValidationResult(response);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.error?.message ||
        err?.message ||
        'Validation failed.';
      setValidationError(msg);
    } finally {
      setIsValidating(false);
    }
  };

  const renderSlot = (title, subtitle, slot, setSlot, inputRef, slotNum) => {
    const isDemoFormat =
      slot.file?.name &&
      ['.jpg', '.jpeg', '.png'].some((ext) => slot.file.name.toLowerCase().endsWith(ext));

    return (
      <Card title={title} subtitle={subtitle}>
        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setSlot((prev) => ({ ...prev, isDragging: true }));
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setSlot((prev) => ({ ...prev, isDragging: false }));
          }}
          onDrop={(e) => {
            e.preventDefault();
            setSlot((prev) => ({ ...prev, isDragging: false }));
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleFileSelection(e.dataTransfer.files[0], slotNum);
            }
          }}
          className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
            slot.isDragging
              ? 'border-cyan-400 bg-cyan-950/30 scale-[1.01]'
              : slot.error
              ? 'border-rose-500/50 bg-rose-950/20'
              : slot.result
              ? 'border-emerald-500/40 bg-emerald-950/10'
              : 'border-white/10 hover:border-cyan-500/40 hover:bg-space-900/60'
          }`}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".tif,.tiff,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelection(e.target.files[0], slotNum);
              }
            }}
          />

          <UploadCloud
            className={`w-10 h-10 mx-auto mb-2.5 transition-transform duration-200 ${
              slot.isDragging ? 'scale-110 text-cyan-300' : 'text-cyan-400'
            }`}
          />
          <p className="text-xs font-medium text-slate-200 mb-1">
            Drag & drop satellite raster tile or <span className="text-cyan-400 underline">browse</span>
          </p>
          <p className="text-[11px] text-slate-400 font-mono">
            Supported: <span className="text-cyan-300">GeoTIFF (.tif, .tiff)</span> • Demo: (.jpg, .png)
          </p>
        </div>

        {/* Demo Format Notice */}
        {isDemoFormat && (
          <div className="mt-3 p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/30 flex items-center gap-2 text-[11px] text-amber-300">
            <Info className="w-4 h-4 shrink-0 text-amber-400" />
            <span>Non-georeferenced demo format detected. For spatial analysis, GeoTIFF is recommended.</span>
          </div>
        )}

        {/* Upload Progress Bar */}
        {slot.isUploading && (
          <div className="mt-4 space-y-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-cyan-400">Uploading & Validating...</span>
              <span className="text-slate-300">{slot.progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-space-900 rounded-full overflow-hidden border border-white/10">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-150"
                style={{ width: `${slot.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Display */}
        {slot.error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-500/40 text-xs text-rose-300 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1 font-mono">{slot.error}</div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSlot((prev) => ({ ...prev, error: null }));
              }}
              className="text-rose-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Metadata Preview Box */}
        {slot.result && (
          <div className="mt-4 p-4 rounded-xl bg-space-900 border border-emerald-500/30 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/5">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-white">Raster Ingested & Validated</span>
              </div>
              <Badge variant={slot.result.is_georeferenced ? 'emerald' : 'amber'}>
                {slot.result.format}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="p-2 rounded bg-space-950/80 border border-white/5">
                <span className="text-slate-500 block text-[10px]">IMAGE ID:</span>
                <span className="text-cyan-400 truncate block" title={slot.result.image_id}>
                  {slot.result.image_id.substring(0, 16)}...
                </span>
              </div>
              <div className="p-2 rounded bg-space-950/80 border border-white/5">
                <span className="text-slate-500 block text-[10px]">FILE SIZE:</span>
                <span className="text-slate-200">
                  {(slot.result.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>

              {slot.result.metadata && (
                <>
                  <div className="p-2 rounded bg-space-950/80 border border-white/5">
                    <span className="text-slate-500 block text-[10px]">DIMENSIONS:</span>
                    <span className="text-slate-200">
                      {slot.result.metadata.width} × {slot.result.metadata.height} px
                    </span>
                  </div>
                  <div className="p-2 rounded bg-space-950/80 border border-white/5">
                    <span className="text-slate-500 block text-[10px]">SPECTRAL BANDS:</span>
                    <span className="text-slate-200">
                      {slot.result.metadata.band_count || 3} Bands ({slot.result.metadata.dtype || 'uint8'})
                    </span>
                  </div>
                  {slot.result.metadata.crs && (
                    <div className="col-span-2 p-2 rounded bg-space-950/80 border border-white/5">
                      <span className="text-slate-500 block text-[10px]">CRS / EPSG:</span>
                      <span className="text-emerald-400 font-semibold">
                        {slot.result.metadata.crs} {slot.result.metadata.epsg_code ? `(EPSG:${slot.result.metadata.epsg_code})` : ''}
                      </span>
                    </div>
                  )}
                  {slot.result.metadata.resolution_x && (
                    <div className="col-span-2 p-2 rounded bg-space-950/80 border border-white/5">
                      <span className="text-slate-500 block text-[10px]">SPATIAL RESOLUTION:</span>
                      <span className="text-cyan-400">
                        {slot.result.metadata.resolution_x.toFixed(2)} m/px (Ground Sampling Distance)
                      </span>
                    </div>
                  )}
                  {slot.result.metadata.acquisition_date && (
                    <div className="col-span-2 p-2 rounded bg-space-950/80 border border-white/5">
                      <span className="text-slate-500 block text-[10px]">ACQUISITION DATE:</span>
                      <span className="text-amber-400 font-semibold">
                        {slot.result.metadata.acquisition_date} {slot.result.metadata.acquisition_time || ''}
                      </span>
                    </div>
                  )}
                </>
              )}

              {slot.result.checksum_sha256 && (
                <div className="col-span-2 p-2 rounded bg-space-950/80 border border-white/5">
                  <span className="text-slate-500 block text-[10px]">SHA-256 INTEGRITY CHECKSUM:</span>
                  <span className="text-slate-400 text-[10px] truncate block font-mono">
                    {slot.result.checksum_sha256}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Upload Satellite Imagery</h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          INGEST MULTI-TEMPORAL GEOTIFF / TIFF RASTERS WITH AUTOMATED CRS & METADATA EXTRACTION
        </p>
      </div>

      {/* Sensor Modality Configuration */}
      <Card title="Sensor Modality Configuration" subtitle="Sensor abstraction layer settings">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            type="button"
            onClick={() => setSelectedSensor('sentinel2')}
            className={`p-4 rounded-xl border text-left transition-all ${
              selectedSensor === 'sentinel2'
                ? 'bg-cyan-950/40 border-cyan-500 text-cyan-300 shadow-glow-cyan'
                : 'bg-space-900 border-white/5 text-slate-400 hover:border-white/20'
            }`}
          >
            <div className="text-xs font-bold font-mono">Sentinel-2 (MSI)</div>
            <div className="text-[11px] text-slate-400 mt-1">Optical Multi-spectral (10m - 20m)</div>
          </button>

          <button
            type="button"
            onClick={() => setSelectedSensor('sentinel1')}
            className={`p-4 rounded-xl border text-left transition-all ${
              selectedSensor === 'sentinel1'
                ? 'bg-cyan-950/40 border-cyan-500 text-cyan-300 shadow-glow-cyan'
                : 'bg-space-900 border-white/5 text-slate-400 hover:border-white/20'
            }`}
          >
            <div className="text-xs font-bold font-mono">Sentinel-1 (SAR)</div>
            <div className="text-[11px] text-slate-400 mt-1">C-band SAR (VV/VH Flood & Terrain)</div>
          </button>

          <button
            type="button"
            onClick={() => setSelectedSensor('landsat')}
            className={`p-4 rounded-xl border text-left transition-all ${
              selectedSensor === 'landsat'
                ? 'bg-cyan-950/40 border-cyan-500 text-cyan-300 shadow-glow-cyan'
                : 'bg-space-900 border-white/5 text-slate-400 hover:border-white/20'
            }`}
          >
            <div className="text-xs font-bold font-mono">Landsat 8/9 & Generic</div>
            <div className="text-[11px] text-slate-400 mt-1">Multi-decade Sprawl & Ortho</div>
          </button>
        </div>
      </Card>

      {/* 1-Click Demo Sample Pair Loader */}
      <Card
        title="1-Click Demo Sample Satellite Pairs"
        subtitle="INSTANTLY LOAD VALIDATED REGIONAL GEOTIFF DATASETS FOR TESTING WITHOUT MANUAL DOWNLOAD"
        glow="cyan"
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono text-cyan-400">
              <Zap className="w-3.5 h-3.5" />
              <span>TESTING DATASETS (ASSAM & NE BORDER REGIONS)</span>
            </div>
            {(slot1.result || slot2.result || activePreset) && (
              <button
                type="button"
                onClick={handleResetAll}
                className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 font-mono px-2.5 py-1 rounded bg-rose-950/40 border border-rose-500/30 transition-all"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Dropzones</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {DEMO_PRESETS.map((preset) => {
              const isSelected = activePreset === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleLoadPreset(preset)}
                  className={`p-3.5 rounded-xl border text-left transition-all relative overflow-hidden group ${
                    isSelected
                      ? 'bg-cyan-950/50 border-cyan-400 ring-1 ring-cyan-400/50 shadow-glow-cyan'
                      : 'bg-space-900/80 border-white/10 hover:border-cyan-500/40 hover:bg-space-800'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors">
                      {preset.name}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold ${
                        preset.sensor === 'sentinel1'
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {preset.sensor === 'sentinel1' ? 'SAR S-1' : 'OPT S-2'}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 font-mono mt-1">
                    {preset.region}
                  </p>
                  <p className="text-[11px] text-slate-300/80 mt-1.5 line-clamp-2">
                    {preset.description}
                  </p>

                  <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">Pair Baseline:</span>
                    <span className="text-cyan-400 font-semibold">
                      {preset.validation.temporal_baseline_days} days
                    </span>
                  </div>

                  {isSelected && (
                    <div className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Dual Tile Upload Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {renderSlot(
          'Observation T1 (Before / Baseline)',
          'Historical Reference Satellite Tile',
          slot1,
          setSlot1,
          fileInputRef1,
          1
        )}
        {renderSlot(
          'Observation T2 (After / Current)',
          'Recent Monitoring Satellite Tile',
          slot2,
          setSlot2,
          fileInputRef2,
          2
        )}
      </div>

      {/* Pair Action & Compatibility Validation Trigger */}
      {slot1.result && slot2.result && (
        <Card title="Temporal Pair Readiness & Quality Verification" glow="cyan">
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-white/5">
              <div>
                <div className="text-sm font-semibold text-white">Both Observation Rasters Ingested</div>
                <p className="text-xs text-slate-400 font-mono">
                  Trigger automated GDAL/Rasterio geospatial overlap, CRS, and Data Quality Score computation.
                </p>
              </div>
              <Button
                variant="primary"
                size="md"
                icon={FileCheck}
                isLoading={isValidating}
                onClick={handleValidatePair}
              >
                Validate Pair Compatibility
              </Button>
            </div>

            {/* Validation Error */}
            {validationError && (
              <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Validation Results Matrix */}
            {validationResult && (
              <div className="space-y-4 pt-2">
                <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-space-950/80 border border-white/10">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-400 uppercase">DATA QUALITY SCORE:</span>
                    <span
                      className={`text-xl font-bold font-mono ${
                        validationResult.data_quality_score >= 80
                          ? 'text-emerald-400'
                          : validationResult.data_quality_score >= 50
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {validationResult.data_quality_score} / 100
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-400">RECOMMENDATION:</span>
                    <Badge
                      variant={
                        validationResult.recommendation === 'READY_FOR_INFERENCE'
                          ? 'emerald'
                          : validationResult.recommendation === 'REQUIRES_PREPROCESSING'
                          ? 'amber'
                          : 'rose'
                      }
                    >
                      {validationResult.recommendation}
                    </Badge>
                  </div>
                </div>

                {/* Diagnostic Check Items Matrix */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs font-mono">
                  {(validationResult.checks_matrix || []).map((check, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border flex items-start justify-between gap-3 ${
                        check.status === 'PASS'
                          ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                          : check.status === 'WARNING'
                          ? 'bg-amber-950/20 border-amber-500/30 text-amber-300'
                          : check.status === 'FAIL'
                          ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                          : 'bg-space-900 border-white/5 text-slate-400'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="font-bold flex items-center gap-1.5">
                          {check.status === 'PASS' ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          ) : check.status === 'WARNING' ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          ) : check.status === 'FAIL' ? (
                            <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                          ) : (
                            <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                          )}
                          <span>{check.name}</span>
                        </div>
                        <p className="text-[11px] opacity-90">{check.message}</p>
                      </div>
                      <Badge
                        variant={
                          check.status === 'PASS'
                            ? 'emerald'
                            : check.status === 'WARNING'
                            ? 'amber'
                            : check.status === 'FAIL'
                            ? 'rose'
                            : 'gray'
                        }
                        size="sm"
                      >
                        {check.status}
                      </Badge>
                    </div>
                  ))}
                </div>

                {/* Direct Action Link to Analysis */}
                <div className="pt-2 flex justify-end">
                  <Link to="/analysis">
                    <Button variant="primary" size="md" icon={ArrowRight} iconPosition="right">
                      Proceed to Siamese U-Net Analysis
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default UploadPage;
