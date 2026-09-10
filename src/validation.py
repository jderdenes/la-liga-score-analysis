import pandas as pd


CRITICAL_COLUMNS = [
    "season",
    "date",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
]


def check_matches_per_season(
    df: pd.DataFrame,
    expected_matches: int = 380
) -> pd.DataFrame:
    """
    Check that each season has the expected number of matches.
    """

    result = (
        df
        .groupby("season")
        .size()
        .reset_index(name="matches")
    )

    result["expected_matches"] = expected_matches
    result["is_valid"] = result["matches"] == expected_matches

    return result


def check_teams_per_season(
    df: pd.DataFrame,
    expected_teams: int = 20
) -> pd.DataFrame:
    """
    Check that each season has the expected number of unique teams.
    """

    result = (
        df
        .groupby("season")
        .apply(
            lambda season_df: len(
                set(season_df["home_team"]) | set(season_df["away_team"])
            )
        )
        .reset_index(name="teams")
    )

    result["expected_teams"] = expected_teams
    result["is_valid"] = result["teams"] == expected_teams

    return result


def check_nulls(
    df: pd.DataFrame,
    columns: list[str] | None = None
) -> pd.DataFrame:
    """
    Check null values in critical columns.
    """

    if columns is None:
        columns = CRITICAL_COLUMNS

    result = (
        df[columns]
        .isna()
        .sum()
        .reset_index()
    )

    result.columns = ["column", "null_count"]
    result["is_valid"] = result["null_count"] == 0

    return result


def check_results_are_valid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check that full-time result matches the full-time goals.

    Requires result_is_valid column from clean_data.py.
    """

    if "result_is_valid" not in df.columns:
        raise ValueError(
            "Column 'result_is_valid' not found. "
            "Run clean_all_matches() before validation."
        )

    total_rows = len(df)
    valid_rows = int(df["result_is_valid"].sum())
    invalid_rows = int((~df["result_is_valid"]).sum())

    result = pd.DataFrame(
        {
            "check": ["results_are_valid"],
            "total_rows": [total_rows],
            "valid_rows": [valid_rows],
            "invalid_rows": [invalid_rows],
        }
    )

    result["is_valid"] = result["invalid_rows"] == 0

    return result



def check_score_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check that goal columns contain valid non-negative values.
    """

    checks = []

    for column in ["home_goals", "away_goals"]:
        checks.append(
            {
                "column": column,
                "min_value": df[column].min(),
                "max_value": df[column].max(),
                "null_count": df[column].isna().sum(),
                "negative_count": (df[column] < 0).sum(),
            }
        )

    result = pd.DataFrame(checks)

    result["is_valid"] = (
        (result["null_count"] == 0)
        & (result["negative_count"] == 0)
    )

    return result


def check_duplicate_matches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check duplicate matches based on season, date, home team, and away team.
    """

    duplicate_columns = [
        "season",
        "date",
        "home_team",
        "away_team",
    ]

    duplicates = df[df.duplicated(subset=duplicate_columns, keep=False)]

    result = pd.DataFrame(
        {
            "check": ["duplicate_matches"],
            "duplicate_rows": [len(duplicates)],
            "is_valid": [len(duplicates) == 0],
        }
    )

    return result


def run_all_validation_checks(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Run all validation checks and return a validation report.
    """

    validation_report = {
        "matches_per_season": check_matches_per_season(df),
        "teams_per_season": check_teams_per_season(df),
        "nulls": check_nulls(df),
        "results_are_valid": check_results_are_valid(df),
        "score_values": check_score_values(df),
        "duplicate_matches": check_duplicate_matches(df),
    }

    return validation_report

def check_standings_teams_per_season(
    standings: pd.DataFrame,
    expected_teams: int = 20
) -> pd.DataFrame:
    """
    Check that each season has the expected number of teams in standings.
    """

    result = (
        standings
        .groupby("season", as_index=False)
        .agg(teams=("team", "nunique"))
    )

    result["expected_teams"] = expected_teams
    result["is_valid"] = result["teams"] == expected_teams

    return result


def check_standings_played_matches(
    standings: pd.DataFrame,
    expected_played: int = 38
) -> pd.DataFrame:
    """
    Check that every team played the expected number of matches.
    """

    result = standings[
        [
            "season",
            "team",
            "team_official",
            "played",
        ]
    ].copy()

    result["expected_played"] = expected_played
    result["is_valid"] = result["played"] == expected_played

    return result


def check_standings_record_totals(standings: pd.DataFrame) -> pd.DataFrame:
    """
    Check that wins + draws + losses equals played.
    """

    result = standings[
        [
            "season",
            "team",
            "team_official",
            "played",
            "wins",
            "draws",
            "losses",
        ]
    ].copy()

    result["record_total"] = (
        result["wins"]
        + result["draws"]
        + result["losses"]
    )

    result["is_valid"] = result["record_total"] == result["played"]

    return result


