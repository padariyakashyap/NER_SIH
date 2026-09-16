"""
ETA Prediction Dataset Builder for SIH Project

This script constructs `eta_training_data.csv` from source CSV files:
- `bus_gps_data.csv`
- `historical_data.csv`
- `route_data.csv`

Proxy ETA Calculation Methodology:
-----------------------------------
Since the raw GPS dataset does not include a ground-truth arrival time (ETA),
we construct a proxy target `eta_minutes` using available geographical and historical data:

1. Map each GPS coordinate to the nearest route stop (`nearest_stop_index`).
2. Identify the target destination stop (`destination_stop_index`), which is the next stop 
   along the route sequence (or the final stop if the bus is already near the final stop).
3. Compute the great-circle geographic distance (`distance_to_destination_km`) from the bus's 
   current location to the destination stop using the Haversine formula.
4. Derive `time_slot` (0-23) from the GPS timestamp hour and join historical route statistics 
   (`historical_avg_speed`, `historical_delay_minutes`).
5. Calculate `effective_speed` as the arithmetic mean of current GPS speed and historical average speed.
6. Estimate baseline travel time: `travel_time_minutes = (distance_to_destination_km / effective_speed) * 60`.
7. Compute proxy ETA: `eta_minutes = travel_time_minutes + historical_delay_minutes`.
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Define paths relative to this script using pathlib
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

gps_path = DATA_DIR / "bus_gps_data.csv"
historical_path = DATA_DIR / "historical_data.csv"
route_path = DATA_DIR / "route_data.csv"
output_path = DATA_DIR / "eta_training_data.csv"


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth specified in decimal degrees using the Haversine formula.
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0  # Earth's radius in kilometers
    return r * c


def main():
    # 1. Load source datasets
    gps_df = pd.read_csv(gps_path)
    historical_df = pd.read_csv(historical_path)
    route_df = pd.read_csv(route_path)

    initial_row_count = len(gps_df)

    # 2. Convert timestamp to datetime and extract time_slot (0-23)
    gps_df["timestamp"] = pd.to_datetime(gps_df["timestamp"])
    gps_df["time_slot"] = gps_df["timestamp"].dt.hour

    # Organize route stops by route_id into indexed stop lists
    # Each route has ordered stops: stop_index = 0, 1, 2, ...
    route_stops = {}
    for route_id, group in route_df.groupby("route_id"):
        # Reset index so stop_index corresponds to sequential stop order (0, 1, 2, 3, 4)
        stops_seq = group.reset_index(drop=True)
        route_stops[route_id] = stops_seq

    # 3. Process each GPS point: determine nearest stop, destination stop, and distance
    nearest_stop_indices = []
    dest_stop_indices = []
    distances_km = []

    for _, row in gps_df.iterrows():
        r_id = row["route_id"]
        bus_lat = row["latitude"]
        bus_lon = row["longitude"]

        stops_df = route_stops[r_id]
        stop_lats = stops_df["latitude"].values
        stop_lons = stops_df["longitude"].values

        # Haversine distance to all stops on this route
        dist_to_all_stops = haversine(bus_lat, bus_lon, stop_lats, stop_lons)
        nearest_idx = int(np.argmin(dist_to_all_stops))

        max_idx = len(stops_df) - 1
        # Target the next stop, or final stop if already at final stop
        dest_idx = min(nearest_idx + 1, max_idx)

        # Destination stop coordinates
        dest_lat = stops_df.loc[dest_idx, "latitude"]
        dest_lon = stops_df.loc[dest_idx, "longitude"]

        # Distance to destination stop in kilometers
        dist_to_dest = haversine(bus_lat, bus_lon, dest_lat, dest_lon)

        nearest_stop_indices.append(nearest_idx)
        dest_stop_indices.append(dest_idx)
        distances_km.append(dist_to_dest)

    gps_df["nearest_stop_index"] = nearest_stop_indices
    gps_df["destination_stop_index"] = dest_stop_indices
    gps_df["distance_to_destination_km"] = distances_km

    # Rename current speed column for clarity
    gps_df.rename(columns={"speed": "current_speed"}, inplace=True)

    # 4. Merge historical data using route_id + time_slot
    historical_renamed = historical_df.rename(
        columns={
            "avg_speed": "historical_avg_speed",
            "avg_delay_minutes": "historical_delay_minutes",
        }
    )

    merged_df = pd.merge(
        gps_df,
        historical_renamed,
        on=["route_id", "time_slot"],
        how="left",
    )

    # 5. Calculate effective speed (average of current and historical speed)
    merged_df["effective_speed"] = (
        merged_df["current_speed"] + merged_df["historical_avg_speed"]
    ) / 2.0

    # 6. Proxy ETA Calculation
    # Travel time (minutes) = (distance_km / effective_speed_kmh) * 60
    # Total ETA (minutes) = travel_time_minutes + historical_delay_minutes
    travel_time_minutes = (
        merged_df["distance_to_destination_km"] / merged_df["effective_speed"]
    ) * 60.0
    merged_df["eta_minutes"] = travel_time_minutes + merged_df["historical_delay_minutes"]

    # 7. Protect against invalid / bad values
    valid_mask = (
        (merged_df["effective_speed"] > 0)
        & (merged_df["distance_to_destination_km"] >= 0)
        & (merged_df["eta_minutes"] >= 0)
        & (~merged_df["eta_minutes"].isna())
        & (~merged_df["distance_to_destination_km"].isna())
        & (~merged_df["effective_speed"].isna())
    )

    final_df = merged_df[valid_mask].copy()
    rows_removed = initial_row_count - len(final_df)

    # Select final dataset columns in specified order
    output_columns = [
        "bus_id",
        "route_id",
        "timestamp",
        "latitude",
        "longitude",
        "current_speed",
        "historical_avg_speed",
        "historical_delay_minutes",
        "time_slot",
        "nearest_stop_index",
        "destination_stop_index",
        "distance_to_destination_km",
        "effective_speed",
        "eta_minutes",
    ]

    final_df = final_df[output_columns]

    # 8. Save output dataset
    final_df.to_csv(output_path, index=False)

    # 9. Print detailed summary
    print("=" * 70)
    print("ETA TRAINING DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Output File: {output_path}")
    print(f"Output Shape: {final_df.shape}")
    print(f"Rows Removed / Invalid: {rows_removed}")
    print("\nColumn Names:")
    print(list(final_df.columns))

    print("\nMissing Values Count:")
    print(final_df.isnull().sum())

    print("\nFirst 10 Rows:")
    print(final_df.head(10).to_string(index=False))

    print("\n" + "=" * 70)
    print("KEY METRICS SUMMARY")
    print("=" * 70)
    print("ETA Minutes:")
    print(f"  Min:    {final_df['eta_minutes'].min():.4f}")
    print(f"  Max:    {final_df['eta_minutes'].max():.4f}")
    print(f"  Mean:   {final_df['eta_minutes'].mean():.4f}")
    print(f"  Median: {final_df['eta_minutes'].median():.4f}")

    print("\nDistance to Destination (km):")
    print(f"  Min:  {final_df['distance_to_destination_km'].min():.4f}")
    print(f"  Max:  {final_df['distance_to_destination_km'].max():.4f}")
    print(f"  Mean: {final_df['distance_to_destination_km'].mean():.4f}")

    print("\nEffective Speed (km/h):")
    print(f"  Min:  {final_df['effective_speed'].min():.4f}")
    print(f"  Max:  {final_df['effective_speed'].max():.4f}")
    print(f"  Mean: {final_df['effective_speed'].mean():.4f}")

    print("\nNumber of Rows per Route:")
    for route_id, count in final_df["route_id"].value_counts().sort_index().items():
        print(f"  Route {route_id}: {count} rows")


if __name__ == "__main__":
    main()
