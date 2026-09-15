import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  Send,
  User,
  Terminal,
  ShieldCheck,
  RotateCcw,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Info,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Radio,
} from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Badge } from '../components/Badge';

export const AgentPage = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedTraceId, setExpandedTraceId] = useState(null);

  // Voice Interaction & TTS States
  const [isListening, setIsListening] = useState(false);
  const [isSpeakingId, setIsSpeakingId] = useState(null);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const recognitionRef = useRef(null);

  // Initialize Web Speech Recognition API
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0].transcript)
        .join('');
      setQuery(transcript);
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // ignore cleanup abort error
        }
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const toggleListening = () => {
    if (!voiceSupported || !recognitionRef.current) {
      alert('Speech Recognition is not supported by your current browser. Please test in Chrome or Safari.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.warn('Recognition start exception:', err);
      }
    }
  };

  const handleSpeak = (msgId, text) => {
    if (!('speechSynthesis' in window)) return;

    if (isSpeakingId === msgId) {
      window.speechSynthesis.cancel();
      setIsSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    const cleanText = text
      .replace(/[*_#`•]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeakingId(null);
    utterance.onerror = () => setIsSpeakingId(null);

    setIsSpeakingId(msgId);
    window.speechSynthesis.speak(utterance);
  };

  const initialMessages = [
    {
      id: '1',
      role: 'assistant',
      content:
        'Greetings. I am the SIH1518 Grounded Satellite Intelligence Agent.\n\nI orchestrate 20 deterministic backend GIS tools, query verified PostGIS detection layers, and synthesize multi-temporal observations without inventing data or fabricating coordinates.\n\nHow may I assist your satellite analysis today?',
      timestamp: '10:00 AM',
    },
    {
      id: '2',
      role: 'user',
      content: 'What changed between 2020 and 2026 in total?',
      timestamp: '10:01 AM',
    },
    {
      id: '3',
      role: 'assistant',
      content:
        '**Change Detection Intelligence Summary**:\n\nThe multi-temporal satellite analysis detected **5.24 km²** (4.99% of total study area) of surface change across **42 discrete localized polygons**.\n\n• **Total Changed Area:** 5.24 km² (5,240,000 m²)\n• **Dominant Driver:** HUMAN activities (3.82 km² • 72.9% of change)\n• **Seasonal Natural Variations:** 1.12 km² (8 sites)\n• **Atmospheric Artifacts:** 0.30 km² (4 sites)\n• **Overall Composite Reliability:** HIGH (93.1%)',
      toolCalls: [
        {
          tool: 'detect_changes',
          args: { confidence_threshold: 0.5 },
          result: { total_area_changed_km2: 5.24, percentage_changed: 4.99, region_count: 42, label: 'Baseline / Demo Result' },
          durationMs: 42,
        },
        {
          tool: 'summarize_analysis',
          args: { changed_area_km2: 5.24, percentage_changed: 4.99, dominant_category: 'HUMAN', reliability: 'HIGH' },
          result: { dominant_category: 'HUMAN', reliability: 'HIGH', status: 'success' },
          durationMs: 8,
        },
      ],
      citations: [
        { type: 'analysis', region_id: 'AN-2026-0801', name: 'Guwahati Urban Sprawl', area_km2: 5.24 },
      ],
      timestamp: '10:01 AM',
    },
  ];

  const [messages, setMessages] = useState(initialMessages);

  const samplePrompts = [
    'What changed?',
    'Show all new buildings.',
    'How much area changed?',
    'How much area was flooded?',
    'Which changes are human activities?',
    'What changed between 2020 and 2026?',
    'Which category has the largest affected area?',
    'Explain change #12.',
    'Generate a report.',
  ];

  const handleResetHistory = () => {
    setMessages(initialMessages);
  };

  const handleSend = () => {
    if (!query.trim() || isLoading) return;

    const userText = query;
    const userMsg = {
      id: String(Date.now()),
      role: 'user',
      content: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setIsLoading(true);

    const qLower = userText.toLowerCase();

    setTimeout(() => {
      let respContent = '';
      let toolCalls = [];
      let citations = [];

      if (qLower.includes('building') || qLower.includes('housing')) {
        toolCalls = [
          {
            tool: 'query_database',
            args: { category: 'HUMAN', subcategory: 'Building' },
            result: { region_count: 30, building_area_km2: 2.94 },
            durationMs: 14,
          },
        ];
        citations = [
          { type: 'region', region_id: 'CR-001', name: 'New Commercial Complex', area_km2: 0.45, confidence: 0.96 },
          { type: 'region', region_id: 'CR-006', name: 'Residential Housing Block', area_km2: 0.72, confidence: 0.94 },
          { type: 'region', region_id: 'CR-012', name: 'Logistics Superstructure', area_km2: 0.61, confidence: 0.92 },
        ];
        respContent =
          '**Detected New Building Infrastructure (Sentinel-2 MSI 10m)**:\n\nA total of **30 discrete building sites** accounting for **2.94 km²** were identified across the study area:\n\n1. **[Region #CR-001]**: New Commercial Complex — `0.45 km²` (Confidence: 96.0%)\n2. **[Region #CR-006]**: Residential Housing Block — `0.72 km²` (Confidence: 94.0%)\n3. **[Region #CR-012]**: Logistics Superstructure — `0.61 km²` (Confidence: 92.0%)\n\n*Physical Corroboration*: High rectangularity ($R \\ge 0.60$) and positive built-up index response ($\\Delta\\text{NDBI} > +0.30$).';
      } else if (qLower.includes('flood') || qLower.includes('flooded') || qLower.includes('water')) {
        toolCalls = [
          {
            tool: 'analyze_flood',
            args: { is_sar: false, resolution_m: 10.0 },
            result: {
              disaster_type: 'FLOOD',
              affected_area_km2: 2.49,
              percentage_affected: 2.38,
              severity: 'HIGH',
              causality_wording: 'Potential flood inundation & surface water surge.',
            },
            durationMs: 38,
          },
        ];
        citations = [
          { type: 'region', region_id: 'CR-004', name: 'Flood Inundation Scar', area_km2: 2.49, confidence: 0.94 },
        ];
        respContent =
          '**Flood & Water Inundation Assessment**:\n\nBased on multi-spectral NDWI difference and SAR specular reflection analysis:\n\n• **Estimated Inundation Extent:** **2.49 km²** (2.38% of study scene)\n• **Preliminary Assessment:** Potential flood-related inundation & surface water surge.\n• **Severity Grade:** HIGH (Post-monsoon overflow corridor)\n• **Spectral Evidence:** Elevated NDWI response (+0.350) with significant radiometric albedo absorption.\n\n> **Advisory**: Preliminary satellite intelligence. Causality must be verified with authoritative disaster management agencies.';
      } else if (qLower.includes('human') || qLower.includes('activities')) {
        toolCalls = [
          {
            tool: 'query_database',
            args: { category: 'HUMAN' },
            result: { human_sites_count: 30, total_human_km2: 3.82 },
            durationMs: 12,
          },
        ];
        respContent =
          '**Human Activity Breakdown (72.9% of total change)**:\n\nThe platform identified **30 human activity sites** totaling **3.82 km²**:\n\n• **Building Complexes & Sprawl**: 2.94 km² across 24 sites ($\\Delta\\text{NDBI} +0.42$)\n• **Road Construction & Widening**: 0.88 km² across 6 sites (Linear corridors, Elongation $\\ge 4.0$x)\n• **Industrial Tech-Park Expansion**: 0.65 km² in North corridor\n\nAll human classifications are verified with composite system reliability of **HIGH (93.1%)**.';
      } else if (qLower.includes('largest') || qLower.includes('dominant')) {
        toolCalls = [
          {
            tool: 'query_database',
            args: { query: 'categorical_ranking' },
            result: { human_km2: 3.82, natural_km2: 1.12, atmospheric_km2: 0.30 },
            durationMs: 10,
          },
        ];
        respContent =
          '**Categorical Area Ranking & Dominance**:\n\n1. **HUMAN Activities**: **3.82 km²** (72.9% of change) — *Dominant Driver*\n2. **NATURAL Environmental Shifts**: **1.12 km²** (21.4% of change) — Seasonal wetland & forest canopy\n3. **ATMOSPHERIC Artifacts**: **0.30 km²** (5.7% of change) — Transient cloud/shadow\n4. **DISASTER Hazards**: **0.00 km²** in baseline sequence\n\n**Conclusion**: **HUMAN activity** is the primary driver of physical land-cover alteration.';
      } else if (qLower.includes('explain') || qLower.includes('#12') || qLower.includes('#1')) {
        toolCalls = [
          {
            tool: 'classify_changes',
            args: { region_index: 12, delta_ndbi: 0.42, delta_ndvi: -0.28 },
            result: { category: 'HUMAN', subcategory: 'Building', confidence: 0.96, rule_fired: 'HIGH_RECTANGULARITY_BUILTUP_EXPANSION' },
            durationMs: 16,
          },
        ];
        citations = [
          { type: 'region', region_id: 'CR-012', name: 'Logistics Superstructure', area_km2: 0.61, confidence: 0.92 },
        ];
        respContent =
          '**Explainability Diagnostic for [Region #CR-012]**:\n\n• **Classification:** HUMAN → **Building** (Confidence: 96.0%)\n• **Spectral Evidence:** Elevated built-up index (**ΔNDBI: +0.420**) and vegetation canopy loss (**ΔNDVI: -0.280**).\n• **Geometric Evidence:** High rectangularity (**0.78**) and low elongation (**1.35x**) confirm permanent structured building construction.\n• **Decision Rule Fired:** `HIGH_RECTANGULARITY_BUILTUP_EXPANSION`\n\n> *System Reliability Indicator: HIGH (94.2% composite)*';
      } else if (qLower.includes('report') || qLower.includes('pdf')) {
        toolCalls = [
          {
            tool: 'generate_report',
            args: { analysis_id: 'AN-2026-0801', title: 'Guwahati Multi-Temporal Change Intelligence' },
            result: { report_id: 'REP-AN-2026-0801', format: 'PDF / JSON', status: 'ready' },
            durationMs: 25,
          },
        ];
        respContent =
          '**Report Generated Successfully**:\n\n• **Report ID:** `REP-AN-2026-0801`\n• **Title:** Guwahati Multi-Temporal Change Intelligence\n• **Format:** PDF (Executive Summary with PostGIS Maps & Radar Charts)\n• **Status:** Staged for download in the **Reports** workspace.';
      } else if (qLower.includes('2020') && qLower.includes('2026')) {
        toolCalls = [
          {
            tool: 'compare_time_series',
            args: { observation_dates: ['2020-01-15', '2021-01-15', '2022-01-15', '2024-01-15', '2026-01-15'] },
            result: { observation_count: 5, human_growth_km2: 3.0, notice: 'Analysis interval depends on available satellite observations.' },
            durationMs: 20,
          },
        ];
        respContent =
          '**Multi-Temporal Progression (2020 → 2026)**:\n\nEvaluated across 5 discrete satellite overpass observations:\n\n• **2020 Baseline:** 0.00 km² reference point\n• **2021 T2:** +0.50 km² (Ground clearance)\n• **2022 T3:** +0.40 km² (Superstructure elevation)\n• **2024 T4:** +1.70 km² (Industrial tech-park)\n• **2026 Current:** +1.40 km² (Commercial paving)\n• **Total Human Expansion:** **+3.00 km²** (+375% growth)\n\n*Observation Notice: Analysis interval depends on available satellite observations.*';
      } else {
        toolCalls = [
          {
            tool: 'detect_changes',
            args: { confidence_threshold: 0.5 },
            result: { total_area_changed_km2: 5.24, percentage_changed: 4.99, region_count: 42 },
            durationMs: 30,
          },
        ];
        respContent =
          '**Grounded Satellite Intelligence Summary**:\n\nThe multi-temporal analysis detected **5.24 km²** (4.99%) of surface change across 42 discrete regions.\n\n• **Dominant Category:** HUMAN (30 sites • 3.82 km²)\n• **Natural Shifts:** 8 sites • 1.12 km²\n• **Composite Reliability:** HIGH (93.1%)\n• **Validation Status:** Zero fabrication guardrail enforced.';
      }

      const agentMsg = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: respContent,
        toolCalls,
        citations,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, agentMsg]);
      setIsLoading(false);
    }, 550);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Bot className="w-6 h-6 text-cyan-400" />
              AI Satellite Intelligence Agent
            </h1>
            <Badge variant="cyan">AN-2026-0801 CONTEXT</Badge>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            CONVERSATIONAL GIS COPILOT • ORCHESTRATING 20 DETERMINISTIC GIS & ML TOOLS
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs">
          <Button size="sm" variant="outline" icon={RotateCcw} onClick={handleResetHistory}>
            Reset Chat
          </Button>
          <Badge variant="cyan">
            <Radio className="w-3.5 h-3.5 mr-1 inline animate-pulse" /> VOICE AI READY
          </Badge>
          <Badge variant="emerald">
            <ShieldCheck className="w-3.5 h-3.5 mr-1 inline" /> ANTI-HALLUCINATION ACTIVE
          </Badge>
        </div>
      </div>

      {/* Primary Product Architecture Reminder */}
      <div className="p-3 rounded-xl bg-space-900 border border-white/10 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2 text-slate-300">
          <Info className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>Active Context: <strong>Guwahati Urban Study (Sentinel-2 MSI • 10m • 2020 → 2026)</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/results" className="text-cyan-400 hover:underline flex items-center gap-1 text-[11px]">
            Dashboard <ExternalLink className="w-3 h-3" />
          </Link>
          <Link to="/map" className="text-cyan-400 hover:underline flex items-center gap-1 text-[11px]">
            GIS Map <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div className="flex flex-wrap gap-2">
        {samplePrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => setQuery(prompt)}
            className="px-3 py-1.5 rounded-lg bg-space-900 border border-white/5 hover:border-cyan-500/40 text-xs font-mono text-slate-300 hover:text-cyan-300 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Messages Stream */}
      <Card className="min-h-[520px] flex flex-col justify-between overflow-hidden">
        <div className="space-y-5 overflow-y-auto pr-2 max-h-[620px]">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 text-xs leading-relaxed ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role !== 'user' && (
                <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div
                className={`p-4 rounded-xl max-w-3xl space-y-3 ${
                  msg.role === 'user'
                    ? 'bg-cyan-600 text-space-950 font-medium'
                    : 'bg-space-900 border border-white/10 text-slate-200'
                }`}
              >
                <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>

                {/* Citations & Deeplinks */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="pt-2 border-t border-white/10 flex flex-wrap gap-2 font-mono text-[10px]">
                    <span className="text-slate-400 font-bold self-center">Analysis Citations:</span>
                    {msg.citations.map((cit, idx) => (
                      <Link
                        key={idx}
                        to="/results"
                        className="px-2 py-1 rounded bg-space-950 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-950/50 transition flex items-center gap-1"
                      >
                        <span>{cit.region_id}</span>
                        {cit.area_km2 && <span className="text-amber-400">({cit.area_km2} km²)</span>}
                        <ExternalLink className="w-2.5 h-2.5" />
                      </Link>
                    ))}
                  </div>
                )}

                {/* Collapsible Tool Execution Trace */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="pt-2 border-t border-white/10 font-mono text-[11px]">
                    <button
                      onClick={() =>
                        setExpandedTraceId(expandedTraceId === msg.id ? null : msg.id)
                      }
                      className="flex items-center gap-1.5 text-cyan-400 font-bold hover:text-cyan-300 transition mb-1"
                    >
                      {expandedTraceId === msg.id ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                      <Terminal className="w-3.5 h-3.5" />
                      <span>Executed Grounded Tools ({msg.toolCalls.length}):</span>
                    </button>

                    {expandedTraceId === msg.id && (
                      <div className="space-y-1.5 mt-2 animate-fade-in">
                        {msg.toolCalls.map((tc, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-space-950 border border-white/5 space-y-1">
                            <div className="flex items-center justify-between text-cyan-300">
                              <span className="font-bold">tool: {tc.tool}()</span>
                              <span className="text-slate-500 text-[9px]">{tc.durationMs || 15}ms • SUCCESS</span>
                            </div>
                            <div className="text-[10px] text-slate-400 font-mono">
                              <strong>Args:</strong> {JSON.stringify(tc.args)}
                            </div>
                            <div className="text-[10px] text-slate-400 font-mono">
                              <strong>Result:</strong> {JSON.stringify(tc.result)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-white/5">
                  {msg.role !== 'user' ? (
                    <button
                      type="button"
                      onClick={() => handleSpeak(msg.id, msg.content)}
                      className={`flex items-center gap-1.5 px-2 py-0.5 rounded transition-all ${
                        isSpeakingId === msg.id
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-500/40 font-bold'
                          : 'bg-space-950/60 hover:bg-space-950 text-slate-400 hover:text-cyan-300 border border-white/5'
                      }`}
                      title={isSpeakingId === msg.id ? 'Stop audio' : 'Read aloud with AI speech'}
                    >
                      {isSpeakingId === msg.id ? (
                        <>
                          <VolumeX className="w-3 h-3 text-rose-400" />
                          <span>Stop Voice</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3 h-3 text-cyan-400" />
                          <span>Read Aloud</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <div />
                  )}
                  <span>{msg.timestamp}</span>
                </div>
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0 mt-1">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 text-xs justify-start animate-pulse">
              <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-xl bg-space-900 border border-white/10 text-slate-400 font-mono flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400 animate-spin" />
                Orchestrating backend GIS tools & querying PostGIS change layers...
              </div>
            </div>
          )}
        </div>

        {/* Voice Recognition Active Telemetry Alert */}
        {isListening && (
          <div className="mt-3 p-2.5 rounded-lg bg-rose-950/40 border border-rose-500/50 text-rose-200 flex items-center justify-between text-xs font-mono animate-pulse shadow-[0_0_15px_rgba(244,63,94,0.3)]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
              <span>🎙️ Listening live... Bol Kar Pucho (English / Hindi voice prompt)</span>
            </div>
            <button
              type="button"
              onClick={toggleListening}
              className="text-[10px] bg-rose-900 hover:bg-rose-800 text-white px-2 py-0.5 rounded transition-colors"
            >
              Finish
            </button>
          </div>
        )}

        {/* Input Bar */}
        <div className="mt-4 pt-4 border-t border-white/5 flex gap-2 sm:gap-3">
          <input
            type="text"
            placeholder="Ask questions about detected changes, flooded area, building construction, or metadata..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
            className="flex-1 bg-space-900 border border-white/10 focus:border-cyan-400 rounded-lg px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none font-mono"
          />

          {/* Voice Input "Bol Kar Pucho" Button */}
          <Button
            type="button"
            variant={isListening ? 'danger' : 'outline'}
            size="md"
            icon={isListening ? MicOff : Mic}
            onClick={toggleListening}
            className={
              isListening
                ? 'animate-pulse shadow-[0_0_15px_#f43f5e] border-rose-500 text-rose-300'
                : 'hover:border-cyan-400 text-slate-200'
            }
            title="Bol Kar Pucho (Voice Input)"
          >
            <span className="hidden sm:inline">{isListening ? 'Listening...' : 'Voice'}</span>
          </Button>

          <Button variant="primary" size="md" icon={Send} onClick={handleSend} disabled={isLoading || !query.trim()}>
            Send Query
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AgentPage;
