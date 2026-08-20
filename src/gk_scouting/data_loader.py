"""
gk_scouting.data_loader
------------------------
Carrega eventos da StatsBomb Open Data e isola tudo o que é relevante
para a análise de guarda-redes (ações de sweeper-keeper, defesas,
distribuição de bola).

Uso típico:
    from data_loader import load_competition_events, build_gk_events

    events = load_competition_events(competition_id=43, season_id=106)  # Mundial 2022
    gk_events = build_gk_events(events)
"""

import time
import warnings
import pandas as pd
from statsbombpy import sb

warnings.filterwarnings("ignore")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3


def _fetch_events_with_retry(match_id):
    """Tenta descarregar os eventos de um jogo, com retries em caso de falha de rede."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return sb.events(match_id=match_id)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"  [tentativa {attempt}/{MAX_RETRIES} falhou para o jogo {match_id}, "
                      f"a tentar de novo em {RETRY_DELAY_SECONDS}s...]")
                time.sleep(RETRY_DELAY_SECONDS)
    raise last_error


def load_competition_events(competition_id: int, season_id: int, match_ids=None) -> pd.DataFrame:
    """
    Descarrega os eventos de todos os jogos de uma competição/época.
    Se `match_ids` for passado, só descarrega esses jogos (mais rápido para testar).
    Devolve um único DataFrame com todos os eventos, com colunas extra
    'match_id' já incluídas pela própria biblioteca.

    Jogos que falhem mesmo após retries são ignorados (com aviso), em vez de
    interromperem todo o download.
    """
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    if match_ids is not None:
        matches = matches[matches["match_id"].isin(match_ids)]

    all_events = []
    failed = []
    total = len(matches)
    for i, (_, row) in enumerate(matches.iterrows(), start=1):
        print(f"[{i}/{total}] a descarregar jogo {row['match_id']} "
              f"({row['home_team']} x {row['away_team']})...")
        try:
            ev = _fetch_events_with_retry(row["match_id"])
            ev["home_team"] = row["home_team"]
            ev["away_team"] = row["away_team"]
            all_events.append(ev)
        except Exception as e:
            print(f"  [aviso] desisti do jogo {row['match_id']} após {MAX_RETRIES} tentativas: {e}")
            failed.append(row["match_id"])

    if not all_events:
        raise ConnectionError(
            "Não consegui descarregar NENHUM jogo. Isto é quase sempre falha de rede "
            "(firewall, antivírus, VPN, ou proxy a bloquear ligações a raw.githubusercontent.com). "
            "Testa abrir https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json "
            "num browser — se também falhar aí, o problema é da rede, não do código."
        )
    if failed:
        print(f"\n[aviso] {len(failed)} jogo(s) não foram incluídos: {failed}")

    return pd.concat(all_events, ignore_index=True)


def _split_location(df: pd.DataFrame, col: str, x_name: str, y_name: str) -> pd.DataFrame:
    """Separa uma coluna de localização [x, y] (lista) em duas colunas numéricas."""
    coords = df[col].apply(lambda v: v if isinstance(v, list) and len(v) == 2 else [None, None])
    df[x_name] = coords.apply(lambda v: v[0])
    df[y_name] = coords.apply(lambda v: v[1])
    return df


def build_gk_events(events: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra o DataFrame de eventos completo e devolve só os eventos
    de guarda-redes (tipo 'Goal Keeper'), com coordenadas separadas
    em colunas x/y prontas a usar em gráficos.
    """
    gk = events[events["type"] == "Goal Keeper"].copy()
    gk = _split_location(gk, "location", "x", "y")
    if "goalkeeper_end_location" in gk.columns:
        gk = _split_location(gk, "goalkeeper_end_location", "end_x", "end_y")

    keep_cols = [
        "match_id", "player", "player_id", "team", "minute", "second",
        "x", "y", "end_x", "end_y",
        "goalkeeper_type", "goalkeeper_outcome",
        "goalkeeper_technique", "goalkeeper_body_part", "goalkeeper_position",
        # Presentes apenas quando o dataset abrange varias competicoes/epocas
        # (ver download_extended_data.py). Preservadas aqui para permitir
        # agregar por contexto em build_scouting_table() e para consumo
        # direto por uma futura API. Ausentes em datasets de competicao
        # unica (ex.: events_full_wc2022.pkl) -- por isso o filtro abaixo.
        "competition_id", "season_id", "competition_name",
    ]
    keep_cols = [c for c in keep_cols if c in gk.columns]
    return gk[keep_cols].reset_index(drop=True)


def build_gk_passes(events: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra passes feitos por jogadores na posição de Guarda-Redes,
    para analisar a construção de jogo / distribuição.
    """
    passes = events[(events["type"] == "Pass") & (events["position"] == "Goalkeeper")].copy()
    passes = _split_location(passes, "location", "x", "y")
    if "pass_end_location" in passes.columns:
        passes = _split_location(passes, "pass_end_location", "end_x", "end_y")

    keep_cols = [
        "match_id", "player", "player_id", "team", "minute",
        "x", "y", "end_x", "end_y",
        "pass_length", "pass_outcome", "pass_height",
        "pass_body_part", "pass_type",
        # Ver a nota equivalente em build_gk_events().
        "competition_id", "season_id", "competition_name",
    ]
    keep_cols = [c for c in keep_cols if c in passes.columns]
    return passes[keep_cols].reset_index(drop=True)
