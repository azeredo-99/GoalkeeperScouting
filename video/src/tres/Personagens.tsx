import React, { useMemo } from "react";
import * as THREE from "three";
import { useThree } from "@react-three/fiber";
import { texturaBola, texturaTexto } from "./texturas";

const PELE = "#E2B48E";

const Braco: React.FC<{ lado: 1 | -1; rot: number; cor: string }> = ({ lado, rot, cor }) => (
  <group position={[lado * 0.27, 1.36, 0]} rotation={[0, 0, rot]}>
    <mesh position={[0, -0.28, 0]} castShadow>
      <capsuleGeometry args={[0.065, 0.42, 6, 12]} />
      <meshStandardMaterial color={cor} roughness={0.7} />
    </mesh>
    <mesh position={[0, -0.6, 0]} castShadow>
      <sphereGeometry args={[0.095, 16, 12]} />
      <meshStandardMaterial color="#F4F6FA" roughness={0.6} />
    </mesh>
  </group>
);

// Guarda-redes feito de formas simples. Origem nos pés, de frente para +z.
// `mergulho`: 0 = posição de espera, 1 = esticado no ar; `lado`: +1 mergulha para +x
export const GuardaRedes3D: React.FC<{
  cor: string;
  texto?: string;
  posicao?: [number, number, number];
  rotacaoY?: number;
  mergulho?: number;
  lado?: 1 | -1;
  alcance?: number; // metros que o mergulho cobre
}> = ({ cor, texto = "GR", posicao = [0, 0, 0], rotacaoY = 0, mergulho = 0, lado = 1, alcance = 1.9 }) => {
  const numero = useMemo(() => texturaTexto(texto), [texto]);
  const d = mergulho;
  const corpoRot = -lado * d * 1.35;
  const dx = lado * d * alcance;
  const dy = Math.sin(d * Math.PI) * 0.45 + d * 0.3;
  // braços: em espera ligeiramente abertos; no mergulho esticados por cima da cabeça
  const bracoFora = lado * (0.5 + d * 2.1);
  const bracoDentro = -lado * 0.5 + lado * d * 2.9;
  return (
    <group position={posicao} rotation={[0, rotacaoY, 0]}>
      <group position={[dx, dy, 0]}>
        <group position={[0, 0.9, 0]} rotation={[0, 0, corpoRot]}>
          <group position={[0, -0.9, 0]}>
            {/* pernas e chuteiras */}
            {[-1, 1].map((s) => (
              <group key={s}>
                <mesh position={[s * 0.11, 0.45, 0]} castShadow>
                  <capsuleGeometry args={[0.085, 0.6, 6, 12]} />
                  <meshStandardMaterial color="#1B2333" roughness={0.8} />
                </mesh>
                <mesh position={[s * 0.11, 0.05, 0.05]} castShadow>
                  <boxGeometry args={[0.13, 0.1, 0.28]} />
                  <meshStandardMaterial color="#0A0D14" />
                </mesh>
              </group>
            ))}
            {/* tronco */}
            <mesh position={[0, 1.17, 0]} castShadow>
              <capsuleGeometry args={[0.2, 0.42, 8, 16]} />
              <meshStandardMaterial color={cor} roughness={0.7} />
            </mesh>
            <mesh position={[0, 1.2, 0.205]}>
              <planeGeometry args={[0.32, 0.32]} />
              <meshBasicMaterial map={numero} transparent />
            </mesh>
            {/* cabeça e cabelo */}
            <mesh position={[0, 1.62, 0]} castShadow>
              <sphereGeometry args={[0.13, 20, 16]} />
              <meshStandardMaterial color={PELE} roughness={0.8} />
            </mesh>
            <mesh position={[0, 1.66, -0.01]}>
              <sphereGeometry args={[0.135, 20, 16, 0, Math.PI * 2, 0, Math.PI / 2.2]} />
              <meshStandardMaterial color="#2A1C14" roughness={0.9} />
            </mesh>
            <Braco lado={1} rot={lado === 1 ? bracoFora : bracoDentro} cor={cor} />
            <Braco lado={-1} rot={lado === 1 ? bracoDentro : bracoFora} cor={cor} />
          </group>
        </group>
      </group>
    </group>
  );
};

export const Bola: React.FC<{ posicao: [number, number, number]; rodar?: number }> = ({ posicao, rodar = 0 }) => {
  const tex = useMemo(() => texturaBola(), []);
  return (
    <mesh position={posicao} rotation={[rodar, rodar * 0.6, 0]} castShadow>
      <sphereGeometry args={[0.11, 24, 18]} />
      <meshStandardMaterial map={tex} roughness={0.5} />
    </mesh>
  );
};

// Câmara controlada por frame
export const Camara: React.FC<{ pos: [number, number, number]; alvo: [number, number, number]; fov?: number }> = ({
  pos,
  alvo,
  fov = 45,
}) => {
  const { camera } = useThree();
  const cam = camera as THREE.PerspectiveCamera;
  cam.position.set(...pos);
  if (cam.fov !== fov) {
    cam.fov = fov;
    cam.updateProjectionMatrix();
  }
  cam.lookAt(...alvo);
  return null;
};

// Projeta um ponto 3D para píxeis do ecrã (para pôr etiquetas HTML por cima)
export const projetar = (
  ponto: [number, number, number],
  pos: [number, number, number],
  alvo: [number, number, number],
  fov: number,
  largura: number,
  altura: number,
) => {
  const cam = new THREE.PerspectiveCamera(fov, largura / altura, 0.1, 200);
  cam.position.set(...pos);
  cam.lookAt(...alvo);
  cam.updateMatrixWorld();
  const v = new THREE.Vector3(...ponto).project(cam);
  return { x: ((v.x + 1) / 2) * largura, y: ((1 - v.y) / 2) * altura };
};
