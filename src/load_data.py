from pathlib import Path
import pandas as pd

from src.config import RAW_DATA_DIR


def get_raw_files(raw_data_dir: Path = RAW_DATA_DIR) -> list[Path]:
    """
    Return all raw La Liga season CSV files.

    Expected filename format:
    2010-11_SP1.csv
    2011-12_SP1.csv
    ...
    """

    raw_files = sorted(raw_data_dir.glob("*_SP1.csv"))

    if not raw_files:
        raise FileNotFoundError(
            f"No raw season files found in: {raw_data_dir}"
        )

    return raw_files


def extract_season_from_filename(file_path: Path) -> str:
    """
    Extract season label from filename.

    Example:
    2010-11_SP1.csv -> 2010-11
    """

    return file_path.stem.replace("_SP1", "")


def load_season_file(file_path: Path) -> pd.DataFrame:
    """
    Load one season CSV file and add a season column.
    """

    season = extract_season_from_filename(file_path)

    df = pd.read_csv(file_path)

    # Add season identifier
    df["season"] = season

    # Add source file for traceability
    df["source_file"] = file_path.name

    return df


def load_all_matches(raw_data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """
    Load all raw season CSV files and combine them into one DataFrame.
    """

    raw_files = get_raw_files(raw_data_dir)

    season_dfs = []

    for file_path in raw_files:
        season_df = load_season_file(file_path)
        season_dfs.append(season_df)

    all_matches = pd.concat(season_dfs, ignore_index=True)

    return all_matches