def check_standings_goal_difference(standings: pd.DataFrame) -> pd.DataFrame:
    """
    Check that goal difference equals goals_for - goals_against.
    """

    result = standings[
        [
            "season",
            "team",
            "team_official",
            "goals_for",
            "goals_against",
            "goal_difference",
        ]
    ].copy()

    result["calculated_goal_difference"] = (
        result["goals_for"]
        - result["goals_against"]
    )

    result["is_valid"] = (
        result["calculated_goal_difference"]
        == result["goal_difference"]
    )

    return result


def check_standings_goals_balance(standings: pd.DataFrame) -> pd.DataFrame:
    """
    Check that total goals for equals total goals against per season.

    In a league table, every goal scored by one team is conceded by another.
    """

    result = (
        standings
        .groupby("season", as_index=False)
        .agg(
            total_goals_for=("goals_for", "sum"),
            total_goals_against=("goals_against", "sum"),
        )
    )

    result["is_valid"] = (
        result["total_goals_for"]
        == result["total_goals_against"]
    )

    return result


def check_standings_points_reconciliation(
    matches: pd.DataFrame,
    standings: pd.DataFrame
) -> pd.DataFrame:
    """
    Check that standings points match the points implied by match results.

    A win gives 3 total points.
    A draw gives 2 total points, one to each team.
    """

    expected_points = (
        matches
        .assign(
            expected_match_points=lambda x: x["result"].map(
                {
                    "H": 3,
                    "A": 3,
                    "D": 2,
                }
            )
        )
        .groupby("season", as_index=False)
        .agg(expected_points=("expected_match_points", "sum"))
    )

    actual_points = (
        standings
        .groupby("season", as_index=False)
        .agg(actual_points=("points", "sum"))
    )

    result = expected_points.merge(
        actual_points,
        on="season",
        how="left"
    )

    result["is_valid"] = (
        result["expected_points"]
        == result["actual_points"]
    )

    return result


def check_standings_official_team_names(standings: pd.DataFrame) -> pd.DataFrame:
    """
    Check that every standings row has an official team name.
    """

    result = standings[
        [
            "season",
            "team",
            "team_official",
        ]
    ].copy()

    result["is_valid"] = result["team_official"].notna()

    return result


