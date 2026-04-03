"use client";

import React, { useEffect, useRef } from "react";
import { useMotionValue, useSpring, useInView } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
  duration?: number;
}

export function AnimatedCounter({
  value,
  prefix = "",
  suffix = "",
  decimals = 0,
  className,
  duration = 1800,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, {
    duration,
    bounce: 0,
  });
  const isInView = useInView(ref, { once: true, margin: "-40px 0px" });

  useEffect(() => {
    if (isInView) {
      motionValue.set(value);
    }
  }, [isInView, value, motionValue]);

  useEffect(() => {
    const unsubscribe = springValue.on("change", (latest) => {
      if (ref.current) {
        ref.current.textContent =
          prefix + latest.toFixed(decimals) + suffix;
      }
    });
    return unsubscribe;
  }, [springValue, prefix, suffix, decimals]);

  return (
    <span ref={ref} className={cn("tabular-nums", className)}>
      {prefix}0{suffix}
    </span>
  );
}
