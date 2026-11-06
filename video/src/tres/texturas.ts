import * as THREE from "three";

const canvas = (w: number, h: number) => {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return c;
};

// Número/inicial na camisola
export const texturaTexto = (texto: string, cor = "rgba(10,15,26,0.8)", fonte = "900 150px Archivo") => {
  const c = canvas(256, 256);
  const g = c.getContext("2d")!;
  g.font = fonte;
  g.fillStyle = cor;
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText(texto, 128, 138);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
};

// Painel LED com a marca, repetido (para deslizar com offset)
export const texturaPainel = (texto: string, cor: string, fundo: string) => {
  const c = canvas(2048, 128);
  const g = c.getContext("2d")!;
  g.fillStyle = fundo;
  g.fillRect(0, 0, 2048, 128);
  g.font = "700 84px 'Barlow Condensed'";
  g.textBaseline = "middle";
  const passo = 680;
  for (let x = 20; x < 2048; x += passo) {
    g.fillStyle = cor;
    g.fillRect(x, 34, 60, 60);
    g.fillStyle = "#F4F6FA";
    g.fillText(texto, x + 84, 68);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
};

// Bola: branca com manchas escuras simples
export const texturaBola = () => {
  const c = canvas(512, 256);
  const g = c.getContext("2d")!;
  g.fillStyle = "#F4F6FA";
  g.fillRect(0, 0, 512, 256);
  g.fillStyle = "#1B2333";
  const pts = [
    [64, 64], [192, 40], [320, 70], [448, 44], [128, 150], [256, 128], [384, 160], [32, 210], [224, 216], [416, 230],
  ];
  pts.forEach(([x, y]) => {
    g.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
      g.lineTo(x + Math.cos(a) * 26, y + Math.sin(a) * 22);
    }
    g.closePath();
    g.fill();
  });
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
};
