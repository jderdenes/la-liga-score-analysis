import pandas as pd
from src.team_names import OFFICIAL_TEAM_NAMES


COLUMN_MAPPING = {
    # Match info
    "Date": "date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",

    # Full-time score and result
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",

    # Half-time score and result
    "HTHG": "half_time_home_goals",
    "HTAG": "half_time_away_goals",
    "HTR": "half_time_result",

    # Match statistics
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_on_target",
    "AST": "away_shots_on_target",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellow_cards",
    "AY": "away_yellow_cards",
    "HR": "home_red_cards",
    "AR": "away_red_cards",
}


BASE_COLUMNS = [
    "season",
    "date",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "source_file",
]


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename raw football-data columns to readable snake_case column names.
    """

    return df.rename(columns=COLUMN_MAPPING)


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse match date column to datetime.

    The raw files contain two date formats:
    - DD/MM/YY, for example 28/08/10
    - DD/MM/YYYY, for example 17/08/2018

    We parse both formats explicitly to avoid ambiguous date parsing.
    """

    df = df.copy()

    # First try DD/MM/YY
    parsed_dates_short_year = pd.to_datetime(
        df["date"],
        format="%d/%m/%y",
        errors="coerce"
    )

    # Then try DD/MM/YYYY
    parsed_dates_long_year = pd.to_datetime(
        df["date"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Use the first successful parse, otherwise fall back to the second
    df["date"] = parsed_dates_short_year.fillna(parsed_dates_long_year)

    return df


def keep_base_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the core columns needed for the first clean matches dataset.

    If some optional columns are missing in a season file, they are skipped.
    """

    available_columns = [
        col for col in BASE_COLUMNS
        if col in df.columns
    ]

    return df[available_columns].copy()


def add_expected_result(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add expected result based on full-time goals.

    H = home win
    D = draw
    A = away win
    """

    df = df.copy()

    df["expected_result"] = "D"

    df.loc[df["home_goals"] > df["away_goals"], "expected_result"] = "H"
    df.loc[df["home_goals"] < df["away_goals"], "expected_result"] = "A"

    return df


def validate_result_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that the provided result column matches the goals.

    Adds a boolean column:
    result_is_valid
    """

    df = df.copy()

    df["result_is_valid"] = df["result"] == df["expected_result"]

    return df


def clean_all_matches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw all_matches dataset.

    Main steps:
    1. Rename columns
    2. Parse dates
    3. Keep core columns
    4. Add official team names
    5. Add expected result
    6. Validate result
    """

    clean_df = (
        df
        .pipe(rename_columns)
        .pipe(parse_dates)
        .pipe(keep_base_columns)
        .pipe(add_official_team_names)
        .pipe(add_expected_result)
        .pipe(validate_result_column)
    )

    return clean_df


def add_official_team_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add official team name columns while keeping the raw team names.

    Raw names are kept for traceability.
    Official names are used for cleaner reporting and visualizations.
    """

    df = df.copy()

    df["home_team_official"] = df["home_team"].map(OFFICIAL_TEAM_NAMES)
    df["away_team_official"] = df["away_team"].map(OFFICIAL_TEAM_NAMES)

    return df

