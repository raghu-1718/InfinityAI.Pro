"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Loader2,
  Send,
  Sparkles,
  Database,
  Terminal,
  ChevronDown,
  ChevronUp,
  Cpu,
  RefreshCw,
  Copy,
  Check,
  Zap,
  TrendingUp,
  ShieldAlert,
  BarChart2,
  Bot,
} from "lucide-react";
import { infinityCopilot } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "copilot";
  content: string;
  timestamp: string;
  model?: string;
  sqlAudit?: {
    sql: string;
    rows_count: number;
    data: any[];
  } | null;
  bigqueryMetrics?: any;
}

const QUICK_PROMPTS = [
  { label: "📊 BigQuery Live Ticks", text: "What is the total live tick count and latest NIFTY price in BigQuery?" },
  { label: "⚡ ML Tri-Model Signal", text: "What is the ML Tri-Model ensemble conviction and technical indicators for NIFTY?" },
  { label: "📈 Options PCR & Greeks", text: "Summarize the options chain open interest, Put-Call Ratio (PCR), and IV skew." },
  { label: "🛡️ VaR & Risk Sizing", text: "Evaluate portfolio Dynamic VaR, max drawdown risk, and position sizing guardrails." },
  { label: "🌐 Macro News Grounding", text: "What are the latest macroeconomic catalysts and central bank sentiment impacting Indian markets?" },
];

