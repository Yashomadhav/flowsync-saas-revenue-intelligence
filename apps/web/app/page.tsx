import React from "react";
import { Navbar } from "@/components/landing/Navbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { WhyItMatters } from "@/components/landing/WhyItMatters";
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { ArchitectureSection } from "@/components/landing/ArchitectureSection";
import { InsightsSection } from "@/components/landing/InsightsSection";
import { CTASection } from "@/components/landing/CTASection";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Navbar />
      <main>
        {/* Hero: 3D sphere + animated KPI badges + dashboard preview */}
        <HeroSection />

        {/* Why It Matters: animated stat counters + 6 metric cards */}
        <WhyItMatters />

        {/* Features: 5 dashboard pages with interactive tab preview */}
        <FeaturesSection />

        {/* Architecture: 5-layer accordion with live diagram */}
        <ArchitectureSection />

        {/* Insights: 6 business insight cards from the data */}
        <InsightsSection />

        {/* Final CTA: buttons + tech badges + stats */}
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
