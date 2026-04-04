"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Key, Bell, Palette, Building2, Shield, Copy, Eye, EyeOff,
  RefreshCw, Check, Plug, CreditCard, Users, Mail, Webhook,
  ChevronRight, AlertCircle, Moon, Sun, Monitor,
} from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.06, duration: 0.35 } }),
};

const API_KEYS = [
  { id: "k1", name: "Production Ingestion Key", prefix: "fs_live_", suffix: "k9mX", created: "2024-01-15", lastUsed: "2 hours ago", scopes: ["ingest:write", "ingest:read"] },
  { id: "k2", name: "Staging / Test Key", prefix: "fs_test_", suffix: "p2nQ", created: "2024-02-20", lastUsed: "3 days ago", scopes: ["ingest:write"] },
  { id: "k3", name: "Stripe Webhook Key", prefix: "fs_whk_", suffix: "r7vL", created: "2024-03-01", lastUsed: "1 hour ago", scopes: ["webhook:receive"] },
];

const INTEGRATIONS = [
  { name: "Stripe", icon: "💳", status: "connected", lastSync: "5 min ago", desc: "Sync invoices, subscriptions, and payment events", border: "border-violet-500/20", bg: "from-violet-500/10 to-violet-500/5" },
  { name: "Chargebee", icon: "📊", status: "disconnected", lastSync: null, desc: "Import subscription lifecycle events and MRR movements", border: "border-blue-500/20", bg: "from-blue-500/10 to-blue-500/5" },
  { name: "HubSpot", icon: "🔶", status: "connected", lastSync: "1 hour ago", desc: "Pull CRM leads and pipeline data into funnel analytics", border: "border-orange-500/20", bg: "from-orange-500/10 to-orange-500/5" },
  { name: "Slack", icon: "💬", status: "connected", lastSync: "Active", desc: "Receive churn risk alerts and weekly revenue digests", border: "border-green-500/20", bg: "from-green-500/10 to-green-500/5" },
  { name: "Salesforce", icon: "☁️", status: "disconnected", lastSync: null, desc: "Sync opportunity data and account health scores", border: "border-sky-500/20", bg: "from-sky-500/10 to-sky-500/5" },
  { name: "Intercom", icon: "🎯", status: "disconnected", lastSync: null, desc: "Import support tickets and CSAT scores for health scoring", border: "border-indigo-500/20", bg: "from-indigo-500/10 to-indigo-500/5" },
];

const NOTIFS_INIT = [
  { id: "churn", label: "Churn Risk Alerts", desc: "Notify when an account enters critical risk tier", on: true },
  { id: "mrr", label: "MRR Drop Alert", desc: "Alert when MRR drops more than 5% month-over-month", on: true },
  { id: "digest", label: "Weekly Revenue Digest", desc: "Summary of MRR, NRR, and key movements every Monday", on: true },
  { id: "pay", label: "Payment Failure Alerts", desc: "Immediate notification on invoice payment failures", on: false },
  { id: "new", label: "New Account Notifications", desc: "Alert when a new paid account is created", on: false },
  { id: "usage", label: "Usage Drop Warnings", desc: "Notify when product usage drops >40% month-over-month", on: true },
];

const TEAM = [
  { name: "Alex Rivera", email: "alex@flowsync.io", role: "Admin", av: "AR", color: "bg-brand-500" },
  { name: "Jordan Kim", email: "jordan@flowsync.io", role: "Analyst", av: "JK", color: "bg-emerald-500" },
  { name: "Sam Patel", email: "sam@flowsync.io", role: "Viewer", av: "SP", color: "bg-violet-500" },
];

function SectionHeader({ icon: Icon, title, desc }: { icon: React.ElementType; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 border border-brand-500/20">
        <Icon className="h-4 w-4 text-brand-400" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
      </div>
    </div>
  );
}

function Toggle({ on, onChange }: { on: boolean; onChange: () => void }) {
  return (
    <button
      onClick={onChange}
      className={cn("relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200", on ? "bg-brand-500" : "bg-muted")}
    >
      <span className={cn("pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition duration-200", on ? "translate-x-4" : "translate-x-0")} />
    </button>
  );
}

