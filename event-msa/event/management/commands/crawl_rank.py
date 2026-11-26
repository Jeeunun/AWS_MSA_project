# event/management/commands/crawl_rank.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from ...models import Season, TotalRank, AttackRank, DefenseRank

import requests
import pandas as pd
from pathlib import Path

DAUM_KBO_RANK_API = (
    "https://sports.daum.net/prx/hermes/api/team/rank.json"
    "?leagueCode=kbo&seasonKey={season}&page=1&pageSize=100"
)


def _fetch_from_daum(season: int, timeout: int = 15):
    """다음 KBO 팀 순위 API 호출 후 전체 JSON 반환"""
    url = DAUM_KBO_RANK_API.format(season=season)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data


def _build_dataframes(teams: list):
    """API 값을 사용해 정렬만 수행하여 DF 3개 생성 (순위 계산/삽입 없음)""" 
    overall_rows, attack_rows, defense_rows = [], [], []

    for t in teams:
        team_name = t.get("shortNameKo") or t.get("teamName") or t.get("team", {}).get("name")
        rk = t.get("rank") if isinstance(t.get("rank"), dict) else {
            "rank": t.get("rank"),
            "game": t.get("game"),
            "win": t.get("win"),
            "draw": t.get("draw"),
            "loss": t.get("loss"),
            "wpct": t.get("wpct"),
            "gb": t.get("gb"),
            "streak": t.get("streak"),
        }
        st = t.get("stat", {}) or {}

        overall_rows.append({
            "team": team_name,
            "rank": rk.get("rank"),
            "game": rk.get("game"),
            "win": rk.get("win"),
            "draw": rk.get("draw"),
            "loss": rk.get("loss"),
            "wpct": rk.get("wpct"),
            "gb": rk.get("gb"),
            "streak": rk.get("streak"),
        })

        attack_rows.append({
            "team": team_name,
            "batAvg": st.get("batAvg"),
            "batObp": st.get("batObp"),
            "batSlg": st.get("batSlg"),
            "batOps": st.get("batOps"),
            "batAb": st.get("batAb"),
            "batH": st.get("batH"),
            "bat2b": st.get("bat2b"),
            "bat3b": st.get("bat3b"),
            "batHr": st.get("batHr"),
            "batRbi": st.get("batRbi"),
            "batR": st.get("batR"),
            "batSb": st.get("batSb"),
            "batBbhp": st.get("batBbhp"),
            "batSo": st.get("batSo"),
            "batGdp": st.get("batGdp"),
        })

        defense_rows.append({
            "team": team_name,
            "pitEra": st.get("pitEra"),
            "pitWhip": st.get("pitWhip"),
            "pitIp": st.get("pitIp"),
            "pitH": st.get("pitH"),
            "pitHr": st.get("pitHr"),
            "pitR": st.get("pitR"),
            "pitEr": st.get("pitEr"),
            "pitBbhp": st.get("pitBbhp"),
            "pitSo": st.get("pitSo"),
            "fldErr": st.get("fldErr"),
            "pitQs": st.get("pitQs"),
            "pitHld": st.get("pitHld"),
            "pitSv": st.get("pitSv"),
        })

    # 정렬 기준: wpct(내림차순), batAvg(내림차순), pitEra(오름차순)
    df_overall = (
        pd.DataFrame(overall_rows)
        .sort_values(by="wpct", ascending=False, na_position="last")
        .reset_index(drop=True)
    )
    df_attack = (
        pd.DataFrame(attack_rows)
        .sort_values(by="batAvg", ascending=False, na_position="last")
        .reset_index(drop=True)
    )
    df_defense = (
        pd.DataFrame(defense_rows)
        .sort_values(by="pitEra", ascending=True, na_position="last")
        .reset_index(drop=True)
    )

    # 타입 안전화(숫자형 문자열/None/NaN 혼재 대비)
    for col in ["rank", "game", "win", "draw", "loss"]:
        if col in df_overall.columns:
            df_overall[col] = pd.to_numeric(df_overall[col], errors="coerce")
    for col in ["wpct", "gb"]:
        if col in df_overall.columns:
            df_overall[col] = pd.to_numeric(df_overall[col], errors="coerce")

    if "batAvg" in df_attack: df_attack["batAvg"] = pd.to_numeric(df_attack["batAvg"], errors="coerce")
    if "batObp" in df_attack: df_attack["batObp"] = pd.to_numeric(df_attack["batObp"], errors="coerce")
    if "batSlg" in df_attack: df_attack["batSlg"] = pd.to_numeric(df_attack["batSlg"], errors="coerce")
    if "batOps" in df_attack: df_attack["batOps"] = pd.to_numeric(df_attack["batOps"], errors="coerce")
    for col in ["batAb","batH","bat2b","bat3b","batHr","batRbi","batR","batSb","batBbhp","batSo","batGdp"]:
        if col in df_attack: df_attack[col] = pd.to_numeric(df_attack[col], errors="coerce")

    if "pitEra" in df_defense: df_defense["pitEra"] = pd.to_numeric(df_defense["pitEra"], errors="coerce")
    if "pitWhip" in df_defense: df_defense["pitWhip"] = pd.to_numeric(df_defense["pitWhip"], errors="coerce")
    for col in ["pitH","pitHr","pitR","pitEr","pitBbhp","pitSo","fldErr","pitQs","pitHld","pitSv"]:
        if col in df_defense: df_defense[col] = pd.to_numeric(df_defense[col], errors="coerce")

    return df_overall, df_attack, df_defense


