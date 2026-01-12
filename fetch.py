import logging
import time
import fastf1
import pandas as pd
import numpy as np
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
SEASONS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("csv_data")

# Mute FastF1 info messages, only show warnings/errors
logging.getLogger('fastf1').setLevel(logging.WARNING)
fastf1.Cache.enable_cache(str(CACHE_DIR))


# ==========================================
# HELPER FUNCTIONS
# ==========================================
def find_cached_sessions():
    """Find all cached sessions for the specified seasons."""
    cached_sessions = []
    if not CACHE_DIR.exists():
        return []

    for year_dir in sorted(CACHE_DIR.iterdir()):
        if year_dir.is_dir() and year_dir.name.isdigit():
            year = int(year_dir.name)
            if year not in SEASONS:
                continue
            for session_dir in sorted(year_dir.iterdir()):
                if session_dir.is_dir():
                    # We are looking for race sessions usually
                    cached_sessions.append((year, session_dir.name))
    return cached_sessions


def extract_race_name(session_name):
    """Clean up folder name to get race name."""
    parts = session_name.split('_', 1)
    if len(parts) == 2:
        return parts[1].replace('_', ' ')
    return session_name


def to_seconds(x):
    """Converts Timedelta to seconds (float), handling NaNs safely."""
    if pd.isna(x):
        return np.nan
    if hasattr(x, 'total_seconds'):
        return x.total_seconds()
    return x


# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    print("=" * 50)
    print("FastF1 Data Extractor (ML Ready)")
    print(f"Target Seasons: {SEASONS}")
    print("=" * 50)

    cached_sessions = find_cached_sessions()
    print(f"\nFound {len(cached_sessions)} cached sessions.")

    if not cached_sessions:
        print("No cache found. Please run your scrape script first.")
        return

    all_laps = []
    all_weather = []
    all_trackStatus = []
    race_metadata = []

    # Loop through sessions
    for i, (year, session_name) in enumerate(cached_sessions, 1):
        race_name = extract_race_name(session_name)
        print(f"[{i}/{len(cached_sessions)}] {year} {race_name}...", end=" ", flush=True)

        try:
            # --- FIX: SLEEP TO PREVENT 429 ERRORS ---
            time.sleep(2)

            session = fastf1.get_session(year, race_name, 'R')

            # Load data
            # Note: If 'laps' fails, the session might be empty or invalid
            session.load(laps=True, telemetry=False, weather=True, messages=True)

            # ------------------------------------------
            # 1. EXTRACT RACE METADATA (For Risk Calc)
            # ------------------------------------------
            circuit_loc = session.event.get('Location', 'Unknown')
            race_meta = {
                'Season': year,
                'Round': session.event.RoundNumber,
                'RaceName': race_name,
                'CircuitLocation': circuit_loc,
                'Country': session.event.get('Country', 'Unknown')
            }
            race_metadata.append(race_meta)

            # ------------------------------------------
            # 2. EXTRACT & CONVERT LAPS
            # ------------------------------------------
            laps = session.laps.copy()
            laps['Season'] = year
            laps['Round'] = session.event.RoundNumber
            laps['CircuitLocation'] = circuit_loc

            # Convert critical times to Seconds (Float) for ML
            laps['LapStartTime_Sec'] = laps['LapStartTime'].apply(to_seconds)
            laps['LapTime_Sec'] = laps['LapTime'].apply(to_seconds)
            laps['Sector1Time_Sec'] = laps['Sector1Time'].apply(to_seconds)
            laps['Sector2Time_Sec'] = laps['Sector2Time'].apply(to_seconds)
            laps['Sector3Time_Sec'] = laps['Sector3Time'].apply(to_seconds)

            # Keep Datetime for merging
            laps['Date'] = session.date + laps['LapStartTime']

            # Select useful columns
            cols_to_keep = [
                'Date', 'Season', 'Round', 'CircuitLocation', 'LapNumber',
                'DriverNumber', 'Team', 'TyreLife', 'Compound', 'TrackStatus',
                'LapStartTime_Sec', 'LapTime_Sec',
                'Sector1Time_Sec', 'Sector2Time_Sec', 'Sector3Time_Sec',
                'Position', 'FreshTyre'
            ]
            # Filter for columns that actually exist
            cols_to_keep = [c for c in cols_to_keep if c in laps.columns]
            laps = laps[cols_to_keep]

            all_laps.append(laps)

            # ------------------------------------------
            # 3. EXTRACT WEATHER
            # ------------------------------------------
            weather = session.weather_data.copy()
            weather['Season'] = year
            weather['Round'] = session.event.RoundNumber
            if 'Date' not in weather.columns:
                weather['Date'] = session.date + weather['Time']
            all_weather.append(weather)

            # ------------------------------------------
            # 4. EXTRACT TRACK STATUS
            # ------------------------------------------
            trackStatus = session.track_status.copy()
            trackStatus['Season'] = year
            trackStatus['Round'] = session.event.RoundNumber
            trackStatus['Date'] = session.date + trackStatus['Time']
            all_trackStatus.append(trackStatus)

            print(f"OK ({len(laps)} laps)")

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                print(f"\n[!] Rate Limit (429) hit. Cooling down for 15 seconds...")
                time.sleep(15)
            else:
                print(f"ERROR: {e}")

    # ==========================================
    # MERGE AND SAVE
    # ==========================================
    if not all_laps:
        print("\nNo data extracted.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 50)
    print("Processing & Saving CSVs...")

    # Concatenate all dataframes
    laps_df = pd.concat(all_laps, ignore_index=True)
    weather_df = pd.concat(all_weather, ignore_index=True)
    track_status_df = pd.concat(all_trackStatus, ignore_index=True)
    meta_df = pd.DataFrame(race_metadata)

    # Sort by Date for correct merging
    laps_df = laps_df.sort_values('Date')
    weather_df = weather_df.sort_values('Date')
    track_status_df = track_status_df.sort_values('Date')

    # Save Meta Data
    meta_df.to_csv(OUTPUT_DIR / 'race_metadata.csv', index=False)
    print("- Saved race_metadata.csv")

    # Merge Weather onto Laps (AsOf Merge)
    print("- Merging Weather...")
    laps_merged = pd.merge_asof(
        laps_df,
        weather_df[['Date', 'Rainfall', 'AirTemp', 'TrackTemp', 'Humidity', 'WindSpeed', 'WindDirection']],
        on='Date',
        direction='backward'
    )

    # Merge Track Status onto Laps (AsOf Merge)
    print("- Merging Track Status...")
    # Rename 'Status' to avoid confusion if needed, usually it's 'Status' column in track_status
    if 'Status' in track_status_df.columns:
        track_status_df = track_status_df.rename(columns={'Status': 'TrackStatus_Detail'})

    laps_merged = pd.merge_asof(
        laps_merged,
        track_status_df[['Date', 'TrackStatus_Detail']],
        on='Date',
        direction='backward'
    )

    # Save Final File
    final_path = OUTPUT_DIR / 'f1_race_data_v2.csv'
    laps_merged.to_csv(final_path, index=False)

    print(f"\nSUCCESS!")
    print(f"Final dataset saved to: {final_path}")
    print(f"Total Rows: {len(laps_merged)}")


if __name__ == "__main__":
    main()