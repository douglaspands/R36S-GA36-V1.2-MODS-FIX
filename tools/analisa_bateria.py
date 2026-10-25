"""Resume o r36-thermal.csv no PC: ponto de partida e queda da bateria por boot.

Uso: uv run python -I tools/analisa_bateria.py r36-thermal.1.csv r36-thermal.csv

Por boot imprime a tensão, o bat_pct (kernel) e o bat_pct_est (estimativa própria) das
primeiras amostras, a diferença entre os dois percentuais e a queda por hora de cada um
nas linhas em Discharging. Colunas que faltam (CSV antigo) são avisadas, não são erro.
"""

import csv
import sys
from datetime import datetime

N_INICIO = 5  # amostras que formam o "ponto de partida" do boot
ESPERADAS = ("boot", "uptime_s", "bat_status", "bat_pct", "bat_voltage", "bat_current",
             "bat_charge_now", "bat_charge_full", "bat_pct_est")


def inteiro(texto):
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None


def tempo(linha):
    """Segundos da amostra: uptime_s, ou a data se o CSV não tiver a coluna."""
    up = inteiro(linha.get("uptime_s"))
    if up is not None:
        return up
    try:
        return datetime.strptime(linha.get("date", ""), "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def media(linhas, coluna):
    vals = [v for v in (inteiro(l.get(coluna)) for l in linhas) if v is not None]
    return sum(vals) / len(vals) if vals else None


def queda_por_hora(linhas, coluna):
    """Queda (pontos percentuais por hora) entre a primeira e a última amostra."""
    pts = [(tempo(l), inteiro(l.get(coluna))) for l in linhas]
    pts = [(t, v) for t, v in pts if t is not None and v is not None]
    if len(pts) < 2 or pts[-1][0] <= pts[0][0]:
        return None
    return (pts[0][1] - pts[-1][1]) * 3600 / (pts[-1][0] - pts[0][0])


def fmt(valor, unidade=""):
    return "n/d" if valor is None else f"{valor:.1f}{unidade}"


def le_csv(caminho, avisos):
    with open(caminho, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        faltam = [c for c in ESPERADAS if c not in (leitor.fieldnames or [])]
        if faltam:
            avisos.append(f"{caminho}: colunas ausentes: {', '.join(faltam)}")
        return list(leitor)


def resumo(caminhos):
    """Devolve (linhas do resumo, avisos)."""
    avisos = []
    boots = {}
    for c in caminhos:
        for linha in le_csv(c, avisos):
            boots.setdefault(linha.get("boot") or "?", []).append(linha)

    saida = []
    for boot, linhas in boots.items():
        linhas.sort(key=lambda l: tempo(l) if tempo(l) is not None else 0)
        inicio = linhas[:N_INICIO]
        mv = media(inicio, "bat_voltage")
        kernel = media(inicio, "bat_pct")
        est = media(inicio, "bat_pct_est")
        dif = kernel - est if kernel is not None and est is not None else None
        desc = [l for l in linhas if l.get("bat_status") == "Discharging"]
        saida.append(f"boot {boot}: {len(linhas)} amostras, {len(desc)} em descarga")
        saida.append(f"  início ({len(inicio)} amostras): tensão {fmt(mv, ' mV')}, "
                     f"kernel {fmt(kernel, '%')}, estimado {fmt(est, '%')}, "
                     f"diferença kernel - estimado {fmt(dif, ' pontos')}")
        saida.append(f"  descarga: kernel {fmt(queda_por_hora(desc, 'bat_pct'), ' pontos/h')}, "
                     f"estimado {fmt(queda_por_hora(desc, 'bat_pct_est'), ' pontos/h')}")
    return saida, avisos


def main(argv):
    if not argv:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    try:
        saida, avisos = resumo(argv)
    except OSError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    for a in avisos:
        print(f"aviso: {a}", file=sys.stderr)
    print("\n".join(saida))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
