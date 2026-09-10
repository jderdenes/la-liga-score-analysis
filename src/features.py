import pandas as pd

from src.team_names import OFFICIAL_TEAM_NAMES


def create_participations_table(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Create a team participation table by season.

    The output contains one row per team per season.
    """

    home_teams = (
        matches[["season", "home_team"]]
        .rename(columns={"home_team": "team"})
    )

    away_teams = (
        matches[["season", "away_team"]]
        .rename(columns={"away_team": "team"})
    )

    participations = (
        pd.concat([home_teams, away_teams], ignore_index=True)
        .drop_duplicates()
        .sort_values(["season", "team"])
        .reset_index(drop=True)
    )

    return participations


def create_team_participation_counts(
    participations: pd.DataFrame
) -> pd.DataFrame:
    """
    Create a summary table with the number of seasons played by each team.
    """

    participation_counts = (
        participations
        .groupby("team", as_index=False)
        .agg(seasons_played=("season", "nunique"))
        .sort_values(["seasons_played", "team"], ascending=[False, True])
        .reset_index(drop=True)
    )

    participation_counts["team_official"] = (
        participation_counts["team"].map(OFFICIAL_TEAM_NAMES)
    )

    participation_counts = participation_counts[
        ["team", "team_official", "seasons_played"]
    ]

    return participation_counts


def create_team_match_stats(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Convert match-level data into team-match-level stats.

    Each match becomes two rows:
    - one from the home team's perspective
    - one from the away team's perspective
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

    team_match_stats = pd.concat(
        [home_rows, away_rows],
        ignore_index=True
    )

    team_match_stats["win"] = (
        team_match_stats["goals_for"]
        > team_match_stats["goals_against"]
    )

    team_match_stats["draw"] = (
        team_match_stats["goals_for"]
        == team_match_stats["goals_against"]
    )

    team_match_stats["loss"] = (
        team_match_stats["goals_for"]
        < team_match_stats["goals_against"]
    )

    team_match_stats["points"] = (
        team_match_stats["win"].astype(int) * 3
        + team_match_stats["draw"].astype(int)
    )

    team_match_stats["clean_sheet"] = (
        team_match_stats["goals_against"] == 0
    )

    team_match_stats["failed_to_score"] = (
        team_match_stats["goals_for"] == 0
    )

    return team_match_stats


def aggregate_team_stats(
    team_match_stats: pd.DataFrame,
    venue: str | None = None,
    prefix: str = ""
) -> pd.DataFrame:
    """
    Aggregate team-match stats by season and team.

    If venue is provided, only that venue is aggregated.
    Prefix is used for home/away columns.
    """

    df = team_match_stats.copy()

    if venue is not None:
        df = df.loc[df["venue"] == venue].copy()

    stats = (
        df
        .groupby(["season", "team"], as_index=False)
        .agg(
            matches=("team", "size"),
            wins=("win", "sum"),
            draws=("draw", "sum"),
            losses=("loss", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
            points=("points", "sum"),
            clean_sheets=("clean_sheet", "sum"),
            failed_to_score=("failed_to_score", "sum"),
        )
    )

    stats["goal_difference"] = (
        stats["goals_for"] - stats["goals_against"]
    )

    stats["points_per_match"] = (
        stats["points"] / stats["matches"]
    ).round(2)

    stats["goals_for_per_match"] = (
        stats["goals_for"] / stats["matches"]
    ).round(2)

    stats["goals_against_per_match"] = (
        stats["goals_against"] / stats["matches"]
    ).round(2)

    if prefix:
        rename_columns = {
            column: f"{prefix}_{column}"
            for column in stats.columns
            if column not in ["season", "team"]
        }

        stats = stats.rename(columns=rename_columns)

    return stats


def create_team_season_stats(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Create score-only team season stats with total, home and away metrics.
    """

    team_match_stats = create_team_match_stats(matches)

    total_stats = aggregate_team_stats(
        team_match_stats=team_match_stats,
        venue=None,
        prefix=""
    )

    home_stats = aggregate_team_stats(
        team_match_stats=team_match_stats,
        venue="home",
        prefix="home"
    )

    away_stats = aggregate_team_stats(
        team_match_stats=team_match_stats,
        venue="away",
        prefix="away"
    )

    team_season_stats = (
        total_stats
        .merge(
            home_stats,
            on=["season", "team"],
            how="left"
        )
        .merge(
            away_stats,
            on=["season", "team"],
            how="left"
        )
    )

    team_season_stats["team_official"] = (
        team_season_stats["team"].map(OFFICIAL_TEAM_NAMES)
    )

    team_season_stats = team_season_stats[
        [
            "season",
            "team",
            "team_official",

            "matches",
            "wins",
            "draws",
            "losses",
            "points",
            "points_per_match",
            "goals_for",
            "goals_against",
            "goal_difference",
            "goals_for_per_match",
            "goals_against_per_match",
            "clean_sheets",
            "failed_to_score",

            "home_matches",
            "home_wins",
            "home_draws",
            "home_losses",
            "home_points",
            "home_points_per_match",
            "home_goals_for",
            "home_goals_against",
            "home_goal_difference",
            "home_goals_for_per_match",
            "home_goals_against_per_match",
            "home_clean_sheets",
            "home_failed_to_score",

            "away_matches",
            "away_wins",
            "away_draws",
            "away_losses",
            "away_points",
            "away_points_per_match",
            "away_goals_for",
            "away_goals_against",
            "away_goal_difference",
            "away_goals_for_per_match",
            "away_goals_against_per_match",
            "away_clean_sheets",
            "away_failed_to_score",
        ]
    ].sort_values(
        ["season", "points", "goal_difference", "goals_for", "team"],
        ascending=[True, False, False, False, True]
    ).reset_index(drop=True)

    return team_season_stats
