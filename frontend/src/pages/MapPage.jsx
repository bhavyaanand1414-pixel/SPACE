import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  Tooltip,
  Rectangle,
  Polyline,
  Polygon,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import {
  MapPin,
  Layers,
  Eye,
  Info,
  Calendar,
  SlidersHorizontal,
  MoveHorizontal,
  Sparkles,
  Radio,
  Trees,
  Building2,
  Crosshair,
  Activity,
  Zap,
  Compass,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Search,
  Navigation,
  LocateFixed,
  X,
  Loader2,
  Globe,
  Ruler,
  Square,
  Trash2,
  Undo,
} from 'lucide-react';
import { Card } from '../components/Card';
import { CategoryBadge, SeverityBadge } from '../components/Badge';
import { Button } from '../components/Button';
import { getAnalysisChangePolygons } from '../services/api';

// Constant initial center coordinates (prevents re-render reference mutation)
const INITIAL_MAP_CENTER = [26.1500, 91.7400];

// Geodesic distance calculation (Haversine formula in meters)
const haversineDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

// Total cumulative distance along multi-point polyline in meters
const calculateTotalDistance = (points) => {
  if (points.length < 2) return 0;
  let total = 0;
  for (let i = 0; i < points.length - 1; i++) {
    total += haversineDistance(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1]);
  }
  return total;
};

// Geodesic polygon area calculation (Shoelace on local tangent plane in m²)
const calculateGeodesicArea = (points) => {
  if (points.length < 3) return 0;
  const avgLat = points.reduce((acc, p) => acc + p[0], 0) / points.length;
  const latFactor = 111132.954;
  const lonFactor = 111132.954 * Math.cos((avgLat * Math.PI) / 180);

  let area = 0;
  const n = points.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const xi = points[i][1] * lonFactor;
    const yi = points[i][0] * latFactor;
    const xj = points[j][1] * lonFactor;
    const yj = points[j][0] * latFactor;
    area += xi * yj - xj * yi;
  }
  return Math.abs(area) / 2;
};

// Map click listener for placing survey measurement points
const MapMeasurementEvents = ({ measureMode, onAddPoint }) => {
  useMapEvents({
    click(e) {
      if (measureMode !== 'none' && e && e.latlng) {
        onAddPoint([+e.latlng.lat.toFixed(6), +e.latlng.lng.toFixed(6)]);
      }
    },
  });
  return null;
};

// Map Event Listener for Real-Time Coordinates & Spectral Probe (Direct DOM update: 0 React re-renders while dragging)
const MapEventsListener = () => {
  useMapEvents({
    mousemove(e) {
      if (!e || !e.latlng) return;
      const lat = +e.latlng.lat.toFixed(4);
      const lon = +e.latlng.lng.toFixed(4);

      let ndvi = 0.65;
      let ndbi = -0.22;
      let sar = '-12.5 dB';
      let status = 'Vegetated Canopy';

      if (lat > 26.140 && lat < 26.150 && lon > 91.730 && lon < 91.740) {
        ndvi = 0.18;
        ndbi = 0.62;
        sar = '+4.1 dB';
        status = 'Urban Construction (Impervious)';
      } else if (lat > 26.150 && lat < 26.156 && lon > 91.740 && lon < 91.752) {
        ndvi = 0.22;
        ndbi = 0.54;
        sar = '+2.9 dB';
        status = 'Road Corridor (Asphalt)';
      } else if (lat > 26.158 && lon < 91.735) {
        ndvi = 0.12;
        ndbi = -0.31;
        sar = '-16.2 dB';
        status = 'Waterbody / River Sandbar';
      }

      const el = document.getElementById('spectral-probe-telemetry');
      if (el) {
        el.innerHTML = `
          <span class="text-white font-bold">${lat}°N, ${lon}°E</span>
          <span class="text-slate-600">|</span>
          <span class="text-emerald-400">NDVI: ${ndvi}</span>
          <span class="text-slate-600">|</span>
          <span class="text-amber-400">NDBI: ${ndbi}</span>
          <span class="text-slate-600">|</span>
          <span class="text-purple-400">SAR: ${sar}</span>
          <span class="text-slate-600">|</span>
          <span class="text-cyan-300">[${status}]</span>
        `;
      }
    },
  });
  return null;
};

// Multi-input map navigation controller (Trackpad 2-finger pan, mouse drag fallback, keyboard arrow keys)
const EnableMapDragging = () => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    if (map.dragging) {
      map.dragging.enable();
    }
    if (map.touchZoom) map.touchZoom.enable();
    if (map.doubleClickZoom) map.doubleClickZoom.enable();
    if (map.scrollWheelZoom) map.scrollWheelZoom.enable();
    if (map.boxZoom) map.boxZoom.enable();
    if (map.keyboard) map.keyboard.enable();
    map.invalidateSize();

    const container = map.getContainer();
    if (!container) return;

    container.tabIndex = 0;
    container.style.cursor = 'grab';

    // 1. Two-finger Trackpad Pan Handler (Fixes Mac trackpad zooming instead of panning left/right)
    const onWheel = (e) => {
      // If user is intentionally pinching with 2 fingers or holding Ctrl/Cmd, allow Leaflet zoom
      if (e.ctrlKey || e.metaKey) {
        return;
      }

      // Detect trackpad gestures (any horizontal swipe or subtle vertical swipe)
      const hasHorizontalDelta = Math.abs(e.deltaX) > 0;
      const isSubtleVerticalDelta = Math.abs(e.deltaY) > 0 && Math.abs(e.deltaY) < 50;

      if (hasHorizontalDelta || isSubtleVerticalDelta) {
        e.preventDefault();
        e.stopPropagation();
        // Direct smooth pixel pan
        map.panBy([e.deltaX, e.deltaY], { animate: false });
      }
    };

    // 2. Direct Mouse Click-and-Drag Pan Engine (Guaranteed fallback across all desktop browsers)
    let isMouseDown = false;
    let startX = 0;
    let startY = 0;

    const onMouseDown = (e) => {
      // Left click only (button 0)
      if (e.button !== 0) return;
      // Do not hijack clicks on controls, popups, buttons, inputs, selects, or swipe slider handle
      if (
        e.target.closest('.leaflet-control') ||
        e.target.closest('.leaflet-popup') ||
        e.target.closest('button') ||
        e.target.closest('input') ||
        e.target.closest('select') ||
        e.target.closest('.swipe-slider-handle')
      ) {
        return;
      }

      isMouseDown = true;
      startX = e.clientX;
      startY = e.clientY;
      container.style.cursor = 'grabbing';
    };

    const onMouseMove = (e) => {
      if (!isMouseDown) return;
      const dx = startX - e.clientX;
      const dy = startY - e.clientY;

      if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
        map.panBy([dx, dy], { animate: false });
        startX = e.clientX;
        startY = e.clientY;
      }
    };

    const onMouseUp = () => {
      if (isMouseDown) {
        isMouseDown = false;
        container.style.cursor = 'grab';
      }
    };

    // 3. Keyboard Arrow Keys Pan Handler (Left, Right, Up, Down arrows)
    const onKeyDown = (e) => {
      // Do not pan if typing in an input or select
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'SELECT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      const step = e.shiftKey ? 300 : 120;
      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          map.panBy([-step, 0], { animate: true, duration: 0.2 });
          break;
        case 'ArrowRight':
          e.preventDefault();
          map.panBy([step, 0], { animate: true, duration: 0.2 });
          break;
        case 'ArrowUp':
          e.preventDefault();
          map.panBy([0, -step], { animate: true, duration: 0.2 });
          break;
        case 'ArrowDown':
          e.preventDefault();
          map.panBy([0, step], { animate: true, duration: 0.2 });
          break;
        default:
          break;
      }
    };

    const handleResize = () => map.invalidateSize();

    container.addEventListener('wheel', onWheel, { passive: false });
    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('resize', handleResize);

    return () => {
      container.removeEventListener('wheel', onWheel);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('resize', handleResize);
    };
  }, [map]);

  return null;
};

