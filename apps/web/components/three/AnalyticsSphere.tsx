"use client";

import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, Torus, Points, PointMaterial, Float } from "@react-three/drei";
import * as THREE from "three";

// ─── Orbiting ring ────────────────────────────────────────────────────────────
function OrbitalRing({
  radius,
  tubeRadius,
  color,
  emissive,
  rotationX,
  rotationZ,
  speed,
}: {
  radius: number;
  tubeRadius: number;
  color: string;
  emissive: string;
  rotationX: number;
  rotationZ: number;
  speed: number;
}) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!ref.current) return;
    ref.current.rotation.z = state.clock.getElapsedTime() * speed;
  });

  return (
    <Torus
      ref={ref}
      args={[radius, tubeRadius, 16, 120]}
      rotation={[rotationX, 0, rotationZ]}
    >
      <meshStandardMaterial
        color={color}
        emissive={emissive}
        emissiveIntensity={0.6}
        metalness={0.9}
        roughness={0.1}
        transparent
        opacity={0.85}
      />
    </Torus>
  );
}

// ─── Orbiting data node ───────────────────────────────────────────────────────
function DataNode({
  orbitRadius,
  orbitSpeed,
  orbitOffset,
  color,
  size,
}: {
  orbitRadius: number;
  orbitSpeed: number;
  orbitOffset: number;
  color: string;
  size: number;
}) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!ref.current) return;
    const t = state.clock.getElapsedTime() * orbitSpeed + orbitOffset;
    ref.current.position.x = Math.cos(t) * orbitRadius;
    ref.current.position.y = Math.sin(t * 0.7) * orbitRadius * 0.4;
    ref.current.position.z = Math.sin(t) * orbitRadius;
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[size, 8, 8]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={1.2}
        metalness={0.5}
        roughness={0.2}
      />
    </mesh>
  );
}

// ─── Particle field ───────────────────────────────────────────────────────────
function ParticleField({ count = 300 }: { count?: number }) {
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 3.2 + Math.random() * 2.5;
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, [count]);

  const ref = useRef<THREE.Points>(null);

  useFrame((state) => {
    if (!ref.current) return;
    ref.current.rotation.y = state.clock.getElapsedTime() * 0.04;
    ref.current.rotation.x = state.clock.getElapsedTime() * 0.02;
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#a78bfa"
        size={0.025}
        sizeAttenuation
        depthWrite={false}
        opacity={0.55}
      />
    </Points>
  );
}

// ─── Core sphere ──────────────────────────────────────────────────────────────
function CoreSphere() {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!ref.current) return;
    ref.current.rotation.y = state.clock.getElapsedTime() * 0.08;
    ref.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.15) * 0.05;
  });

  return (
    <group ref={ref}>
      {/* Inner core */}
      <Sphere args={[1, 64, 64]}>
        <meshStandardMaterial
          color="#3730a3"
          emissive="#1e1b4b"
          emissiveIntensity={0.4}
          metalness={0.95}
          roughness={0.05}
        />
      </Sphere>

      {/* Outer glow shell */}
      <Sphere args={[1.08, 32, 32]}>
        <meshStandardMaterial
          color="#7c3aed"
          transparent
          opacity={0.08}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </Sphere>

      {/* Wireframe overlay */}
      <Sphere args={[1.02, 16, 16]}>
        <meshBasicMaterial
          color="#6366f1"
          wireframe
          transparent
          opacity={0.12}
        />
      </Sphere>
    </group>
  );
}

// ─── Full scene ───────────────────────────────────────────────────────────────
function Scene() {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.25} />
      <pointLight position={[6, 6, 6]} intensity={2.5} color="#7c3aed" />
      <pointLight position={[-6, -4, -6]} intensity={1.5} color="#0ea5e9" />
      <pointLight position={[0, 8, 0]} intensity={0.8} color="#10b981" />

      {/* Floating wrapper for gentle bob */}
      <Float speed={1.2} rotationIntensity={0.15} floatIntensity={0.4}>
        <CoreSphere />

        {/* Orbital rings */}
        <OrbitalRing
          radius={1.85}
          tubeRadius={0.018}
          color="#818cf8"
          emissive="#4f46e5"
          rotationX={Math.PI / 3}
          rotationZ={0}
          speed={0.18}
        />
        <OrbitalRing
          radius={2.3}
          tubeRadius={0.012}
          color="#38bdf8"
          emissive="#0284c7"
          rotationX={-Math.PI / 5}
          rotationZ={Math.PI / 4}
          speed={-0.12}
        />
        <OrbitalRing
          radius={2.7}
          tubeRadius={0.008}
          color="#34d399"
          emissive="#059669"
          rotationX={Math.PI / 7}
          rotationZ={-Math.PI / 6}
          speed={0.09}
        />

        {/* Orbiting data nodes */}
        <DataNode orbitRadius={2.0} orbitSpeed={0.5} orbitOffset={0} color="#f59e0b" size={0.07} />
        <DataNode orbitRadius={2.4} orbitSpeed={0.35} orbitOffset={2.1} color="#10b981" size={0.055} />
        <DataNode orbitRadius={1.7} orbitSpeed={0.65} orbitOffset={4.2} color="#f472b6" size={0.05} />
        <DataNode orbitRadius={2.6} orbitSpeed={0.28} orbitOffset={1.0} color="#60a5fa" size={0.065} />
        <DataNode orbitRadius={1.9} orbitSpeed={0.45} orbitOffset={3.5} color="#a78bfa" size={0.045} />
      </Float>

      {/* Particle field (outside Float so it rotates independently) */}
      <ParticleField count={280} />
    </>
  );
}

// ─── Exported canvas component ────────────────────────────────────────────────
export function AnalyticsSphere() {
  return (
    <Canvas
      camera={{ position: [0, 0, 6.5], fov: 42 }}
      gl={{ antialias: true, alpha: true }}
      style={{ background: "transparent" }}
      dpr={[1, 1.5]}
    >
      <Scene />
    </Canvas>
  );
}