def run_standings_validation_checks(
    matches: pd.DataFrame,
    standings: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """
    Run all standings validation checks.
    """

    validation_report = {
        "standings_teams_per_season": check_standings_teams_per_season(
            standings
        ),
        "standings_played_matches": check_standings_played_matches(
            standings
        ),
        "standings_record_totals": check_standings_record_totals(
            standings
        ),
        "standings_goal_difference": check_standings_goal_difference(
            standings
        ),
        "standings_goals_balance": check_standings_goals_balance(
            standings
        ),
        "standings_points_reconciliation": check_standings_points_reconciliation(
            matches,
            standings
        ),
        "standings_official_team_names": check_standings_official_team_names(
            standings
        ),
    }

    return validation_report


def check_team_season_stats_rows(
    team_season_stats: pd.DataFrame,
    expected_rows: int = 200
) -> pd.DataFrame:
    """
    Check that team season stats has the expected number of rows.
    """

    result = pd.DataFrame(
        {
            "check": ["team_season_stats_rows"],
            "rows": [len(team_season_stats)],
            "expected_rows": [expected_rows],
        }
    )

    result["is_valid"] = result["rows"] == result["expected_rows"]

    return result


def check_team_season_stats_teams_per_season(
    team_season_stats: pd.DataFrame,
    expected_teams: int = 20
) -> pd.DataFrame:
    """
    Check that each season has the expected number of teams.
    """

    result = (
        team_season_stats
        .groupby("season", as_index=False)
        .agg(teams=("team", "nunique"))
    )

    result["expected_teams"] = expected_teams
    result["is_valid"] = result["teams"] == expected_teams

    return result


def check_team_season_stats_matches(
    team_season_stats: pd.DataFrame,
    expected_matches: int = 38,
    expected_home_matches: int = 19,
    expected_away_matches: int = 19
) -> pd.DataFrame:
    """
    Check total, home and away matches per team-season.
    """

    result = team_season_stats[
        [
            "season",
            "team",
            "team_official",
            "matches",
            "home_matches",
            "away_matches",
        ]
    ].copy()

    result["expected_matches"] = expected_matches
    result["expected_home_matches"] = expected_home_matches
    result["expected_away_matches"] = expected_away_matches

    result["is_valid"] = (
        (result["matches"] == expected_matches)
        & (result["home_matches"] == expected_home_matches)
        & (result["away_matches"] == expected_away_matches)
        & (result["home_matches"] + result["away_matches"] == result["matches"])
    )

    return result


def check_team_season_stats_record_totals(
    team_season_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Check that wins + draws + losses equals matches for total, home and away.
    """

    result = team_season_stats[
        [
            "season",
            "team",
            "team_official",
            "matches",
            "wins",
            "draws",
            "losses",
            "home_matches",
            "home_wins",
            "home_draws",
            "home_losses",
            "away_matches",
            "away_wins",
            "away_draws",
            "away_losses",
        ]
    ].copy()

    result["total_record_sum"] = (
        result["wins"] + result["draws"] + result["losses"]
    )

    result["home_record_sum"] = (
        result["home_wins"] + result["home_draws"] + result["home_losses"]
    )

    result["away_record_sum"] = (
        result["away_wins"] + result["away_draws"] + result["away_losses"]
    )

    result["is_valid"] = (
        (result["total_record_sum"] == result["matches"])
        & (result["home_record_sum"] == result["home_matches"])
        & (result["away_record_sum"] == result["away_matches"])
    )

    return result


def check_team_season_stats_home_away_totals(
    team_season_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Check that total values equal home + away values.
    """

    checks = [
        {
            "metric": "wins",
            "is_valid": (
                team_season_stats["wins"]
                == team_season_stats["home_wins"] + team_season_stats["away_wins"]
            ).all(),
        },
        {
            "metric": "draws",
            "is_valid": (
                team_season_stats["draws"]
                == team_season_stats["home_draws"] + team_season_stats["away_draws"]
            ).all(),
        },
        {
            "metric": "losses",
            "is_valid": (
                team_season_stats["losses"]
                == team_season_stats["home_losses"] + team_season_stats["away_losses"]
            ).all(),
        },
        {
            "metric": "points",
            "is_valid": (
                team_season_stats["points"]
                == team_season_stats["home_points"] + team_season_stats["away_points"]
            ).all(),
        },
        {
            "metric": "goals_for",
            "is_valid": (
                team_season_stats["goals_for"]
                == team_season_stats["home_goals_for"] + team_season_stats["away_goals_for"]
            ).all(),
        },
        {
            "metric": "goals_against",
            "is_valid": (
                team_season_stats["goals_against"]
                == team_season_stats["home_goals_against"] + team_season_stats["away_goals_against"]
            ).all(),
        },
        {
            "metric": "clean_sheets",
            "is_valid": (
                team_season_stats["clean_sheets"]
                == team_season_stats["home_clean_sheets"] + team_season_stats["away_clean_sheets"]
            ).all(),
        },
        {
            "metric": "failed_to_score",
            "is_valid": (
                team_season_stats["failed_to_score"]
                == team_season_stats["home_failed_to_score"] + team_season_stats["away_failed_to_score"]
            ).all(),
        },
    ]

    return pd.DataFrame(checks)


def check_team_season_stats_official_names(
    team_season_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Check that every row has an official team name.
    """

    result = team_season_stats[
        [
            "season",
            "team",
            "team_official",
        ]
    ].copy()

    result["is_valid"] = result["team_official"].notna()

    return result


def check_team_season_stats_against_standings(
    team_season_stats: pd.DataFrame,
    standings: pd.DataFrame
) -> pd.DataFrame:
    """
    Check that team season stats agrees with standings for core metrics.
    """

    comparison = standings.merge(
        team_season_stats[
            [
                "season",
                "team",
                "matches",
                "wins",
                "draws",
                "losses",
                "goals_for",
                "goals_against",
                "goal_difference",
                "points",
            ]
        ],
        on=["season", "team"],
        how="left",
        suffixes=("_standings", "_stats"),
    )

    checks = []

    checks.append(
        {
            "metric": "played_vs_matches",
            "is_valid": (
                comparison["played"] == comparison["matches"]
            ).all(),
        }
    )

    for metric in [
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]:
        checks.append(
            {
                "metric": metric,
                "is_valid": (
                    comparison[f"{metric}_standings"]
                    == comparison[f"{metric}_stats"]
                ).all(),
            }
        )

    return pd.DataFrame(checks)


def run_team_season_stats_validation_checks(
    team_season_stats: pd.DataFrame,
    standings: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """
    Run all validation checks for team season stats.
    """

    validation_report = {
        "team_season_stats_rows": check_team_season_stats_rows(
            team_season_stats
        ),
        "team_season_stats_teams_per_season": check_team_season_stats_teams_per_season(
            team_season_stats
        ),
        "team_season_stats_matches": check_team_season_stats_matches(
            team_season_stats
        ),
        "team_season_stats_record_totals": check_team_season_stats_record_totals(
            team_season_stats
        ),
        "team_season_stats_home_away_totals": check_team_season_stats_home_away_totals(
            team_season_stats
        ),
        "team_season_stats_official_names": check_team_season_stats_official_names(
            team_season_stats
        ),
        "team_season_stats_against_standings": check_team_season_stats_against_standings(
            team_season_stats,
            standings
        ),
    }

    return validation_report