// 🧭 Professional GIS Pan Navigation Pad (D-Pad: Up, Down, Left, Right, Recenter)
const GISNavigationControl = ({ center, zoom }) => {
  const map = useMap();
  const panStep = 180;

  return (
    <div className="leaflet-top leaflet-left" style={{ marginTop: '80px', marginLeft: '12px', zIndex: 400 }}>
      <div className="bg-space-950/95 border border-cyan-500/40 rounded-xl p-1.5 shadow-glow-cyan backdrop-blur-md flex flex-col items-center gap-1 font-mono">
        <span className="text-[8px] text-cyan-400 font-bold tracking-wider uppercase">PAN / NAV</span>

        {/* Up / North */}
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            map.panBy([0, -panStep], { animate: true, duration: 0.25 });
          }}
          title="Pan North (Up) [↑]"
          className="w-6 h-6 flex items-center justify-center rounded bg-space-900 border border-white/10 hover:border-cyan-400 hover:bg-cyan-950 text-cyan-300 transition-colors cursor-pointer"
        >
          <ArrowUp className="w-3.5 h-3.5" />
        </button>

        {/* Middle Row: Left / West, Recenter / Compass, Right / East */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              map.panBy([-panStep, 0], { animate: true, duration: 0.25 });
            }}
            title="Pan West (Left) [←]"
            className="w-6 h-6 flex items-center justify-center rounded bg-space-900 border border-white/10 hover:border-cyan-400 hover:bg-cyan-950 text-cyan-300 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              map.flyTo(center, zoom, { duration: 0.7 });
            }}
            title="Recenter Scene Extent [Space]"
            className="w-6 h-6 flex items-center justify-center rounded bg-cyan-500/20 border border-cyan-500/50 hover:bg-cyan-500/40 text-cyan-300 transition-colors cursor-pointer"
          >
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
          </button>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              map.panBy([panStep, 0], { animate: true, duration: 0.25 });
            }}
            title="Pan East (Right) [→]"
            className="w-6 h-6 flex items-center justify-center rounded bg-space-900 border border-white/10 hover:border-cyan-400 hover:bg-cyan-950 text-cyan-300 transition-colors cursor-pointer"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Down / South */}
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            map.panBy([0, panStep], { animate: true, duration: 0.25 });
          }}
          title="Pan South (Down) [↓]"
          className="w-6 h-6 flex items-center justify-center rounded bg-space-900 border border-white/10 hover:border-cyan-400 hover:bg-cyan-950 text-cyan-300 transition-colors cursor-pointer"
        >
          <ArrowDown className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

// Capture Map instance for Search flyTo & GPS locate
const CaptureMapInstance = ({ onMap }) => {
  const map = useMap();
  useEffect(() => {
    if (map) onMap(map);
  }, [map, onMap]);
  return null;
};

// Curated Popular Indian Satellite & ISRO Space Center Locations
const POPULAR_LOCATIONS = [
  {
    name: 'Guwahati Scene Extent',
    category: 'ISRO Change Detection Baseline (Assam)',
    lat: 26.1500,
    lon: 91.7400,
    zoom: 13,
  },
  {
    name: 'Brahmaputra River Corridor',
    category: 'Riparian Siltation & Flood Zone',
    lat: 26.1850,
    lon: 91.7350,
    zoom: 14,
  },
  {
    name: 'Sriharikota (SDSC SHAR)',
    category: 'ISRO Spaceport / Launch Pads',
    lat: 13.7199,
    lon: 80.2305,
    zoom: 14,
  },
  {
    name: 'ISRO Headquarters, Bengaluru',
    category: 'Antariksh Bhavan / Mission Control',
    lat: 13.0334,
    lon: 77.5640,
    zoom: 15,
  },
  {
    name: 'NESAC Shillong',
    category: 'North Eastern Space Applications Centre',
    lat: 25.6791,
    lon: 91.9168,
    zoom: 15,
  },
  {
    name: 'New Delhi (National Capital)',
    category: 'Urban Infrastructure / NCR',
    lat: 28.6139,
    lon: 77.2090,
    zoom: 13,
  },
  {
    name: 'Mumbai Marine Corridor',
    category: 'Coastal Maritime / Port',
    lat: 18.9388,
    lon: 72.8354,
    zoom: 13,
  },
];

// Ground-truth fallback sample coordinates for Guwahati / Brahmaputra satellite scene
const DEFAULT_GEOJSON_FEATURES = [
  {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [91.7310, 26.1420],
          [91.7360, 26.1420],
          [91.7375, 26.1465],
          [91.7320, 26.1470],
          [91.7310, 26.1420],
        ],
      ],
    },
    properties: {
      region_index: 1,
      category: 'HUMAN',
      subtype: 'New Building Complex',
      area_m2: 45200.0,
      area_km2: 0.0452,
      perimeter_m: 890.0,
      centroid_lat: 26.1444,
      centroid_lon: 91.7341,
      mean_confidence: 0.94,
      severity_level: 'HIGH',
      label: 'Baseline / Demo Result',
      observation_t1: '2020-01-15',
      observation_t2: '2026-01-15',
      ndvi_t1: 0.74,
      ndvi_t2: 0.16,
      ndbi_t1: -0.22,
      ndbi_t2: +0.64,
      sar_sigma0: '+4.2 dB',
      corroboration: 'Severe canopy defoliation with high-albedo concrete footprint and +4.2 dB double-bounce radar echo.',
    },
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [91.7420, 26.1510],
          [91.7510, 26.1515],
          [91.7505, 26.1540],
          [91.7415, 26.1535],
          [91.7420, 26.1510],
        ],
      ],
    },
    properties: {
      region_index: 2,
      category: 'HUMAN',
      subtype: 'Road Widening Corridor',
      area_m2: 88500.0,
      area_km2: 0.0885,
      perimeter_m: 1950.0,
      centroid_lat: 26.1525,
      centroid_lon: 91.7462,
      mean_confidence: 0.88,
      severity_level: 'MEDIUM',
      label: 'Baseline / Demo Result',
      observation_t1: '2020-01-15',
      observation_t2: '2026-01-15',
      ndvi_t1: 0.62,
      ndvi_t2: 0.20,
      ndbi_t1: -0.15,
      ndbi_t2: +0.55,
      sar_sigma0: '+2.8 dB',
      corroboration: 'Linear asphalt surge corroborates arterial widening with sustained impervious surface reflection.',
    },
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [91.7200, 26.1600],
          [91.7280, 26.1590],
          [91.7320, 26.1660],
          [91.7230, 26.1680],
          [91.7200, 26.1600],
        ],
      ],
    },
    properties: {
      region_index: 3,
      category: 'NATURAL',
      subtype: 'Riparian Siltation Shift',
      area_m2: 142000.0,
      area_km2: 0.1420,
      perimeter_m: 2300.0,
      centroid_lat: 26.1632,
      centroid_lon: 91.7258,
      mean_confidence: 0.79,
      severity_level: 'LOW',
      label: 'Baseline / Demo Result',
      observation_t1: '2020-01-15',
      observation_t2: '2026-01-15',
      ndvi_t1: 0.42,
      ndvi_t2: 0.15,
      ndbi_t1: -0.32,
      ndbi_t2: -0.25,
      sar_sigma0: '-14.6 dB',
      corroboration: 'Silt deposition near sandbar; low SAR backscatter confirms natural sand and water boundary shift.',
    },
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [91.7580, 26.1380],
          [91.7640, 26.1390],
          [91.7630, 26.1430],
          [91.7560, 26.1420],
          [91.7580, 26.1380],
        ],
      ],
    },
    properties: {
      region_index: 4,
      category: 'DISASTER',
      subtype: 'Monsoon Embankment Scour',
      area_m2: 67300.0,
      area_km2: 0.0673,
      perimeter_m: 1120.0,
      centroid_lat: 26.1405,
      centroid_lon: 91.7602,
      mean_confidence: 0.91,
      severity_level: 'CRITICAL',
      label: 'Baseline / Demo Result',
      observation_t1: '2020-01-15',
      observation_t2: '2026-01-15',
      ndvi_t1: 0.55,
      ndvi_t2: 0.08,
      ndbi_t1: -0.40,
      ndbi_t2: -0.35,
      sar_sigma0: '-18.5 dB',
      corroboration: 'Flash inundation scour with specular reflection attenuation in microwave C-Band.',
    },
  },
];