export default function SettingsPage() {
  const [copied, setCopied] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<string | null>(null);
  const [notifs, setNotifs] = useState(NOTIFS_INIT);
  const [theme, setTheme] = useState<"dark" | "light" | "system">("dark");
  const [saved, setSaved] = useState(false);

  const handleCopy = (id: string) => {
    navigator.clipboard.writeText(`${id}_DEMO_REDACTED`).catch(() => {});
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div>
      <DashboardHeader title="Settings" description="Manage your FlowSync workspace, API keys, and integrations" />
      <div className="p-6 space-y-6 max-w-5xl">
        <PageHeader title="Settings" description="Configure your workspace, data connections, and notification preferences" />

        {/* Organization Profile */}
        <motion.div custom={0} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Building2} title="Organization Profile" desc="Your company details shown across the platform" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { label: "Company Name", value: "FlowSync Inc." },
                  { label: "Industry", value: "Workflow Automation" },
                  { label: "Primary Contact Email", value: "admin@flowsync.io" },
                  { label: "Timezone", value: "UTC-5 (Eastern Time)" },
                  { label: "Fiscal Year Start", value: "January" },
                  { label: "Currency", value: "USD ($)" },
                ].map((f) => (
                  <div key={f.label}>
                    <label className="text-xs font-medium text-muted-foreground block mb-1.5">{f.label}</label>
                    <input
                      defaultValue={f.value}
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-500/40 transition-all"
                    />
                  </div>
                ))}
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  onClick={handleSave}
                  className={cn("flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all", saved ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-brand-500 text-white hover:bg-brand-600")}
                >
                  {saved ? <><Check className="h-3.5 w-3.5" />Saved</> : "Save Changes"}
                </button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* API Keys */}
        <motion.div custom={1} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Key} title="API Keys" desc="Use these keys to push your data into FlowSync via REST API or webhooks" />
              <div className="mb-4 flex items-start gap-3 rounded-lg border border-brand-500/20 bg-brand-500/5 p-3">
                <AlertCircle className="h-4 w-4 text-brand-400 shrink-0 mt-0.5" />
                <p className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">How to use: </span>
                  Include your key in the <code className="rounded bg-muted px-1 py-0.5 font-mono text-brand-400">X-API-Key</code> header when calling{" "}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-brand-400">POST /api/v1/ingest/*</code>.{" "}
                  See the <a href="/dashboard/help" className="text-brand-400 underline underline-offset-2">Help page</a> for full integration guides.
                </p>
              </div>
              <div className="space-y-3">
                {API_KEYS.map((k) => (
                  <div key={k.id} className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-4 py-3 gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-foreground">{k.name}</p>
                        <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-500/30 bg-emerald-500/5">active</Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <code className="font-mono text-brand-400">{k.prefix}{"••••••••"}{k.suffix}</code>
                        <span>· Last used: {k.lastUsed}</span>
                        <span>· Created: {k.created}</span>
                      </div>
                      <div className="flex gap-1 mt-1.5">
                        {k.scopes.map((s) => (
                          <span key={s} className="text-[10px] rounded-full bg-muted px-2 py-0.5 text-muted-foreground font-mono">{s}</span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button onClick={() => setRevealed(revealed === k.id ? null : k.id)} className="rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
                        {revealed === k.id ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </button>
                      <button onClick={() => handleCopy(k.id)} className="rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
                        {copied === k.id ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                      <button className="rounded-md p-1.5 text-muted-foreground hover:text-amber-400 hover:bg-amber-500/10 transition-colors">
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <button className="flex items-center gap-2 rounded-lg border border-dashed border-border px-4 py-2.5 text-sm text-muted-foreground hover:border-brand-500/40 hover:text-brand-400 hover:bg-brand-500/5 transition-all w-full justify-center">
                  <Key className="h-3.5 w-3.5" />Generate New API Key
                </button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Integrations */}
        <motion.div custom={2} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Plug} title="Data Integrations" desc="Connect your billing, CRM, and support tools to automatically sync data" />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {INTEGRATIONS.map((ig) => (
                  <div key={ig.name} className={cn("rounded-lg border bg-gradient-to-br p-4 transition-all hover:shadow-sm", ig.border, ig.bg)}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{ig.icon}</span>
                        <div>
                          <p className="text-sm font-semibold text-foreground">{ig.name}</p>
                          <p className="text-[10px] text-muted-foreground">{ig.status === "connected" && ig.lastSync ? `Synced ${ig.lastSync}` : "Not connected"}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className={cn("text-[10px] shrink-0", ig.status === "connected" ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/5" : "text-muted-foreground border-border")}>
                        {ig.status === "connected" ? "Connected" : "Available"}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">{ig.desc}</p>
                    <button className={cn("w-full rounded-md px-3 py-1.5 text-xs font-medium transition-all", ig.status === "connected" ? "bg-muted text-muted-foreground hover:bg-red-500/10 hover:text-red-400" : "bg-brand-500/10 text-brand-400 hover:bg-brand-500/20 border border-brand-500/20")}>
                      {ig.status === "connected" ? "Disconnect" : "Connect"}
                    </button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Notifications */}
        <motion.div custom={3} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Bell} title="Notification Preferences" desc="Control which alerts and digests you receive" />
              <div className="space-y-3">
                {notifs.map((n) => (
                  <div key={n.id} className="flex items-center justify-between py-2.5 border-b border-border/40 last:border-0">
                    <div className="min-w-0 flex-1 pr-4">
                      <p className="text-sm font-medium text-foreground">{n.label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{n.desc}</p>
                    </div>
                    <Toggle on={n.on} onChange={() => setNotifs((prev) => prev.map((x) => x.id === n.id ? { ...x, on: !x.on } : x))} />
                  </div>
                ))}
              </div>
              <Separator className="my-4" />
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">Notification Channels</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Where to deliver alerts</p>
                </div>
                <div className="flex gap-2">
                  {[{ icon: Mail, label: "Email", active: true }, { icon: Webhook, label: "Slack", active: true }, { icon: Webhook, label: "Webhook", active: false }].map(({ icon: Icon, label, active }) => (
                    <button key={label} className={cn("flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all", active ? "border-brand-500/30 bg-brand-500/10 text-brand-400" : "border-border text-muted-foreground hover:border-brand-500/20 hover:text-brand-400")}>
                      <Icon className="h-3 w-3" />{label}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Appearance */}
        <motion.div custom={4} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Palette} title="Appearance" desc="Customize the look and feel of your dashboard" />
              <div className="flex gap-3">
                {([{ value: "dark", icon: Moon, label: "Dark" }, { value: "light", icon: Sun, label: "Light" }, { value: "system", icon: Monitor, label: "System" }] as const).map(({ value, icon: Icon, label }) => (
                  <button key={value} onClick={() => setTheme(value)} className={cn("flex flex-1 flex-col items-center gap-2 rounded-xl border p-4 transition-all", theme === value ? "border-brand-500/40 bg-brand-500/10 text-brand-400" : "border-border text-muted-foreground hover:border-brand-500/20 hover:bg-accent")}>
                    <Icon className="h-5 w-5" />
                    <span className="text-xs font-medium">{label}</span>
                    {theme === value && <span className="text-[10px] text-brand-400">Active</span>}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Team Members */}
        <motion.div custom={5} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Users} title="Team Members" desc="Manage who has access to your FlowSync workspace" />
              <div className="space-y-2">
                {TEAM.map((m) => (
                  <div key={m.email} className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/20 px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white", m.color)}>{m.av}</div>
                      <div>
                        <p className="text-sm font-medium text-foreground">{m.name}</p>
                        <p className="text-xs text-muted-foreground">{m.email}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className={cn("text-xs", m.role === "Admin" ? "text-brand-400 border-brand-500/30" : m.role === "Analyst" ? "text-emerald-400 border-emerald-500/30" : "text-muted-foreground border-border")}>
                      {m.role}
                    </Badge>
                  </div>
                ))}
              </div>
              <div className="mt-3">
                <button className="flex items-center gap-2 rounded-lg border border-dashed border-border px-4 py-2.5 text-sm text-muted-foreground hover:border-brand-500/40 hover:text-brand-400 hover:bg-brand-500/5 transition-all w-full justify-center">
                  <Users className="h-3.5 w-3.5" />Invite Team Member
                </button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Security */}
        <motion.div custom={6} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <SectionHeader icon={Shield} title="Security" desc="Manage authentication and access control settings" />
              <div className="space-y-1">
                {[
                  { label: "Two-Factor Authentication", desc: "Add an extra layer of security to your account", status: "Enabled", color: "text-emerald-400" },
                  { label: "SSO / SAML", desc: "Single sign-on via your identity provider", status: "Not configured", color: "text-muted-foreground" },
                  { label: "IP Allowlist", desc: "Restrict API access to specific IP ranges", status: "Disabled", color: "text-amber-400" },
                  { label: "Audit Log", desc: "Track all user actions and data access events", status: "Active", color: "text-emerald-400" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-3 border-b border-border/40 last:border-0 cursor-pointer hover:bg-accent/30 rounded-lg px-2 -mx-2 transition-colors">
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{item.desc}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-4">
                      <span className={cn("text-xs font-medium", item.color)}>{item.status}</span>
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Billing */}
        <motion.div custom={7} variants={fadeUp} initial="hidden" animate="visible">
          <Card className="border-brand-500/20 bg-gradient-to-br from-brand-500/5 to-transparent">
            <CardContent className="pt-6">
              <SectionHeader icon={CreditCard} title="Billing & Plan" desc="Your current subscription and usage limits" />
              <div className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-4 mb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-base font-bold text-foreground">Enterprise Plan</p>
                      <Badge className="bg-brand-500/20 text-brand-400 border-brand-500/30 text-[10px]">Active</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">Unlimited accounts · 5 team seats · Priority support</p>
                    <p className="text-xs text-muted-foreground mt-1">Next billing: <span className="text-foreground font-medium">May 1, 2026 · $499/mo</span></p>
                  </div>
                  <button className="rounded-lg border border-brand-500/30 bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-400 hover:bg-brand-500/20 transition-colors shrink-0">
                    Manage Plan
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "API Calls This Month", value: "142,830", sub: "Unlimited" },
                  { label: "Active Accounts Tracked", value: "176", sub: "Unlimited" },
                  { label: "Team Seats Used", value: "3 / 5", sub: "5 seats max" },
                ].map((u) => (
                  <div key={u.label} className="rounded-lg border border-border/50 bg-muted/20 p-3">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">{u.label}</p>
                    <p className="text-sm font-bold text-foreground">{u.value}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{u.sub}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