export function InfinityAICopilotPanel({ embedded = true }: { embedded?: boolean }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "copilot",
      content:
        "👋 Welcome to **InfinityAI Copilot** — your institutional quantitative trading intelligence engine.\n\n" +
        "I am directly integrated with **Google Cloud BigQuery** (`market_data.live_ticks`, `options_ticks`, `history`) and **Vertex AI Gemini 2.5 Flash**.\n\n" +
        "Ask me anything about real-time market ticks, Tri-Model ML predictions, Options Greeks, or Macroeconomic Sentiment.",
      timestamp: new Date().toISOString(),
      model: "Vertex AI Gemini 2.5 Flash",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copilotStatus, setCopilotStatus] = useState<any>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedSqlId, setExpandedSqlId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const fetchStatus = async () => {
    try {
      const data = await infinityCopilot.getStatus();
      setCopilotStatus(data);
    } catch (e) {
      console.warn("Copilot status check:", e);
    }
  };

  const handleSend = async (customText?: string) => {
    const messageText = customText || input;
    if (!messageText.trim() || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: messageText.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInput("");
    setIsLoading(true);

    try {
      const res = await infinityCopilot.chat(messageText.trim());
      if (res.success) {
        const copilotMsg: Message = {
          id: `copilot-${Date.now()}`,
          role: "copilot",
          content: res.response,
          timestamp: res.timestamp || new Date().toISOString(),
          model: res.model || "Vertex AI Gemini 2.5 Flash",
          sqlAudit: res.sql_audit,
          bigqueryMetrics: res.bigquery_metrics,
        };
        setMessages((prev) => [...prev, copilotMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "copilot",
            content: `⚠️ **InfinityAI Copilot Error:** ${res.error || "Failed to process query."}`,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "copilot",
          content: `⚠️ **Connection Notice:** Unable to reach Copilot engine (${err.message || err}). Please check Cloud Run Engine C status.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <Card className={`glass-card border border-purple-500/20 flex flex-col ${embedded ? "h-[700px]" : "h-full"}`}>
      {/* Header */}
      <CardHeader className="pb-3 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-md shadow-purple-500/20">
              <Sparkles className="h-5 w-5 text-white animate-pulse" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold flex items-center gap-2 text-white">
                Infinity<span className="gradient-text">AI</span> Copilot
                <Badge variant="outline" className="border-purple-500/40 text-purple-300 text-[10px] uppercase tracking-wider font-mono">
                  GCP Native
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs text-white/50">
                BigQuery Data Warehouse & Vertex AI Gemini 2.5 Flash Grounding
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs flex items-center gap-1.5 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              BigQuery Active
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white/50 hover:text-white"
              onClick={fetchStatus}
              title="Refresh status"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardHeader>

      {/* Messages Feed */}
      <CardContent className="flex-1 flex flex-col p-4 overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-white/10">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[90%] md:max-w-[85%] rounded-2xl p-4 transition-all duration-200 ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-purple-600/30 to-indigo-600/30 border border-purple-500/30 text-white shadow-lg"
                    : "bg-white/[0.04] border border-white/10 text-slate-200 shadow-md backdrop-blur-md"
                }`}
              >
                {/* Copilot Header Badge */}
                {msg.role === "copilot" && (
                  <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-white/5">
                    <div className="flex items-center gap-1.5 text-xs text-purple-300 font-semibold">
                      <Cpu className="w-3.5 h-3.5 text-purple-400" />
                      <span>{msg.model || "Vertex AI Gemini 2.5 Flash"}</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="text-white/40 hover:text-white text-xs flex items-center gap-1"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                )}

                {/* Content */}
                <div className="text-sm space-y-2 whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>

                {/* BigQuery SQL Audit Dropdown */}
                {msg.sqlAudit && (
                  <div className="mt-3 pt-2 border-t border-white/5">
                    <button
                      onClick={() => setExpandedSqlId(expandedSqlId === msg.id ? null : msg.id)}
                      className="flex items-center justify-between w-full text-xs text-cyan-400 hover:text-cyan-300 font-mono py-1 px-2 rounded bg-cyan-500/10 border border-cyan-500/20"
                    >
                      <span className="flex items-center gap-1.5">
                        <Database className="w-3 h-3" />
                        BigQuery SQL Executed ({msg.sqlAudit.rows_count} rows fetched)
                      </span>
                      {expandedSqlId === msg.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {expandedSqlId === msg.id && (
                      <div className="mt-2 p-2.5 rounded bg-black/50 border border-white/10 text-xs font-mono text-cyan-300 overflow-x-auto">
                        <p className="text-white/50 mb-1">// BigQuery SQL Query</p>
                        <pre className="text-[11px] leading-tight">{msg.sqlAudit.sql}</pre>
                      </div>
                    )}
                  </div>
                )}

                {/* Timestamp */}
                <div className="mt-2 text-[10px] text-white/30 text-right">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-center gap-3 p-4 max-w-sm rounded-2xl bg-white/[0.03] border border-white/10 text-slate-400 text-xs animate-pulse">
              <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
              <span>Querying BigQuery & synthesizing Vertex AI signals...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="pt-3 pb-2 flex gap-1.5 overflow-x-auto no-scrollbar">
          {QUICK_PROMPTS.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip.text)}
              disabled={isLoading}
              className="text-xs px-2.5 py-1 rounded-full bg-white/5 hover:bg-purple-500/20 border border-white/10 hover:border-purple-500/30 text-white/70 hover:text-white whitespace-nowrap transition-all flex items-center gap-1"
            >
              {chip.label}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div className="pt-2 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Ask InfinityAI about live BigQuery ticks, ML signals, or Options Greeks..."
            disabled={isLoading}
            className="bg-black/30 border-white/10 text-white placeholder:text-white/30 focus-visible:ring-purple-500"
          />
          <Button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white px-4 shadow-lg shadow-purple-500/20"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Global Floating Copilot Trigger & Drawer ────────────────────────────────
export function InfinityAICopilotFloating() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          className="fixed bottom-6 right-6 z-50 p-3.5 rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-500 text-white shadow-2xl shadow-purple-500/40 hover:scale-105 active:scale-95 transition-all duration-300 group flex items-center gap-2 border border-white/20 backdrop-blur-lg"
          title="Open InfinityAI Copilot"
        >
          <Sparkles className="w-5 h-5 animate-pulse text-white group-hover:rotate-12 transition-transform" />
          <span className="text-sm font-bold tracking-wide pr-1">InfinityAI</span>
        </button>
      </SheetTrigger>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl p-0 bg-[#0B0E14] border-l border-white/10 text-white flex flex-col h-full z-50"
      >
        <InfinityAICopilotPanel embedded={false} />
      </SheetContent>
    </Sheet>
  );
}
