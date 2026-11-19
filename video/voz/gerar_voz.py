"""Gera a voz (IA, Piper, local e grátis) de um episódio e os tempos de cada frase.

Uso (a partir da pasta video/):
    python voz/gerar_voz.py ep01            # voz normal
    python voz/gerar_voz.py ep01 --velocidade 0.85   # mais rápida (menor = mais rápido)

Lê   src/episodios/<ep>.texto.json   (campo "fala" de cada cena)
Cria public/voz/<ep>/<cena>_<frase>.wav
     src/episodios/<ep>.voz.json     (duração de cada frase, em segundos)

Primeira vez:
    pip install piper-tts
    e descarrega a voz para voz/modelos/ (ver README).
"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "voz" / "modelos" / "pt_PT-tugao-medium.onnx"


def duracao(wav: Path) -> float:
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


def main():
    a = argparse.ArgumentParser()
    a.add_argument("episodio")
    a.add_argument("--velocidade", type=float, default=0.88, help="length_scale do Piper (1 = normal)")
    a.add_argument("--modelo", default=str(MODELO))
    args = a.parse_args()

    textos = json.loads((RAIZ / "src" / "episodios" / f"{args.episodio}.texto.json").read_text(encoding="utf-8"))
    saida = RAIZ / "public" / "voz" / args.episodio
    saida.mkdir(parents=True, exist_ok=True)

    tempos = []
    for i, cena in enumerate(textos):
        linha = []
        for j, frase in enumerate(cena["fala"]):
            wav = saida / f"{i}_{j}.wav"
            subprocess.run(
                [sys.executable, "-m", "piper", "-m", args.modelo, "--length-scale", str(args.velocidade), "-f", str(wav)],
                input=frase.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            d = duracao(wav)
            linha.append(round(d, 3))
            print(f"{i}_{j}  {d:5.2f}s  {frase}")
        tempos.append(linha)

    (RAIZ / "src" / "episodios" / f"{args.episodio}.voz.json").write_text(json.dumps(tempos), encoding="utf-8")
    print(f"\nTotal de voz: {sum(map(sum, tempos)):.1f}s")


if __name__ == "__main__":
    main()
