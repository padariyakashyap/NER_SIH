from pathlib import Path
import pandas as pd

# Define paths relative to this script file using pathlib
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

gps_path = DATA_DIR / "bus_gps_data.csv"
historical_path = DATA_DIR / "historical_data.csv"
route_path = DATA_DIR / "route_data.csv"

# 1. Load CSV files using pandas
gps_df = pd.read_csv(gps_path)
historical_df = pd.read_csv(historical_path)
route_df = pd.read_csv(route_path)

datasets = [
    ("bus_gps_data.csv", gps_df),
    ("historical_data.csv", historical_df),
    ("route_data.csv", route_df),
]

# 2. Print shape, columns, data types, missing-value counts, first 5 rows for each file
for name, df in datasets:
    print("=" * 60)
    print(f"FILE: {name}")
    print("=" * 60)
    print(f"Shape: {df.shape}")
    print("\nColumns:")
    print(list(df.columns))
    print("\nData Types:")
    print(df.dtypes)
    print("\nMissing Values:")
    print(df.isnull().sum())
    print("\nFirst 5 Rows:")
    print(df.head())
    print("\n")

# 3. Print useful dataset statistics
print("=" * 60)
print("DATASET STATISTICS")
print("=" * 60)

# Unique buses and routes across dataset
all_routes = set(gps_df['route_id']).union(set(historical_df['route_id'])).union(set(route_df['route_id']))
print(f"Number of unique buses (in GPS data): {gps_df['bus_id'].nunique()}")
print(f"Number of unique routes (overall): {len(all_routes)}")
print(f"  - Unique routes in GPS data: {gps_df['route_id'].nunique()}")
print(f"  - Unique routes in Historical data: {historical_df['route_id'].nunique()}")
print(f"  - Unique routes in Route data: {route_df['route_id'].nunique()}")

# GPS statistics
gps_timestamps = pd.to_datetime(gps_df['timestamp'])
print(f"\nGPS Timestamp Range: {gps_timestamps.min()} to {gps_timestamps.max()}")
print(f"GPS Speed Min: {gps_df['speed'].min()}")
print(f"GPS Speed Max: {gps_df['speed'].max()}")
print(f"GPS Speed Mean: {gps_df['speed'].mean():.2f}")

# Historical statistics
time_slots = [int(x) for x in sorted(historical_df['time_slot'].unique())]
print(f"\nHistorical Time Slots ({len(time_slots)} unique): {time_slots}")
print(f"Historical Avg Speed Min: {historical_df['avg_speed'].min()}")
print(f"Historical Avg Speed Max: {historical_df['avg_speed'].max()}")
print(f"Historical Avg Speed Mean: {historical_df['avg_speed'].mean():.2f}")

print(f"Historical Delay Min (minutes): {historical_df['avg_delay_minutes'].min():.2f}")
print(f"Historical Delay Max (minutes): {historical_df['avg_delay_minutes'].max():.2f}")
print(f"Historical Delay Mean (minutes): {historical_df['avg_delay_minutes'].mean():.2f}")

# Number of stops per route
stops_per_route = route_df.groupby('route_id')['stop_name'].nunique()
print("\nNumber of stops per route:")
for route_id, count in stops_per_route.items():
    print(f"  Route {route_id}: {count} stops")
