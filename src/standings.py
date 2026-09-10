import pandas as pd

from src.team_names import OFFICIAL_TEAM_NAMES


def create_home_team_match_rows(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Create one row per match from the home team's perspective.
    """

    home_rows = matches[
        [
            "season",
            "date",
            "home_team",
            "away_team",
            "home_goals",
            "away_goals",
        ]
    ].copy()

    home_rows = home_rows.rename(
        columns={
            "home_team": "team",
            "away_team": "opponent",
            "home_goals": "goals_for",
            "away_goals": "goals_against",
        }
    )

    home_rows["venue"] = "home"

    home_rows["win"] = home_rows["goals_for"] > home_rows["goals_against"]
    home_rows["draw"] = home_rows["goals_for"] == home_rows["goals_against"]
    home_rows["loss"] = home_rows["goals_for"] < home_rows["goals_against"]

    return home_rows


def create_away_team_match_rows(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Create one row per match from the away team's perspective.
    """

    away_rows = matches[
        [
            "season",
            "date",
            "away_team",
            "home_team",
            "away_goals",
            "home_goals",
        ]
    ].copy()

    away_rows = away_rows.rename(
        columns={
            "away_team": "team",
            "home_team": "opponent",
            "away_goals": "goals_for",
            "home_goals": "goals_against",
        }
    )

    away_rows["venue"] = "away"

    away_rows["win"] = away_rows["goals_for"] > away_rows["goals_against"]
    away_rows["draw"] = away_rows["goals_for"] == away_rows["goals_against"]
    away_rows["loss"] = away_rows["goals_for"] < away_rows["goals_against"]

    return away_rows


def create_team_match_rows(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Convert match-level data into team-match-level data.

    Each match becomes two rows:
    - one for the home team
    - one for the away team
    """

    home_rows = create_home_team_match_rows(matches)
    away_rows = create_away_team_match_rows(matches)

    team_match_rows = pd.concat(
        [home_rows, away_rows],
        ignore_index=True
    )

    team_match_rows["points"] = (
        team_match_rows["win"].astype(int) * 3
        + team_match_rows["draw"].astype(int)
    )

    return team_match_rows


def create_standings_table(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Create final standings table by season and team.
    """

    team_match_rows = create_team_match_rows(matches)

    standings = (
        team_match_rows
        .groupby(["season", "team"], as_index=False)
        .agg(
            played=("team", "size"),
            wins=("win", "sum"),
            draws=("draw", "sum"),
            losses=("loss", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
            points=("points", "sum"),
        )
    )

    standings["goal_difference"] = (
        standings["goals_for"] - standings["goals_against"]
    )
    standings["team_official"] = standings["team"].map(OFFICIAL_TEAM_NAMES)

    # Sort according to standard league table logic.
    # Note: La Liga officially uses head-to-head as a tie-breaker.
    # Here we use points, goal difference, goals for as a simplified reproducible ranking.
    standings = standings.sort_values(
        by=[
            "season",
            "points",
            "goal_difference",
            "goals_for",
            "team",
        ],
        ascending=[True, False, False, False, True],
    )

    standings["position"] = (
        standings
        .groupby("season")
        .cumcount()
        + 1
    )

    standings = standings[
        [
            "season",
            "position",
            "team",
            "team_official",
            "played",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
        ]
    ].reset_index(drop=True)

    return standings

