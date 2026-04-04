"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen, Code2, Webhook, Zap, ChevronDown, ChevronRight,
  ExternalLink, Copy, Check, Search, MessageCircle, FileText,
  PlayCircle, Database, GitBranch, Terminal,
} from "lucide-react";
import { DashboardHeader, PageHeader } from "@/components/layout/DashboardHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.06, duration: 0.35 } }),
};

// ─── Code block component ─────────────────────────────────────────────────────
function CodeBlock({ code, lang = "bash" }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(code).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="relative rounded-lg border border-border/60 bg-[#0d1117] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border/40 bg-muted/20">
        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">{lang}</span>
        <button onClick={handleCopy} className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-foreground transition-colors">
          {copied ? <><Check className="h-3 w-3 text-emerald-400" /><span className="text-emerald-400">Copied</span></> : <><Copy className="h-3 w-3" />Copy</>}
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-slate-300 overflow-x-auto leading-relaxed whitespace-pre">{code}</pre>
    </div>
  );
}

// ─── Accordion ────────────────────────────────────────────────────────────────
function Accordion({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-border/40 last:border-0">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center justify-between py-3.5 text-left gap-3 hover:text-foreground transition-colors">
        <span className="text-sm font-medium text-foreground">{question}</span>
        {open ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" /> : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />}
      </button>
      {open && <p className="pb-4 text-sm text-muted-foreground leading-relaxed">{answer}</p>}
    </div>
  );
}

// ─── Data ─────────────────────────────────────────────────────────────────────
const QUICK_LINKS = [
  { icon: PlayCircle, label: "Quickstart Guide", desc: "Get data flowing in 5 minutes", href: "#quickstart", color: "text-brand-400 bg-brand-500/10 border-brand-500/20" },
  { icon: Code2, label: "REST API Reference", desc: "All 24 endpoints documented", href: "#api-ref", color: "text-violet-400 bg-violet-500/10 border-violet-500/20" },
  { icon: Webhook, label: "Webhook Setup", desc: "Stripe & Chargebee integration", href: "#webhooks", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  { icon: Database, label: "Data Model", desc: "Schema, medallion architecture", href: "#data-model", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  { icon: GitBranch, label: "dbt Transformations", desc: "Run and customize dbt models", href: "#dbt", color: "text-orange-400 bg-orange-500/10 border-orange-500/20" },
  { icon: Terminal, label: "CLI & Docker", desc: "Local dev and deployment", href: "#deployment", color: "text-sky-400 bg-sky-500/10 border-sky-500/20" },
];

const ENDPOINTS = [
  { method: "POST", path: "/api/v1/ingest/accounts", desc: "Upsert account records", tag: "Ingest" },
  { method: "POST", path: "/api/v1/ingest/subscriptions", desc: "Upsert subscription data", tag: "Ingest" },
  { method: "POST", path: "/api/v1/ingest/invoices", desc: "Upsert invoice records", tag: "Ingest" },
  { method: "POST", path: "/api/v1/ingest/usage-events", desc: "Batch ingest usage events", tag: "Ingest" },
  { method: "POST", path: "/api/v1/ingest/tickets", desc: "Upsert support tickets", tag: "Ingest" },
  { method: "POST", path: "/api/v1/ingest/leads", desc: "Upsert lead/opportunity data", tag: "Ingest" },
  { method: "POST", path: "/api/v1/webhook/stripe", desc: "Receive Stripe webhook events", tag: "Webhook" },
  { method: "GET", path: "/api/v1/executive/summary", desc: "Executive KPI summary", tag: "Analytics" },
  { method: "GET", path: "/api/v1/executive/mrr-trend", desc: "MRR trend over time", tag: "Analytics" },
  { method: "GET", path: "/api/v1/cohorts/heatmap", desc: "Cohort retention heatmap", tag: "Analytics" },
  { method: "GET", path: "/api/v1/health/risky-accounts", desc: "Accounts at churn risk", tag: "Analytics" },
  { method: "GET", path: "/api/v1/funnel/overview", desc: "Lead-to-paid funnel metrics", tag: "Analytics" },
];

const FAQS = [
  { q: "How do I authenticate API requests?", a: "Include your API key in the X-API-Key request header. Keys are scoped per operation (ingest:write, ingest:read, webhook:receive). Generate keys from Settings → API Keys." },
  { q: "What data format does the ingest API expect?", a: "All ingest endpoints accept JSON arrays of objects. Each object must include the required fields for that entity type. Optional fields can be omitted and will default to null. See the schema reference below for field definitions." },
  { q: "How often should I push data?", a: "For real-time accuracy, push subscription and invoice events immediately via webhooks. For usage events, batch hourly. For account metadata, daily syncs are sufficient. The platform aggregates monthly for MRR calculations." },
  { q: "How is MRR calculated from my data?", a: "MRR is derived from active subscriptions in the raw_subscriptions table. Monthly amounts are normalized from annual/quarterly plans. The dbt model fct_mrr_movements classifies each account's MRR change as new, expansion, contraction, churn, or reactivation." },
  { q: "Can I backfill historical data?", a: "Yes. The ingest API is idempotent — re-posting the same record with the same ID will upsert (update) it. You can backfill up to 36 months of historical data. Use the month_key field to ensure correct period attribution." },
  { q: "How is the health score calculated?", a: "Health scores (0–100) are computed nightly using a rule-based model: product usage frequency (25pts), active users vs seats (20pts), feature adoption (15pts), support burden (15pts), CSAT (15pts), payment history (10pts). Accounts below 40 are flagged as critical risk." },
  { q: "What triggers a churn risk flag?", a: "Risk flags are raised when: usage drops >40% MoM, no login in 14+ days, 2+ unresolved high-priority tickets, payment failure in current cycle, CSAT < 3, or seat utilization below 25%. Multiple flags escalate the risk tier." },
  { q: "How do I run dbt transformations?", a: "Run `docker-compose --profile dbt up dbt` to execute all models. Or exec into the dbt container: `docker-compose exec dbt dbt run --select marts.*`. Models run in dependency order: bronze → silver → intermediate → gold/marts." },
];

const CURL_ACCOUNT = `curl -X POST https://api.flowsync.io/api/v1/ingest/accounts \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: fs_live_YOUR_KEY_HERE" \\
  -d '[
    {
      "account_id": "acc_001",
      "company_name": "Acme Corp",
      "industry": "Technology",
      "company_size": "mid_market",
      "region": "North America",
      "acquisition_channel": "inbound",
      "created_at": "2024-01-15T00:00:00Z"
    }
  ]'`;

const CURL_SUBSCRIPTION = `curl -X POST https://api.flowsync.io/api/v1/ingest/subscriptions \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: fs_live_YOUR_KEY_HERE" \\
  -d '[
    {
      "subscription_id": "sub_001",
      "account_id": "acc_001",
      "plan_name": "Growth",
      "mrr": 499.00,
      "status": "active",
      "started_at": "2024-01-15T00:00:00Z",
      "billing_interval": "monthly"
    }
  ]'`;

const PYTHON_SDK = `import requests

API_KEY = "fs_live_YOUR_KEY_HERE"
BASE_URL = "https://api.flowsync.io/api/v1"

def ingest_accounts(accounts: list[dict]) -> dict:
    resp = requests.post(
        f"{BASE_URL}/ingest/accounts",
        json=accounts,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()

# Example usage
result = ingest_accounts([
    {
        "account_id": "acc_001",
        "company_name": "Acme Corp",
        "industry": "Technology",
        "company_size": "mid_market",
        "region": "North America",
        "acquisition_channel": "inbound",
        "created_at": "2024-01-15T00:00:00Z",
    }
])
print(result)  # {"inserted": 1, "updated": 0, "errors": []}`;

const STRIPE_WEBHOOK = `# 1. In your Stripe Dashboard → Webhooks → Add endpoint:
#    URL: https://api.flowsync.io/api/v1/webhook/stripe
#    Events: customer.subscription.*, invoice.*, payment_intent.*

# 2. Copy the webhook signing secret and add to your .env:
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE

# 3. FlowSync will automatically process:
#    - customer.subscription.created  → new MRR
#    - customer.subscription.updated  → expansion/contraction
#    - customer.subscription.deleted  → churned MRR
#    - invoice.payment_failed         → payment failure flag
#    - invoice.payment_succeeded      → invoice record`;

const DOCKER_QUICKSTART = `# Clone and start the full stack
git clone https://github.com/your-org/saas-revenue-intelligence
cd saas-revenue-intelligence

# Copy environment variables
cp env.example .env

# Start postgres + api (builds images automatically)
docker-compose up -d postgres api

# Wait for postgres to be healthy, then seed with synthetic data
docker-compose --profile seed up seeder

# Run dbt transformations to populate marts
docker-compose --profile dbt up dbt

# Start the web frontend
cd apps/web && npm install && npm run dev

# API: http://localhost:8000
# Web: http://localhost:3000
# Docs: http://localhost:8000/docs`;

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function HelpPage() {
  const [search, setSearch] = useState("");

  const filteredFaqs = FAQS.filter(
    (f) =>
      search === "" ||
      f.q.toLowerCase().includes(search.toLowerCase()) ||
      f.a.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <DashboardHeader title="Help & Documentation" description="Integration guides, API reference, and troubleshooting" />
      <div className="p-6 space-y-8 max-w-5xl">
        <PageHeader title="Help & Documentation" description="Everything you need to integrate your data and get the most from FlowSync" />

        {/* Quick Links */}
        <motion.div custom={0} variants={fadeUp} initial="hidden" animate="visible">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {QUICK_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="group flex items-start gap-3 rounded-xl border border-border/60 bg-card p-4 hover:border-brand-500/30 hover:bg-accent/30 transition-all"
              >
                <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border", link.color)}>
                  <link.icon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground group-hover:text-brand-400 transition-colors">{link.label}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{link.desc}</p>
                </div>
              </a>
            ))}
          </div>
        </motion.div>

        {/* Quickstart */}
        <motion.div custom={1} variants={fadeUp} initial="hidden" animate="visible" id="quickstart">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-500/10 border border-brand-500/20">
                  <PlayCircle className="h-4 w-4 text-brand-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Quickstart: Get Data Flowing in 5 Minutes</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">Local development with Docker Compose</p>
                </div>
              </div>
              <CodeBlock code={DOCKER_QUICKSTART} lang="bash" />
              <div className="mt-4 grid grid-cols-3 gap-3">
                {[
                  { step: "1", label: "Start Stack", desc: "docker-compose up -d postgres api" },
                  { step: "2", label: "Seed Data", desc: "docker-compose --profile seed up seeder" },
                  { step: "3", label: "Run dbt", desc: "docker-compose --profile dbt up dbt" },
                ].map((s) => (
                  <div key={s.step} className="rounded-lg border border-border/50 bg-muted/20 p-3 text-center">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500/20 text-brand-400 text-xs font-bold mx-auto mb-2">{s.step}</div>
                    <p className="text-xs font-semibold text-foreground">{s.label}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5 font-mono">{s.desc}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* API Reference */}
        <motion.div custom={2} variants={fadeUp} initial="hidden" animate="visible" id="api-ref">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/10 border border-violet-500/20">
                    <Code2 className="h-4 w-4 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">REST API Reference</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">Base URL: <code className="font-mono text-brand-400">https://api.flowsync.io/api/v1</code></p>
                  </div>
                </div>
                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-brand-400 hover:border-brand-500/30 transition-all">
                  <ExternalLink className="h-3 w-3" />Swagger UI
                </a>
              </div>

              <div className="mb-4 flex items-start gap-3 rounded-lg border border-brand-500/20 bg-brand-500/5 p-3">
                <Zap className="h-4 w-4 text-brand-400 shrink-0 mt-0.5" />
                <p className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">Authentication: </span>
                  All requests require <code className="rounded bg-muted px-1 py-0.5 font-mono text-brand-400">X-API-Key: fs_live_YOUR_KEY</code> header.
                  Get your key from <a href="/dashboard/settings" className="text-brand-400 underline underline-offset-2">Settings → API Keys</a>.
                </p>
              </div>

              <div className="space-y-1">
                {ENDPOINTS.map((ep) => (
                  <div key={ep.path} className="flex items-center gap-3 rounded-lg px-3 py-2.5 hover:bg-accent/30 transition-colors">
                    <span className={cn("shrink-0 rounded px-2 py-0.5 text-[10px] font-bold font-mono w-12 text-center", ep.method === "POST" ? "bg-emerald-500/15 text-emerald-400" : "bg-blue-500/15 text-blue-400")}>
                      {ep.method}
                    </span>
                    <code className="text-xs font-mono text-brand-400 flex-1 min-w-0 truncate">{ep.path}</code>
                    <span className="text-xs text-muted-foreground hidden sm:block flex-1">{ep.desc}</span>
                    <Badge variant="outline" className={cn("text-[10px] shrink-0", ep.tag === "Ingest" ? "text-emerald-400 border-emerald-500/30" : ep.tag === "Webhook" ? "text-violet-400 border-violet-500/30" : "text-blue-400 border-blue-500/30")}>
                      {ep.tag}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Code Examples */}
        <motion.div custom={3} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <FileText className="h-4 w-4 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Integration Examples</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">cURL and Python SDK snippets</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-xs font-semibold text-foreground mb-2">1. Ingest Account Data (cURL)</p>
                  <CodeBlock code={CURL_ACCOUNT} lang="bash" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-foreground mb-2">2. Ingest Subscription Data (cURL)</p>
                  <CodeBlock code={CURL_SUBSCRIPTION} lang="bash" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-foreground mb-2">3. Python SDK Pattern</p>
                  <CodeBlock code={PYTHON_SDK} lang="python" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Webhook Setup */}
        <motion.div custom={4} variants={fadeUp} initial="hidden" animate="visible" id="webhooks">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/10 border border-violet-500/20">
                  <Webhook className="h-4 w-4 text-violet-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Webhook Setup (Stripe)</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">Automatically sync billing events in real-time</p>
                </div>
              </div>
              <CodeBlock code={STRIPE_WEBHOOK} lang="bash" />
              <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
                {["subscription.created", "subscription.updated", "subscription.deleted", "invoice.payment_failed"].map((evt) => (
                  <div key={evt} className="rounded-lg border border-border/50 bg-muted/20 px-3 py-2 text-center">
                    <p className="text-[10px] font-mono text-muted-foreground">{evt}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* FAQ */}
        <motion.div custom={5} variants={fadeUp} initial="hidden" animate="visible">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <MessageCircle className="h-4 w-4 text-amber-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-foreground">Frequently Asked Questions</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">Common integration and data questions</p>
                </div>
              </div>

              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search FAQs..."
                  className="w-full rounded-lg border border-border bg-background pl-9 pr-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-500/40 transition-all"
                />
              </div>

              <div className="space-y-0">
                {filteredFaqs.length > 0 ? (
                  filteredFaqs.map((faq) => (
                    <Accordion key={faq.q} question={faq.q} answer={faq.a} />
                  ))
                ) : (
                  <p className="py-6 text-center text-sm text-muted-foreground">No FAQs match your search.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Support CTA */}
        <motion.div custom={6} variants={fadeUp} initial="hidden" animate="visible">
          <div className="rounded-xl border border-brand-500/20 bg-gradient-to-br from-brand-500/10 to-violet-500/5 p-6 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-500/20 border border-brand-500/30 mx-auto mb-3">
              <BookOpen className="h-5 w-5 text-brand-400" />
            </div>
            <h3 className="text-base font-bold text-foreground mb-1">Need more help?</h3>
            <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
              Check the full documentation, open a GitHub issue, or reach out to the FlowSync team directly.
            </p>
            <div className="flex items-center justify-center gap-3 flex-wrap">
              <a href="https://github.com/your-org/saas-revenue-intelligence" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:border-brand-500/30 transition-all">
                <ExternalLink className="h-3.5 w-3.5" />GitHub Repo
              </a>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 transition-all">
                <Code2 className="h-3.5 w-3.5" />Open API Docs
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