class Command(BaseCommand):
    help = "다음(Daum) KBO 팀 순위를 가져와 DB에 덮어쓰기 저장합니다. (Total/Attack/Defense)"

    def add_arguments(self, parser):
        parser.add_argument("--season", type=int, default=2025, help="시즌(예: 2025)")
        parser.add_argument("--top-n", type=int, default=None, help="상위 N개 팀만 처리(옵션)")
        parser.add_argument("--save-csv-dir", type=str, default=None, help="CSV도 저장할 디렉터리(옵션)")

    @transaction.atomic
    def handle(self, *args, **opts):
        season = opts["season"]
        top_n = opts["top_n"]
        save_csv_dir = opts["save_csv_dir"]

        data = _fetch_from_daum(season=season)

        # 1) API 호출
        season_meta = data.get("season", {}) or {}
        teams = data.get("list", []) or []

        # 시즌 테이블에 데이터 저장
        season_obj, _ = Season.objects.update_or_create(
            season=season,
            defaults={
            "startDate": season_meta.get("startDate"),
            "endDate": season_meta.get("endDate"),
            },
        )
        
        if top_n:
            teams = teams[:top_n]
        df_overall, df_attack, df_defense = _build_dataframes(teams)

        # 2) CSV 저장(옵션)
        if save_csv_dir:
            out = Path(save_csv_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"kbo_{season}_overall.csv").write_text(
                df_overall.to_csv(index=False, encoding="utf-8-sig"), encoding="utf-8"
            )
            (out / f"kbo_{season}_attack.csv").write_text(
                df_attack.to_csv(index=False, encoding="utf-8-sig"), encoding="utf-8"
            )
            (out / f"kbo_{season}_defense.csv").write_text(
                df_defense.to_csv(index=False, encoding="utf-8-sig"), encoding="utf-8"
            )

        # 3) 덮어쓰기 저장: 기존 데이터 전부 삭제 후 bulk_create
        with transaction.atomic():
            TotalRank.objects.filter(season__season=season).delete()
            AttackRank.objects.filter(season__season=season).delete()
            DefenseRank.objects.filter(season__season=season).delete()

            total_objs = [
                TotalRank(
                    rank=int(row["rank"]) if pd.notna(row["rank"]) else None,
                    season=season_obj,
                    team=(str(row["team"]) if pd.notna(row["team"]) else ""),
                    game=int(row["game"]) if pd.notna(row["game"]) else None,
                    win=int(row["win"]) if pd.notna(row["win"]) else None,
                    draw=int(row["draw"]) if pd.notna(row["draw"]) else None,
                    loss=int(row["loss"]) if pd.notna(row["loss"]) else None,
                    wpct=Decimal(str(row["wpct"])) if pd.notna(row["wpct"]) else None,
                    gb=Decimal(str(row["gb"])) if pd.notna(row["gb"]) else None,
                    streak=(str(row["streak"]) if pd.notna(row["streak"]) else None),
                )
                for _, row in df_overall.iterrows()
            ]

            # Attack/Defense는 API에 rank가 없으므로 정렬 순서로 채움(모델 NOT NULL 대비)
            attack_objs = [
                AttackRank(
                    rank=i + 1,
                    season=season_obj,
                    team=(str(row["team"]) if pd.notna(row["team"]) else ""),
                    batAb=_i(row.get("batAb")),   batH=_i(row.get("batH")),
                    bat2b=_i(row.get("bat2b")),   bat3b=_i(row.get("bat3b")),
                    batHr=_i(row.get("batHr")),   batRbi=_i(row.get("batRbi")),
                    batR=_i(row.get("batR")),     batSb=_i(row.get("batSb")),
                    batBbhp=_i(row.get("batBbhp")), batSo=_i(row.get("batSo")),
                    batGdp=_i(row.get("batGdp")),
                    batAvg=_d(row.get("batAvg")), batObp=_d(row.get("batObp")),
                    batSlg=_d(row.get("batSlg")), batOps=_d(row.get("batOps")),
                )
                for i, row in df_attack.iterrows()
            ]

            defense_objs = [
                DefenseRank(
                    rank=i + 1,
                    season=season_obj,
                    team=(str(row["team"]) if pd.notna(row["team"]) else ""),
                    pitIp=(str(row["pitIp"]) if pd.notna(row["pitIp"]) else None),
                    pitH=_i(row.get("pitH")),     pitHr=_i(row.get("pitHr")),
                    pitR=_i(row.get("pitR")),     pitEr=_i(row.get("pitEr")),
                    pitBbhp=_i(row.get("pitBbhp")), pitSo=_i(row.get("pitSo")),
                    fldErr=_i(row.get("fldErr")), pitQs=_i(row.get("pitQs")),
                    pitHld=_i(row.get("pitHld")), pitSv=_i(row.get("pitSv")),
                    pitEra=_d(row.get("pitEra")), pitWhip=_d(row.get("pitWhip")),
                )
                for i, row in df_defense.iterrows()
            ]

            TotalRank.objects.bulk_create(total_objs, batch_size=1000)
            AttackRank.objects.bulk_create(attack_objs, batch_size=1000)
            DefenseRank.objects.bulk_create(defense_objs, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"season={season} 순위 덮어쓰기 저장 완료: total={len(total_objs)}, attack={len(attack_objs)}, defense={len(defense_objs)}"
        ))


def _i(x):
    """정수형 안전 변환: NaN/None/문자 → None 또는 int"""
    if pd.isna(x): return None
    try:
        return int(x)
    except Exception:
        try:
            return int(str(x).strip())
        except Exception:
            return None


def _d(x):
    """DecimalField 안전 변환: NaN/None/문자 → None 또는 Decimal"""
    if pd.isna(x): return None
    try:
        return Decimal(str(x))
    except Exception:
        return None
