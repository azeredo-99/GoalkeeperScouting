import React, { useMemo } from "react";
import * as THREE from "three";
import { useCurrentFrame } from "remotion";
import { MARCA } from "../marca";
import { texturaPainel } from "./texturas";

// Medidas reais (metros). Linha de golo em z = 0, o campo cresce para +z.
export const BALIZA = { largura: 7.32, altura: 2.44, fundo: 1.6 };

const Linha: React.FC<{ x: number; z: number; w: number; d: number }> = ({ x, z, w, d }) => (
  <mesh position={[x, 0.012, z]} rotation={[-Math.PI / 2, 0, 0]}>
    <planeGeometry args={[w, d]} />
    <meshStandardMaterial color="#EEF2F6" roughness={0.9} />
  </mesh>
);

const Relvado: React.FC = () => {
  const faixas = useMemo(() => Array.from({ length: 14 }, (_, i) => i), []);
  return (
    <group>
      {faixas.map((i) => (
        <mesh key={i} position={[0, 0, -8 + i * 5 + 2.5]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[90, 5]} />
          <meshStandardMaterial color={i % 2 ? "#2F8F3F" : "#2A8238"} roughness={1} />
        </mesh>
      ))}
      {/* linha de golo, pequena área, grande área, marca de penálti */}
      <Linha x={0} z={0} w={68} d={0.12} />
      <Linha x={-9.16} z={2.75} w={0.12} d={5.5} />
      <Linha x={9.16} z={2.75} w={0.12} d={5.5} />
      <Linha x={0} z={5.5} w={18.32} d={0.12} />
      <Linha x={-20.16} z={8.25} w={0.12} d={16.5} />
      <Linha x={20.16} z={8.25} w={0.12} d={16.5} />
      <Linha x={0} z={16.5} w={40.32} d={0.12} />
      <mesh position={[0, 0.013, 11]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.12, 24]} />
        <meshStandardMaterial color="#EEF2F6" />
      </mesh>
    </group>
  );
};

const Baliza: React.FC = () => {
  const { largura: L, altura: A, fundo: F } = BALIZA;
  const rede = useMemo(() => {
    const p: number[] = [];
    const passo = 0.25;
    // fundo
    for (let x = -L / 2; x <= L / 2 + 1e-6; x += passo) p.push(x, 0, -F, x, A * 0.75, -F);
    for (let y = 0; y <= A * 0.75 + 1e-6; y += passo) p.push(-L / 2, y, -F, L / 2, y, -F);
    // teto inclinado (da trave ao fundo)
    for (let x = -L / 2; x <= L / 2 + 1e-6; x += passo) p.push(x, A, 0, x, A * 0.75, -F);
    // lados
    for (const s of [-1, 1]) {
      for (let z = 0; z >= -F - 1e-6; z -= passo) p.push((s * L) / 2, 0, z, (s * L) / 2, A + (A * 0.75 - A) * (-z / F), z);
      for (let y = 0; y <= A * 0.75 + 1e-6; y += passo) p.push((s * L) / 2, y, 0, (s * L) / 2, y, -F);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    return g;
  }, [L, A, F]);
  const branco = <meshStandardMaterial color="#F7F9FB" roughness={0.4} />;
  return (
    <group>
      <mesh position={[-L / 2, A / 2, 0]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, A, 16]} />
        {branco}
      </mesh>
      <mesh position={[L / 2, A / 2, 0]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, A, 16]} />
        {branco}
      </mesh>
      <mesh position={[0, A, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, L + 0.12, 16]} />
        {branco}
      </mesh>
      <lineSegments geometry={rede}>
        <lineBasicMaterial color="#E6ECF2" transparent opacity={0.55} />
      </lineSegments>
    </group>
  );
};

// Bancada: degraus escuros com público em cores da marca (discretas)
const Bancada: React.FC = () => {
  const n = 6000;
  const { matrizes, cores } = useMemo(() => {
    const m: THREE.Matrix4[] = [];
    const c: THREE.Color[] = [];
    const paleta = ["#1E2A44", "#2A3A5C", "#3DF5B0", "#F4F6FA", "#4FA3FF", "#FF8A3D", "#16203A"];
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < n; i++) {
      const fila = Math.floor(rnd() * 16);
      const x = -32 + rnd() * 64;
      const y = 1.4 + fila * 0.62 + 0.25;
      const z = -12 - fila * 0.85;
      m.push(new THREE.Matrix4().makeTranslation(x, y, z));
      const r = rnd();
      c.push(new THREE.Color(paleta[r < 0.55 ? 0 : r < 0.75 ? 1 : r < 0.8 ? 2 : r < 0.88 ? 3 : r < 0.93 ? 4 : r < 0.97 ? 5 : 6]));
    }
    return { matrizes: m, cores: c };
  }, []);
  const ref = React.useRef<THREE.InstancedMesh>(null);
  React.useLayoutEffect(() => {
    if (!ref.current) return;
    matrizes.forEach((mm, i) => {
      ref.current!.setMatrixAt(i, mm);
      ref.current!.setColorAt(i, cores[i]);
    });
    ref.current.instanceMatrix.needsUpdate = true;
    if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true;
  }, [matrizes, cores]);
  return (
    <group>
      {Array.from({ length: 16 }).map((_, f) => (
        <mesh key={f} position={[0, 1.4 + f * 0.62 - 0.3, -12 - f * 0.85]}>
          <boxGeometry args={[70, 0.62, 0.85]} />
          <meshStandardMaterial color="#0C1322" roughness={1} />
        </mesh>
      ))}
      <instancedMesh ref={ref} args={[undefined, undefined, n]}>
        <sphereGeometry args={[0.13, 6, 5]} />
        <meshStandardMaterial roughness={1} />
      </instancedMesh>
    </group>
  );
};

const PainelLED: React.FC = () => {
  const frame = useCurrentFrame();
  const tex = useMemo(() => texturaPainel(MARCA.serie, MARCA.cores.destaque, "#0A0F1A"), []);
  tex.repeat.set(6, 1);
  tex.offset.x = frame * 0.004;
  return (
    <mesh position={[0, 0.4, -10]}>
      <boxGeometry args={[70, 0.8, 0.1]} />
      <meshBasicMaterial map={tex} toneMapped={false} color="#5E6A80" />
    </mesh>
  );
};

export const Estadio: React.FC = () => (
  <group>
    <color attach="background" args={[MARCA.cores.fundo]} />
    <fog attach="fog" args={[MARCA.cores.fundo, 30, 75]} />
    <hemisphereLight args={["#DDE8FF", "#1A3A22", 0.9]} />
    <directionalLight
      position={[8, 18, 14]}
      intensity={2.2}
      castShadow
      shadow-mapSize-width={1024}
      shadow-mapSize-height={1024}
      shadow-camera-left={-12}
      shadow-camera-right={12}
      shadow-camera-top={12}
      shadow-camera-bottom={-12}
    />
    <Relvado />
    <Baliza />
    <PainelLED />
    <Bancada />
  </group>
);
