"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { BarChart3, Menu, X, ArrowRight, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { label: "Why It Matters", href: "#why" },
  { label: "Features", href: "#features" },
  { label: "Architecture", href: "#architecture" },
  { label: "Insights", href: "#insights" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close mobile menu on resize
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 768) setMobileOpen(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <>
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        className={cn(
          "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
          scrolled
            ? "bg-slate-950/80 backdrop-blur-xl border-b border-white/[0.06] shadow-2xl shadow-black/20"
            : "bg-transparent"
        )}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="relative">
                <div className="absolute inset-0 bg-violet-500/30 rounded-lg blur-md group-hover:bg-violet-500/50 transition-all duration-300" />
                <div className="relative h-8 w-8 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                  <BarChart3 className="h-4.5 w-4.5 text-white" strokeWidth={2.5} />
                </div>
              </div>
              <div className="flex flex-col leading-none">
                <span className="text-sm font-bold text-white tracking-tight">
                  FlowSync
                </span>
                <span className="text-[9px] text-slate-500 font-medium tracking-widest uppercase">
                  Revenue Intelligence
                </span>
              </div>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="px-3.5 py-2 text-sm text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-all duration-200 font-medium"
                >
                  {link.label}
                </a>
              ))}
            </nav>

            {/* Desktop CTA */}
            <div className="hidden md:flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-slate-500">
                <Zap className="h-3 w-3 text-emerald-500" />
                <span>Live Demo</span>
              </div>
              <Link href="/dashboard">
                <Button
                  size="sm"
                  className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white border-0 shadow-lg shadow-violet-500/20 gap-1.5 h-8 px-4 text-xs font-semibold"
                >
                  Open Dashboard
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileOpen((v) => !v)}
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="fixed top-16 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur-xl border-b border-white/[0.06] shadow-2xl md:hidden"
          >
            <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col gap-1">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-4 py-3 text-sm text-slate-300 hover:text-white rounded-xl hover:bg-white/5 transition-all duration-200 font-medium"
                >
                  {link.label}
                </a>
              ))}
              <div className="pt-3 mt-2 border-t border-white/[0.06]">
                <Link href="/dashboard" onClick={() => setMobileOpen(false)}>
                  <Button className="w-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white border-0 gap-2">
                    Open Dashboard
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
