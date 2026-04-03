"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { cn } from "@/lib/utils";

interface SectionWrapperProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
  delay?: number;
  direction?: "up" | "left" | "right" | "none";
}

export function SectionWrapper({
  children,
  className,
  id,
  delay = 0,
  direction = "up",
}: SectionWrapperProps) {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px 0px" });

  const variants = {
    hidden: {
      opacity: 0,
      y: direction === "up" ? 48 : 0,
      x: direction === "left" ? -48 : direction === "right" ? 48 : 0,
    },
    visible: {
      opacity: 1,
      y: 0,
      x: 0,
    },
  };

  return (
    <motion.section
      ref={ref}
      id={id}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={variants}
      transition={{ duration: 0.75, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={cn("relative", className)}
    >
      {children}
    </motion.section>
  );
}

// Stagger container for child animations
export function StaggerContainer({
  children,
  className,
  staggerDelay = 0.1,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
  id?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px 0px" });

  return (
    <motion.div
      ref={ref}
      id={id}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={{
        hidden: {},
        visible: { transition: { staggerChildren: staggerDelay } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// Individual stagger child
export function StaggerChild({
  children,
  className,
  direction = "up",
}: {
  children: React.ReactNode;
  className?: string;
  direction?: "up" | "left" | "right";
}) {
  return (
    <motion.div
      variants={{
        hidden: {
          opacity: 0,
          y: direction === "up" ? 32 : 0,
          x: direction === "left" ? -32 : direction === "right" ? 32 : 0,
        },
        visible: {
          opacity: 1,
          y: 0,
          x: 0,
          transition: { duration: 0.65, ease: [0.25, 0.46, 0.45, 0.94] },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