export const MapPage = () => {
  // Layer & Display States
  const [basemap, setBasemap] = useState('dark');
  const [spectralMode, setSpectralMode] = useState('RGB'); // 'RGB' | 'NDVI' | 'NDBI' | 'SAR'
  const [showFootprint, setShowFootprint] = useState(true);
  const [showPolygons, setShowPolygons] = useState(true);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(false);
  const [showCentroids, setShowCentroids] = useState(true);
  const [isChangeOnlyMode, setIsChangeOnlyMode] = useState(false);

  // Split-Screen Swipe Comparison Slider States
  const [isSwipeMode, setIsSwipeMode] = useState(false);
  const [sliderPos, setSliderPos] = useState(50); // percentage 5-95
  const [isDragging, setIsDragging] = useState(false);
  const mapContainerRef = useRef(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [minConfidence, setMinConfidence] = useState(0.5);

  // Data & Selection State
  const [geoData, setGeoData] = useState(DEFAULT_GEOJSON_FEATURES);
  const [selectedFeature, setSelectedFeature] = useState(DEFAULT_GEOJSON_FEATURES[0]);
  const [observationMode, setObservationMode] = useState('both');

  // Google Maps Location Search & Geocoding States
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchPin, setSearchPin] = useState(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const mapInstanceRef = useRef(null);
  const searchDebounceRef = useRef(null);
  const searchContainerRef = useRef(null);

  // GIS Geodesic Measurement Tool States ('none' | 'distance' | 'area')
  const [measureMode, setMeasureMode] = useState('none');
  const [measurePoints, setMeasurePoints] = useState([]);

  const handleAddMeasurePoint = useCallback((pt) => {
    setMeasurePoints((prev) => [...prev, pt]);
  }, []);

  const handleUndoMeasurePoint = () => {
    setMeasurePoints((prev) => prev.slice(0, -1));
  };

  const handleClearMeasure = () => {
    setMeasurePoints([]);
  };

  const handleToggleMeasureMode = (mode) => {
    if (measureMode === mode) {
      setMeasureMode('none');
      setMeasurePoints([]);
    } else {
      setMeasureMode(mode);
      setMeasurePoints([]);
    }
  };

  const totalSurveyDistance = calculateTotalDistance(measurePoints);
  const totalSurveyArea = calculateGeodesicArea(measurePoints);

  // Close search dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target)) {
        setIsSearchOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  // Parse coordinate pattern like "26.15, 91.74" or "26.15 91.74"
  const parseCoordinates = (text) => {
    const match = text.trim().match(/^(-?\d+(\.\d+)?)[,\s]+(-?\d+(\.\d+)?)$/);
    if (match) {
      const lat = parseFloat(match[1]);
      const lon = parseFloat(match[3]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        return { lat, lon };
      }
    }
    return null;
  };

  const handleSearchInputChange = (text) => {
    setSearchQuery(text);
    setIsSearchOpen(true);

    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);

    if (!text.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    // Direct coordinate match
    const coords = parseCoordinates(text);
    if (coords) {
      setSearchResults([
        {
          name: `Coordinates: ${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E`,
          category: 'Direct WGS84 Geographic Coordinate',
          lat: coords.lat,
          lon: coords.lon,
          zoom: 15,
        },
      ]);
      return;
    }

    // Local curated Indian Satellite landmarks match
    const qLower = text.toLowerCase();
    const localMatches = POPULAR_LOCATIONS.filter(
      (l) => l.name.toLowerCase().includes(qLower) || l.category.toLowerCase().includes(qLower)
    );

    // Live Geocoding via Nominatim OpenStreetMap API
    searchDebounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(text)}&limit=5&addressdetails=1`,
          { headers: { 'Accept-Language': 'en' } }
        );
        if (res.ok) {
          const data = await res.json();
          const remoteResults = data.map((item) => ({
            name: item.display_name.split(',')[0],
            category: item.display_name,
            lat: parseFloat(item.lat),
            lon: parseFloat(item.lon),
            zoom: item.type === 'city' ? 12 : item.type === 'administrative' ? 10 : 15,
          }));

          const merged = [...localMatches];
          remoteResults.forEach((r) => {
            if (!merged.some((m) => Math.abs(m.lat - r.lat) < 0.01 && Math.abs(m.lon - r.lon) < 0.01)) {
              merged.push(r);
            }
          });
          setSearchResults(merged);
        } else {
          setSearchResults(localMatches);
        }
      } catch {
        setSearchResults(localMatches);
      } finally {
        setIsSearching(false);
      }
    }, 350);
  };

  const handleSelectLocation = (loc) => {
    setSearchPin(loc);
    setSearchQuery(loc.name);
    setIsSearchOpen(false);

    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([loc.lat, loc.lon], loc.zoom || 14, { duration: 1.2 });
    }
  };

  const handleSearchSubmit = () => {
    if (searchResults.length > 0) {
      handleSelectLocation(searchResults[0]);
    } else if (searchQuery.trim()) {
      const coords = parseCoordinates(searchQuery);
      if (coords) {
        handleSelectLocation({
          name: `Coordinates: ${coords.lat.toFixed(4)}°N, ${coords.lon.toFixed(4)}°E`,
          category: 'Direct WGS84 Geographic Coordinate',
          lat: coords.lat,
          lon: coords.lon,
          zoom: 15,
        });
      }
    }
  };

  const handleCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }
    setIsSearching(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsSearching(false);
        handleSelectLocation({
          name: 'My Current Location (GPS)',
          category: `Device Telemetry (Accuracy ±${Math.round(pos.coords.accuracy)}m)`,
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          zoom: 15,
        });
      },
      (err) => {
        setIsSearching(false);
        alert(`Location access failed: ${err.message}`);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Footprint bounding coordinates
  const footprintBounds = [
    [26.1300, 91.7100],
    [26.1750, 91.7750],
  ];

  useEffect(() => {
    const fetchPolygons = async () => {
      try {
        const res = await getAnalysisChangePolygons('AN-ISRO-DEMO');
        if (res && res.features && res.features.length > 0) {
          setGeoData(res.features);
          setSelectedFeature(res.features[0]);
        }
      } catch {
        // Fallback to default geo features
      }
    };
    fetchPolygons();
  }, []);

  // Mouse & Touch Drag Handlers for Swipe Slider
  const handleDragMove = useCallback(
    (clientX) => {
      if (!mapContainerRef.current) return;
      const rect = mapContainerRef.current.getBoundingClientRect();
      const relativeX = clientX - rect.left;
      const percentage = (relativeX / rect.width) * 100;
      setSliderPos(Math.max(5, Math.min(95, percentage)));
    },
    []
  );

  useEffect(() => {
    const onMouseMove = (e) => {
      if (!isDragging) return;
      handleDragMove(e.clientX);
    };

    const onTouchMove = (e) => {
      if (!isDragging || !e.touches[0]) return;
      handleDragMove(e.touches[0].clientX);
    };

    const onStopDrag = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onStopDrag);
      window.addEventListener('touchmove', onTouchMove);
      window.addEventListener('touchend', onStopDrag);
    }

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onStopDrag);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('touchend', onStopDrag);
    };
  }, [isDragging, handleDragMove]);

  // Filter features
  const filteredFeatures = geoData.filter((f) => {
    const matchCat =
      selectedCategory === 'ALL' || f.properties.category === selectedCategory;
    const matchSev =
      selectedSeverity === 'ALL' || f.properties.severity_level === selectedSeverity;
    const matchConf = f.properties.mean_confidence >= minConfidence;
    return matchCat && matchSev && matchConf;
  });

  const getCategoryColor = (cat) => {
    switch (cat) {
      case 'HUMAN':
        return '#06b6d4'; // Cyan
      case 'NATURAL':
        return '#10b981'; // Emerald
      case 'DISASTER':
        return '#f43f5e'; // Rose
      case 'ATMOSPHERIC':
        return '#a855f7'; // Purple
      default:
        return '#f59e0b'; // Amber
    }
  };

  const getTileLayerUrl = () => {
    if (isChangeOnlyMode) {
      return 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
    }
    switch (basemap) {
      case 'satellite':
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      case 'street':
        return 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
      case 'dark':
      default:
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
    }
  };

  const getTileLayerAttribution = () => {
    switch (basemap) {
      case 'satellite':
        return '&copy; <a href="https://www.esri.com/">Esri</a>, Maxar, Earthstar Geographics / ISRO';
      case 'street':
        return '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors / ISRO';
      case 'dark':
      default:
        return '&copy; <a href="https://www.esri.com/">Esri</a>, DeLorme, NAVTEQ / ISRO';
    }
  };

  // Spectral CSS shader filters for realistic multi-spectral emulation
  const getSpectralFilterStyle = () => {
    switch (spectralMode) {
      case 'NDVI':
        // Shifts green biomass to deep emerald, barren to ochre, water to deep navy
        return {
          filter: 'contrast(145%) saturate(220%) hue-rotate(65deg) brightness(95%)',
        };
      case 'NDBI':
        // High-contrast built-up emulation: turns vegetation to dark slate, concrete to bright cyan/orange
        return {
          filter: 'contrast(165%) brightness(90%) hue-rotate(185deg) saturate(180%)',
        };
      case 'SAR':
        // C-Band microwave radar backscatter: monochrome speckle with high-intensity metallic returns
        return {
          filter: 'grayscale(100%) contrast(220%) brightness(85%)',
        };
      case 'RGB':
      default:
        return {
          filter: 'saturate(115%) contrast(105%)',
        };
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Header & Telemetry */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 glass-panel rounded-xl">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <MapPin className="w-5 h-5 text-cyan-400" />
            Interactive Geospatial Satellite Change Map
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            COORDINATE SYSTEM: EPSG:4326 (WGS84) • SATELLITE EXTENT: 26.13°N - 26.17°N, 91.71°E - 91.77°E
          </p>
        </div>

        {/* Observation, Swipe & Mode Toggles */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Split-Screen Swipe Mode Toggle Button */}
          <Button
            variant={isSwipeMode ? 'primary' : 'outline'}
            size="sm"
            icon={SlidersHorizontal}
            onClick={() => {
              setIsSwipeMode(!isSwipeMode);
              if (!isSwipeMode) setObservationMode('both');
            }}
            className={isSwipeMode ? 'shadow-glow-cyan' : ''}
          >
            {isSwipeMode ? 'Swipe Split-Screen (ACTIVE)' : 'Swipe Comparison Slider'}
          </Button>

          {/* Standard Observation T1 / T2 Toggle (Disabled during Swipe Mode) */}
          {!isSwipeMode && (
            <div className="flex rounded-lg bg-space-900 border border-white/10 p-1">
              <button
                onClick={() => setObservationMode('both')}
                className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${
                  observationMode === 'both'
                    ? 'bg-cyan-500 text-space-950 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Overlay (T1 + T2)
              </button>
              <button
                onClick={() => setObservationMode('t1')}
                className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${
                  observationMode === 't1'
                    ? 'bg-cyan-500 text-space-950 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                T1 (Baseline 2020)
              </button>
              <button
                onClick={() => setObservationMode('t2')}
                className={`px-2.5 py-1 text-xs font-mono rounded transition-colors ${
                  observationMode === 't2'
                    ? 'bg-cyan-500 text-space-950 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                T2 (Current 2026)
              </button>
            </div>
          )}

          {/* Change-Only Mode Button */}
          <Button
            variant={isChangeOnlyMode ? 'danger' : 'outline'}
            size="sm"
            icon={Eye}
            onClick={() => setIsChangeOnlyMode(!isChangeOnlyMode)}
          >
            {isChangeOnlyMode ? 'Change-Only (ACTIVE)' : 'Change-Only'}
          </Button>

          {/* 📏 Geodesic Distance Measuring Tool */}
          <Button
            variant={measureMode === 'distance' ? 'primary' : 'outline'}
            size="sm"
            icon={Ruler}
            onClick={() => handleToggleMeasureMode('distance')}
            className={measureMode === 'distance' ? 'shadow-glow-cyan' : ''}
          >
            {measureMode === 'distance' ? 'Ruler (ACTIVE)' : 'Distance'}
          </Button>

          {/* 📐 Geodesic Polygon Area Measuring Tool */}
          <Button
            variant={measureMode === 'area' ? 'primary' : 'outline'}
            size="sm"
            icon={Square}
            onClick={() => handleToggleMeasureMode('area')}
            className={measureMode === 'area' ? 'shadow-glow-cyan' : ''}
          >
            {measureMode === 'area' ? 'Area (ACTIVE)' : 'Area'}
          </Button>
        </div>
      </div>

      {/* 🛰️ Dedicated Spectral Index Switcher Toolbar */}
      <div className="p-3.5 glass-panel rounded-xl font-mono text-xs flex flex-col md:flex-row md:items-center justify-between gap-3 border border-cyan-500/30">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse shrink-0" />
          <span className="font-bold text-white tracking-wider text-[11px] uppercase">
            Spectral Index Switcher:
          </span>
          <span className="text-slate-400 text-[10px] hidden sm:inline">
            Multi-spectral band math & microwave radar products
          </span>
        </div>

        {/* 4 Spectral Mode Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 bg-space-950/80 p-1 rounded-lg border border-white/10">
          <button
            onClick={() => setSpectralMode('RGB')}
            className={`px-2.5 py-1 rounded text-xs transition flex items-center gap-1.5 ${
              spectralMode === 'RGB'
                ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/50 shadow-glow-cyan'
                : 'text-slate-400 hover:text-white hover:bg-space-900'
            }`}
            title="Cartosat-3 & Sentinel-2 Optical True-Color (B4, B3, B2)"
          >
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>RGB True-Color</span>
          </button>

          <button
            onClick={() => setSpectralMode('NDVI')}
            className={`px-2.5 py-1 rounded text-xs transition flex items-center gap-1.5 ${
              spectralMode === 'NDVI'
                ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/50 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
                : 'text-slate-400 hover:text-white hover:bg-space-900'
            }`}
            title="Normalized Difference Vegetation Index: (NIR - Red) / (NIR + Red)"
          >
            <Trees className="w-3 h-3 text-emerald-400" />
            <span>NDVI (Vegetation)</span>
          </button>

          <button
            onClick={() => setSpectralMode('NDBI')}
            className={`px-2.5 py-1 rounded text-xs transition flex items-center gap-1.5 ${
              spectralMode === 'NDBI'
                ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/50 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
                : 'text-slate-400 hover:text-white hover:bg-space-900'
            }`}
            title="Normalized Difference Built-up Index: (SWIR - NIR) / (SWIR + NIR)"
          >
            <Building2 className="w-3 h-3 text-amber-400" />
            <span>NDBI (Built-Up)</span>
          </button>

          <button
            onClick={() => setSpectralMode('SAR')}
            className={`px-2.5 py-1 rounded text-xs transition flex items-center gap-1.5 ${
              spectralMode === 'SAR'
                ? 'bg-purple-500/20 text-purple-300 font-bold border border-purple-500/50 shadow-[0_0_12px_rgba(168,85,247,0.3)]'
                : 'text-slate-400 hover:text-white hover:bg-space-900'
            }`}
            title="EOS-04 / RISAT-1A Microwave Radar Backscatter (σ⁰ dB)"
          >
            <Radio className="w-3 h-3 text-purple-400" />
            <span>SAR Radar σ⁰</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-3.5 glass-panel rounded-xl text-xs font-mono">
        {/* Category Filter */}
        <div>
          <label className="text-slate-400 block mb-1 text-[11px]">CATEGORY FILTER:</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full p-1.5 rounded bg-space-900 border border-white/10 text-slate-200 text-xs"
          >
            <option value="ALL">All Categories ({geoData.length})</option>
            <option value="HUMAN">Human Activity</option>
            <option value="NATURAL">Natural / Environmental</option>
            <option value="DISASTER">Disaster / Inundation</option>
            <option value="ATMOSPHERIC">Atmospheric / Cloud</option>
          </select>
        </div>

        {/* Severity Filter */}
        <div>
          <label className="text-slate-400 block mb-1 text-[11px]">SEVERITY FILTER:</label>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="w-full p-1.5 rounded bg-space-900 border border-white/10 text-slate-200 text-xs"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Confidence Filter */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-slate-400">MIN CONFIDENCE:</span>
            <span className="text-cyan-400">{Math.round(minConfidence * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.4"
            max="0.95"
            step="0.05"
            value={minConfidence}
            onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer"
          />
        </div>

        {/* Basemap Switcher */}
        <div>
          <label className="text-slate-400 block mb-1 text-[11px]">BASEMAP STYLE:</label>
          <div className="flex rounded bg-space-900 border border-white/10 p-0.5">
            <button
              onClick={() => setBasemap('dark')}
              className={`flex-1 py-1 rounded text-[11px] ${
                basemap === 'dark' ? 'bg-space-800 text-cyan-300 font-bold' : 'text-slate-400'
              }`}
            >
              Dark GIS
            </button>
            <button
              onClick={() => setBasemap('satellite')}
              className={`flex-1 py-1 rounded text-[11px] ${
                basemap === 'satellite' ? 'bg-space-800 text-cyan-300 font-bold' : 'text-slate-400'
              }`}
            >
              Satellite
            </button>
            <button
              onClick={() => setBasemap('street')}
              className={`flex-1 py-1 rounded text-[11px] ${
                basemap === 'street' ? 'bg-space-800 text-cyan-300 font-bold' : 'text-slate-400'
              }`}
            >
              Street
            </button>
          </div>
        </div>
      </div>

      {/* 🗺️ Google Maps Style Location Search & Geocoding Bar */}
      <div
        ref={searchContainerRef}
        className="relative p-3 bg-space-950/90 border border-cyan-500/40 rounded-xl shadow-glow-cyan backdrop-blur-md space-y-2.5 z-[500]"
      >
        <div className="flex flex-col md:flex-row items-center gap-2.5">
          {/* Autocomplete Input */}
          <div className="relative flex-1 w-full">
            <div className="flex items-center gap-2.5 px-3 py-2 bg-space-900 border border-white/15 rounded-lg focus-within:border-cyan-400 focus-within:shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all">
              <Search className="w-4 h-4 text-cyan-400 shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearchInputChange(e.target.value)}
                onFocus={() => setIsSearchOpen(true)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSearchSubmit();
                  if (e.key === 'Escape') setIsSearchOpen(false);
                }}
                placeholder="Search any city, landmark, or lat,lon (e.g. Guwahati, Sriharikota, Delhi, 26.15, 91.74)..."
                className="bg-transparent text-xs text-white placeholder-slate-400 w-full focus:outline-none font-mono"
              />
              {isSearching && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />}
              {searchQuery && !isSearching && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    setSearchResults([]);
                    setSearchPin(null);
                  }}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Google Maps Autocomplete Dropdown */}
            {isSearchOpen && (searchResults.length > 0 || isSearching) && (
              <div className="absolute top-full left-0 right-0 mt-1.5 bg-space-950/98 border border-cyan-500/40 rounded-xl shadow-2xl backdrop-blur-xl z-[600] max-h-72 overflow-y-auto font-mono text-xs divide-y divide-white/5">
                {searchResults.map((res, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectLocation(res)}
                    className="w-full text-left px-3.5 py-2.5 hover:bg-cyan-950/60 hover:text-cyan-300 flex items-start gap-2.5 transition-colors cursor-pointer"
                  >
                    <MapPin className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-slate-100 truncate text-xs">{res.name}</div>
                      <div className="text-[10px] text-slate-400 truncate">{res.category}</div>
                      <div className="text-[9px] text-cyan-400 font-mono mt-0.5">
                        {res.lat.toFixed(4)}°N, {res.lon.toFixed(4)}°E
                      </div>
                    </div>
                    <Navigation className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-1" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons: Search & GPS Location */}
          <div className="flex items-center gap-2 w-full md:w-auto">
            <Button
              variant="primary"
              size="sm"
              icon={Search}
              onClick={handleSearchSubmit}
              className="flex-1 md:flex-initial shadow-glow-cyan"
            >
              Search
            </Button>

            <button
              type="button"
              onClick={handleCurrentLocation}
              title="Locate My Position via GPS"
              className="px-3 py-2 rounded-lg bg-space-900 border border-white/15 hover:border-cyan-400 hover:bg-cyan-950 text-cyan-300 hover:text-cyan-200 text-xs font-mono flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <LocateFixed className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span className="hidden sm:inline">My Location</span>
            </button>

            {searchPin && (
              <button
                type="button"
                onClick={() => setSearchPin(null)}
                title="Clear Active Search Pin"
                className="px-2.5 py-2 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 hover:bg-rose-900/60 text-xs font-mono transition-colors cursor-pointer"
              >
                Clear Pin
              </button>
            )}
          </div>
        </div>

        {/* Quick Landmark Jump Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-white/10 font-mono text-[11px]">
          <span className="text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1">
            <Globe className="w-3 h-3 text-cyan-400" />
            ISRO / Key Sites:
          </span>
          {POPULAR_LOCATIONS.map((loc, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSelectLocation(loc)}
              className={`px-2 py-0.5 rounded-full border text-[10px] transition-colors cursor-pointer ${
                searchPin?.name === loc.name
                  ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200 font-bold shadow-glow-cyan'
                  : 'bg-space-900 border-white/10 hover:border-cyan-400/60 hover:bg-cyan-950/50 text-slate-300 hover:text-cyan-300'
              }`}
            >
              {loc.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Map Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Map Canvas (3 cols) */}
        <div
          ref={mapContainerRef}
          className="lg:col-span-3 h-[640px] rounded-xl overflow-hidden bg-space-950/80 border border-white/10 relative select-none"
        >
          {/* Active Split-Screen Swipe Top HUD */}
          {isSwipeMode && (
            <div className="absolute top-4 left-4 right-4 z-[450] flex items-center justify-between pointer-events-none">
              {/* T1 Baseline Pill */}
              <div className="px-3 py-1.5 rounded-lg bg-space-950/90 border border-cyan-500/40 shadow-glow-cyan text-xs font-mono text-cyan-300 flex items-center gap-2 backdrop-blur-md">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span>BEFORE (T1): <strong>2020-01-15 Baseline</strong></span>
              </div>

              {/* Quick Jump Position Presets */}
              <div className="pointer-events-auto hidden sm:flex items-center gap-1.5 p-1 rounded-lg bg-space-950/90 border border-white/10 backdrop-blur-md font-mono text-[11px]">
                <button
                  onClick={() => setSliderPos(25)}
                  className="px-2 py-0.5 rounded hover:bg-white/10 text-slate-300 transition-colors"
                >
                  25%
                </button>
                <button
                  onClick={() => setSliderPos(50)}
                  className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30"
                >
                  50% Center
                </button>
                <button
                  onClick={() => setSliderPos(75)}
                  className="px-2 py-0.5 rounded hover:bg-white/10 text-slate-300 transition-colors"
                >
                  75%
                </button>
              </div>

              {/* T2 Monitoring Pill */}
              <div className="px-3 py-1.5 rounded-lg bg-space-950/90 border border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.25)] text-xs font-mono text-amber-300 flex items-center gap-2 backdrop-blur-md">
                <span>AFTER (T2): <strong>2026-01-15 Current</strong></span>
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              </div>
            </div>
          )}

          {/* 📍 Live Spectral Cursor Probe Pill (Top-Left under swipe HUD) */}
          <div className="absolute top-4 left-4 z-[420] pointer-events-none hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-space-950/90 border border-cyan-500/40 shadow-glow-cyan backdrop-blur-md font-mono text-[10px]">
            <Crosshair className="w-3.5 h-3.5 text-cyan-400 animate-pulse shrink-0" />
            <span className="text-slate-400">PROBE:</span>
            <div id="spectral-probe-telemetry" className="flex items-center gap-2">
              <span className="text-white font-bold">26.1444°N, 91.7341°E</span>
              <span className="text-slate-600">|</span>
              <span className="text-emerald-400">NDVI: 0.68</span>
              <span className="text-slate-600">|</span>
              <span className="text-amber-400">NDBI: -0.18</span>
              <span className="text-slate-600">|</span>
              <span className="text-purple-400">SAR: -11.8 dB</span>
              <span className="text-slate-600">|</span>
              <span className="text-cyan-300">[Dense Canopy]</span>
            </div>
          </div>

          {/* 📏 Interactive GIS Survey Measurement Floating HUD */}
          {measureMode !== 'none' && (
            <div className="absolute top-14 left-4 z-[430] p-3.5 rounded-xl bg-space-950/95 border border-cyan-500/50 shadow-glow-cyan backdrop-blur-md font-mono text-xs max-w-xs space-y-2.5">
              <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-2">
                <div className="flex items-center gap-2">
                  {measureMode === 'distance' ? (
                    <Ruler className="w-4 h-4 text-cyan-400" />
                  ) : (
                    <Square className="w-4 h-4 text-amber-400" />
                  )}
                  <span className="font-bold text-white uppercase text-[11px]">
                    {measureMode === 'distance' ? 'Geodesic Distance Ruler' : 'Geodesic Area Survey'}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggleMeasureMode(measureMode)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-1">
                {measureMode === 'distance' ? (
                  <div>
                    <div className="text-[10px] text-slate-400">TOTAL CUMULATIVE DISTANCE:</div>
                    <div className="text-base font-bold text-cyan-400">
                      {totalSurveyDistance >= 1000
                        ? `${(totalSurveyDistance / 1000).toFixed(2)} km (${Math.round(totalSurveyDistance).toLocaleString()} m)`
                        : `${Math.round(totalSurveyDistance).toLocaleString()} m`}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="text-[10px] text-slate-400">ENCLOSED GEODESIC AREA:</div>
                    <div className="text-base font-bold text-amber-400">
                      {totalSurveyArea >= 1000000
                        ? `${(totalSurveyArea / 1000000).toFixed(3)} km² (${(totalSurveyArea / 10000).toFixed(2)} ha)`
                        : totalSurveyArea >= 10000
                        ? `${(totalSurveyArea / 10000).toFixed(2)} ha (${Math.round(totalSurveyArea).toLocaleString()} m²)`
                        : `${Math.round(totalSurveyArea).toLocaleString()} m²`}
                    </div>
                  </div>
                )}
                <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1">
                  <span>Vertices pinned: <strong className="text-white">{measurePoints.length}</strong></span>
                  <span className="text-cyan-300 animate-pulse">
                    {measurePoints.length === 0
                      ? 'Click map to place'
                      : measureMode === 'area' && measurePoints.length < 3
                      ? 'Need 3+ points'
                      : 'Click to extend'}
                  </span>
                </div>
              </div>

              {measurePoints.length > 0 && (
                <div className="flex items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleUndoMeasurePoint}
                    className="flex-1 flex items-center justify-center gap-1 py-1 px-2 rounded bg-space-900 hover:bg-space-800 text-slate-300 text-[10px] border border-white/10"
                  >
                    <Undo className="w-3 h-3" />
                    <span>Undo</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleClearMeasure}
                    className="flex-1 flex items-center justify-center gap-1 py-1 px-2 rounded bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 text-[10px] border border-rose-500/30"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Reset</span>
                  </button>
                </div>
              )}
            </div>
          )}

          <div className={`w-full h-full spectral-${spectralMode.toLowerCase()}`}>
            <MapContainer
              center={INITIAL_MAP_CENTER}
              zoom={13}
              scrollWheelZoom={true}
              dragging={true}
              doubleClickZoom={true}
              touchZoom={true}
              style={{ width: '100%', height: '100%' }}
            >
              <EnableMapDragging />
              <MapEventsListener />
              <GISNavigationControl center={INITIAL_MAP_CENTER} zoom={13} />

              {/* Primary Base TileLayer */}
              <TileLayer
                key={`${basemap}-${isChangeOnlyMode}-${spectralMode}`}
                attribution={getTileLayerAttribution()}
                url={getTileLayerUrl()}
              />

              {/* Satellite Raster Footprint Envelope (non-interactive so it never blocks dragging) */}
              {showFootprint && (
                <Rectangle
                  bounds={footprintBounds}
                  interactive={false}
                  pathOptions={{
                    interactive: false,
                    color: spectralMode === 'NDVI' ? '#10b981' : spectralMode === 'NDBI' ? '#f59e0b' : '#06b6d4',
                    weight: 2,
                    dashArray: '6, 6',
                    fillOpacity: spectralMode === 'RGB' ? 0.03 : 0.12,
                    fillColor: spectralMode === 'NDVI' ? '#10b981' : spectralMode === 'NDBI' ? '#f59e0b' : '#06b6d4',
                  }}
                />
              )}

              {/* Change Polygons Layer */}
              {showPolygons &&
                observationMode !== 't1' &&
                filteredFeatures.map((feat) => {
                  const color = getCategoryColor(feat.properties.category);
                  const isSelected = selectedFeature?.properties.region_index === feat.properties.region_index;

                  return (
                    <GeoJSON
                      key={`poly-${feat.properties.region_index}-${selectedCategory}-${minConfidence}-${isSwipeMode}-${spectralMode}`}
                      data={feat.geometry}
                      style={{
                        color: isSelected ? '#ffffff' : color,
                        weight: isSelected ? 3 : 2,
                        fillColor: color,
                        fillOpacity: isSelected ? 0.65 : 0.4,
                      }}
                      eventHandlers={{
                        click: () => setSelectedFeature(feat),
                      }}
                    />
                  );
                })}

              {/* Bounding Boxes Layer (non-interactive) */}
              {showBoundingBoxes &&
                filteredFeatures.map((feat) => {
                  const coords = feat.geometry.coordinates[0];
                  if (!coords || coords.length === 0) return null;
                  const lons = coords.map((c) => c[0]);
                  const lats = coords.map((c) => c[1]);
                  const b = [
                    [Math.min(...lats), Math.min(...lons)],
                    [Math.max(...lats), Math.max(...lons)],
                  ];
                  return (
                    <Rectangle
                      key={`bbox-${feat.properties.region_index}`}
                      bounds={b}
                      interactive={false}
                      pathOptions={{
                        interactive: false,
                        color: '#f59e0b',
                        weight: 1,
                        dashArray: '4, 4',
                        fillOpacity: 0.0,
                      }}
                    />
                  );
                })}

              {/* Centroids Markers Layer */}
              {showCentroids &&
                filteredFeatures.map((feat) => {
                  const color = getCategoryColor(feat.properties.category);
                  return (
                    <CircleMarker
                      key={`cent-${feat.properties.region_index}`}
                      center={[feat.properties.centroid_lat, feat.properties.centroid_lon]}
                      radius={5}
                      pathOptions={{
                        color: '#ffffff',
                        weight: 1.5,
                        fillColor: color,
                        fillOpacity: 1.0,
                      }}
                      eventHandlers={{
                        click: () => setSelectedFeature(feat),
                      }}
                    >
                      <Popup className="custom-leaflet-popup">
                        <div className="text-xs p-1 space-y-1 font-mono text-space-950">
                          <div className="font-bold text-sm">Region #{feat.properties.region_index}</div>
                          <div>Category: {feat.properties.category}</div>
                          <div>Subtype: {feat.properties.subtype}</div>
                          <div>Area: {feat.properties.area_m2.toLocaleString()} m²</div>
                          <div>Confidence: {Math.round(feat.properties.mean_confidence * 100)}%</div>
                          <div>NDVI: {feat.properties.ndvi_t2 ?? 0.2} | NDBI: {feat.properties.ndbi_t2 ?? +0.55}</div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}

              <CaptureMapInstance onMap={(m) => { mapInstanceRef.current = m; }} />

              {/* 📍 Google Maps Search Location Marker & Pin */}
              {searchPin && (
                <>
                  <CircleMarker
                    center={[searchPin.lat, searchPin.lon]}
                    radius={22}
                    pathOptions={{
                      color: '#06b6d4',
                      fillColor: '#06b6d4',
                      fillOpacity: 0.18,
                      weight: 1.5,
                      dashArray: '4, 4',
                    }}
                  />
                  <CircleMarker
                    center={[searchPin.lat, searchPin.lon]}
                    radius={9}
                    pathOptions={{
                      color: '#ffffff',
                      fillColor: '#ef4444', // Google Maps style red pin
                      fillOpacity: 1.0,
                      weight: 2.5,
                    }}
                  >
                    <Popup className="custom-leaflet-popup" autoPan={true}>
                      <div className="text-xs p-1 space-y-1 font-mono text-space-950 min-w-[210px]">
                        <div className="font-bold text-sm text-cyan-950 flex items-center gap-1.5">
                          <MapPin className="w-4 h-4 text-rose-500 shrink-0" />
                          <span>{searchPin.name}</span>
                        </div>
                        <div className="text-[11px] text-slate-600 line-clamp-2">{searchPin.category}</div>
                        <div className="pt-1.5 border-t border-slate-200 text-[10px] text-slate-700 flex justify-between font-bold">
                          <span className="text-cyan-800">LAT: {searchPin.lat.toFixed(4)}°N</span>
                          <span className="text-cyan-800">LON: {searchPin.lon.toFixed(4)}°E</span>
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                </>
              )}

              {/* 📐 Survey Measurement Click Event Interceptor */}
              <MapMeasurementEvents
                measureMode={measureMode}
                onAddPoint={handleAddMeasurePoint}
              />

              {/* Distance Mode Polyline */}
              {measureMode === 'distance' && measurePoints.length >= 2 && (
                <Polyline
                  positions={measurePoints}
                  pathOptions={{
                    color: '#06b6d4',
                    weight: 3.5,
                    dashArray: '6, 6',
                    opacity: 0.9,
                  }}
                />
              )}

              {/* Area Mode Enclosed Polygon */}
              {measureMode === 'area' && measurePoints.length >= 3 && (
                <Polygon
                  positions={measurePoints}
                  pathOptions={{
                    color: '#f59e0b',
                    fillColor: '#f59e0b',
                    fillOpacity: 0.25,
                    weight: 2.5,
                    dashArray: '5, 5',
                  }}
                />
              )}

              {/* Measurement Vertices Pins */}
              {measureMode !== 'none' &&
                measurePoints.map((pt, idx) => (
                  <CircleMarker
                    key={`survey-pt-${idx}-${pt[0]}-${pt[1]}`}
                    center={pt}
                    radius={6}
                    pathOptions={{
                      color: '#ffffff',
                      fillColor: measureMode === 'distance' ? '#06b6d4' : '#f59e0b',
                      fillOpacity: 1,
                      weight: 2,
                    }}
                  >
                    <Tooltip
                      permanent
                      direction="top"
                      offset={[0, -6]}
                      className="custom-leaflet-tooltip font-mono text-[10px] font-bold"
                    >
                      P{idx + 1}
                    </Tooltip>
                  </CircleMarker>
                ))}
            </MapContainer>
          </div>

          {/* Swipe Mode Split Mask Overlay */}
          {isSwipeMode && (
            <>
              {/* Left Mask Curtain */}
              <div
                className="absolute inset-0 z-[350] pointer-events-none bg-emerald-950/10 border-r border-cyan-400"
                style={{
                  clipPath: `inset(0 ${100 - sliderPos}% 0 0)`,
                }}
              />

              {/* Vertical Drag Line Divider */}
              <div
                className="absolute top-0 bottom-0 z-[460] w-1 bg-gradient-to-b from-cyan-400 via-indigo-400 to-cyan-400 shadow-[0_0_15px_#06b6d4] pointer-events-none"
                style={{ left: `${sliderPos}%` }}
              />

              {/* Central Glowing Draggable Swipe Handle */}
              <div
                onMouseDown={() => setIsDragging(true)}
                onTouchStart={() => setIsDragging(true)}
                className="swipe-slider-handle absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-[470] w-10 h-10 rounded-full bg-space-950 border-2 border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.8)] flex items-center justify-center cursor-ew-resize text-cyan-300 hover:scale-110 active:scale-95 transition-transform"
                style={{ left: `${sliderPos}%` }}
                title="Drag left/right to compare Before vs After satellite observation"
              >
                <MoveHorizontal className="w-5 h-5 text-cyan-300 animate-pulse" />
              </div>
            </>
          )}

          {/* 📊 Dynamic Floating Spectral Color-Ramp Legend */}
          <div className="absolute bottom-4 left-4 z-[400] glass-panel p-3 rounded-lg border border-white/10 text-xs font-mono space-y-2 backdrop-blur-md max-w-xs">
            <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                {spectralMode === 'RGB' && 'Optical Composite'}
                {spectralMode === 'NDVI' && 'NDVI Canopy Scale'}
                {spectralMode === 'NDBI' && 'NDBI Built-Up Scale'}
                {spectralMode === 'SAR' && 'C-Band Radar Backscatter (σ⁰)'}
              </span>
              <span className="text-cyan-300 font-bold">{spectralMode}</span>
            </div>

            {spectralMode === 'RGB' && (
              <div className="space-y-1 text-[10px] text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-sm bg-cyan-400" />
                  <span>Band 4 (Red) • Band 3 (Green) • Band 2 (Blue)</span>
                </div>
                <div className="text-slate-500">Natural optical surface reflection</div>
              </div>
            )}

            {spectralMode === 'NDVI' && (
              <div className="space-y-1.5">
                {/* Continuous Color-Ramp Bar */}
                <div className="h-3 rounded w-full bg-gradient-to-r from-red-600 via-yellow-400 to-emerald-500 border border-white/20" />
                <div className="flex items-center justify-between text-[9px] text-slate-400 font-mono">
                  <span>-1.0 (Water)</span>
                  <span>0.0 (Barren)</span>
                  <span>+0.4 (Grass)</span>
                  <span className="text-emerald-400 font-bold">+1.0 (Canopy)</span>
                </div>
              </div>
            )}

            {spectralMode === 'NDBI' && (
              <div className="space-y-1.5">
                {/* Built-up Ramp */}
                <div className="h-3 rounded w-full bg-gradient-to-r from-emerald-800 via-slate-700 via-cyan-400 to-amber-500 border border-white/20" />
                <div className="flex items-center justify-between text-[9px] text-slate-400 font-mono">
                  <span>-1.0 (Canopy)</span>
                  <span>0.0 (Soil)</span>
                  <span className="text-cyan-400 font-bold">+0.5 (Built-Up)</span>
                  <span className="text-amber-400 font-bold">+1.0 (Core)</span>
                </div>
              </div>
            )}

            {spectralMode === 'SAR' && (
              <div className="space-y-1.5">
                {/* Microwave SAR Ramp */}
                <div className="h-3 rounded w-full bg-gradient-to-r from-slate-950 via-slate-600 via-amber-200 to-white border border-white/20" />
                <div className="flex items-center justify-between text-[9px] text-slate-400 font-mono">
                  <span>-25 dB (Water)</span>
                  <span>-12 dB (Diffuse)</span>
                  <span className="text-amber-300 font-bold">+8 dB (Concrete)</span>
                </div>
              </div>
            )}

            {/* Taxonomy Dots */}
            <div className="pt-1 border-t border-white/5 grid grid-cols-2 gap-1 text-[10px]">
              <div className="flex items-center gap-1.5 text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                <span>Human</span>
              </div>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>Natural</span>
              </div>
              <div className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                <span>Disaster</span>
              </div>
              <div className="flex items-center gap-1.5 text-purple-400">
                <span className="w-2 h-2 rounded-full bg-purple-400" />
                <span>Atmospheric</span>
              </div>
            </div>
          </div>

          {/* Floating Layer Controls (Top Right) */}
          <div className="absolute top-16 right-4 z-[400] glass-panel p-2.5 rounded-lg border border-white/10 text-[11px] font-mono space-y-2 backdrop-blur-md">
            <div className="text-[10px] text-slate-400 uppercase font-bold">GIS Layers</div>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showFootprint}
                onChange={(e) => setShowFootprint(e.target.checked)}
                className="accent-cyan-400"
              />
              <span>Image Footprint</span>
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showPolygons}
                onChange={(e) => setShowPolygons(e.target.checked)}
                className="accent-cyan-400"
              />
              <span>Change Polygons</span>
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showBoundingBoxes}
                onChange={(e) => setShowBoundingBoxes(e.target.checked)}
                className="accent-cyan-400"
              />
              <span>Bounding Boxes</span>
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={showCentroids}
                onChange={(e) => setShowCentroids(e.target.checked)}
                className="accent-cyan-400"
              />
              <span>Centroid Markers</span>
            </label>
          </div>
        </div>

        {/* Feature Inspector & Polygon Details Panel (1 col) */}
        <div className="space-y-4">
          <Card title="Feature Inspector" subtitle="Selected polygon telemetry" glow="cyan">
            {selectedFeature ? (
              <div className="space-y-3.5 text-xs font-mono">
                {/* Header with Change ID & Category */}
                <div className="p-3 rounded-lg bg-space-900 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 text-[11px]">CHANGE REGION:</span>
                    <span className="text-cyan-400 font-bold">#{selectedFeature.properties.region_index}</span>
                  </div>
                  <div className="text-base font-bold text-white">{selectedFeature.properties.subtype}</div>
                  <div className="flex gap-2">
                    <CategoryBadge category={selectedFeature.properties.category} />
                    <SeverityBadge severity={selectedFeature.properties.severity_level} />
                  </div>
                </div>

                {/* Spatial Area Metrics */}
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2.5 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[10px]">SURFACE AREA:</span>
                    <span className="text-emerald-400 font-bold">
                      {selectedFeature.properties.area_m2.toLocaleString()} m²
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[10px]">AREA (KM²):</span>
                    <span className="text-slate-200">{selectedFeature.properties.area_km2} km²</span>
                  </div>
                  <div className="p-2.5 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[10px]">CONFIDENCE:</span>
                    <span className="text-cyan-400 font-bold">
                      {Math.round(selectedFeature.properties.mean_confidence * 100)}%
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[10px]">PERIMETER:</span>
                    <span className="text-slate-200">{selectedFeature.properties.perimeter_m || 850} m</span>
                  </div>
                </div>

                {/* 🔬 Multi-Spectral Corroboration Card */}
                <div className="p-3 rounded-lg bg-space-950 border border-cyan-500/30 space-y-2">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-cyan-300 font-bold flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5 text-cyan-400" />
                      SPECTRAL SIGNATURE
                    </span>
                    <span className="text-[10px] text-slate-500">ISRO CORROBORATION</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-1.5 rounded bg-space-900 border border-white/5">
                      <div className="text-slate-500">NDVI (T1 → T2):</div>
                      <div className="font-bold text-slate-200">
                        {selectedFeature.properties.ndvi_t1 ?? 0.72} →{' '}
                        <span className="text-rose-400">{selectedFeature.properties.ndvi_t2 ?? 0.18}</span>
                      </div>
                      <div className="text-[9px] text-rose-400">
                        Δ: {(+(selectedFeature.properties.ndvi_t2 ?? 0.18) - +(selectedFeature.properties.ndvi_t1 ?? 0.72)).toFixed(2)}
                      </div>
                    </div>

                    <div className="p-1.5 rounded bg-space-900 border border-white/5">
                      <div className="text-slate-500">NDBI (T1 → T2):</div>
                      <div className="font-bold text-slate-200">
                        {selectedFeature.properties.ndbi_t1 ?? -0.22} →{' '}
                        <span className="text-cyan-400">{selectedFeature.properties.ndbi_t2 ?? +0.64}</span>
                      </div>
                      <div className="text-[9px] text-cyan-400">
                        Δ: {((selectedFeature.properties.ndbi_t2 ?? 0.64) - (selectedFeature.properties.ndbi_t1 ?? -0.22)).toFixed(2)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] pt-1 border-t border-white/5">
                    <span className="text-slate-400">SAR Backscatter σ⁰:</span>
                    <span className="text-amber-400 font-bold">
                      {selectedFeature.properties.sar_sigma0 ?? '+4.2 dB'}
                    </span>
                  </div>

                  <p className="text-[10px] text-slate-300 leading-relaxed bg-space-900/60 p-2 rounded border border-white/5">
                    {selectedFeature.properties.corroboration ??
                      'Spectral shift confirms anthropogenic surface conversion.'}
                  </p>
                </div>

                {/* Coordinates */}
                <div className="p-2.5 rounded bg-space-900 border border-white/5 space-y-1 text-[11px]">
                  <span className="text-slate-500 block text-[10px]">CENTROID COORDINATES:</span>
                  <div className="text-slate-300">
                    LAT: <span className="text-cyan-300">{selectedFeature.properties.centroid_lat.toFixed(5)}°N</span>
                  </div>
                  <div className="text-slate-300">
                    LON: <span className="text-cyan-300">{selectedFeature.properties.centroid_lon.toFixed(5)}°E</span>
                  </div>
                </div>

                {/* Observation Intervals */}
                <div className="p-2.5 rounded bg-space-900 border border-white/5 space-y-1 text-[11px]">
                  <span className="text-slate-500 block text-[10px] flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-cyan-400" />
                    OBSERVATION DATES:
                  </span>
                  <div className="text-slate-300">
                    T1: <span className="text-slate-400">{selectedFeature.properties.observation_t1 || '2020-01-15'}</span>
                  </div>
                  <div className="text-slate-300">
                    T2: <span className="text-amber-400">{selectedFeature.properties.observation_t2 || '2026-01-15'}</span>
                  </div>
                </div>

                {/* Baseline Label Tag */}
                <div className="p-2 rounded bg-amber-950/30 border border-amber-500/30 text-[10px] text-amber-300">
                  <span className="font-bold block">MODEL TAG:</span>
                  {selectedFeature.properties.label || 'Baseline / Demo Result'}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 font-mono text-xs">
                <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                Click on any change polygon or centroid on the map to inspect telemetry.
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MapPage;
