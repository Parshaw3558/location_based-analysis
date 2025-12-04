import os
import pandas as pd
import numpy as np

from math import isnan
import folium
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_PATH = "Dataset.csv"   # <- ensure file is here

def _ensure_columns(df, want):
    missing = [c for c in want if c not in df.columns]
    return missing

def load_dataset(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at {path}")
    df = pd.read_csv(path, low_memory=False)
    return df

def basic_cleaning(df):
    # lowercase column names stripped
    df.columns = [c.strip() for c in df.columns]
    df = df.drop_duplicates().reset_index(drop=True)
    # Replace obvious null-like strings
    df = df.replace({"\\N": np.nan, "": np.nan})
    return df

def coerce_latlon(df, lat_col, lon_col):
    # Try to coerce lat/lon to numeric
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    return df

def sample_for_map(df, n=3000, random_state=42):
    # keep rows with lat/lon first, else sample rows without lat/lon
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        has_coords = df.dropna(subset=['Latitude','Longitude'])
        if len(has_coords) > n:
            return has_coords.sample(n=n, random_state=random_state)
        return has_coords.copy()
    # fallback: return top n rows
    return df.head(n).copy()

def make_folium_map(df_with_coords, lat_col='Latitude', lon_col='Longitude', popup_cols=None):
    # Choose center
    if df_with_coords.empty:
        raise ValueError("No coordinates available to build map.")
    center = [df_with_coords[lat_col].median(), df_with_coords[lon_col].median()]
    m = folium.Map(location=center, zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)
    for _, r in df_with_coords.iterrows():
        lat = r.get(lat_col); lon = r.get(lon_col)
        if pd.isna(lat) or pd.isna(lon):
            continue
        popup = ""
        if popup_cols:
            popup = "<br>".join([f"<b>{col}:</b> {r.get(col, '')}" for col in popup_cols if col in r.index])
        folium.CircleMarker(location=[lat, lon],
                            radius=4,
                            color="blue",
                            fill=True,
                            fill_opacity=0.7,
                            popup=folium.Popup(popup, max_width=300)).add_to(marker_cluster)
    return m

def aggregate_by_city(df, city_col='City'):
    if city_col not in df.columns:
        return pd.DataFrame()
    g = df.groupby(city_col)
    out = g.agg(
        restaurants_count = ('Restaurant Name', 'nunique') if 'Restaurant Name' in df.columns else ('Cuisines','count'),
        avg_rating = ('Rating', lambda s: pd.to_numeric(s, errors='coerce').mean()) if 'Rating' in df.columns else ('Cuisines','count'),
        avg_cost = ('Average Cost for two', lambda s: pd.to_numeric(s, errors='coerce').mean()) if 'Average Cost for two' in df.columns else ('Cuisines','count'),
    ).reset_index()
    return out

def main():
    print("Loading dataset...")
    df = load_dataset(DATA_PATH)
    print("Initial rows:", len(df))

    print("Cleaning dataset...")
    df = basic_cleaning(df)

    # Check for common columns — we will attempt to adapt to available columns
    possible_lat = [c for c in df.columns if c.lower() in ('latitude','lat')]
    possible_lon = [c for c in df.columns if c.lower() in ('longitude','lon','long')]
    lat_col = possible_lat[0] if possible_lat else None
    lon_col = possible_lon[0] if possible_lon else None

    required_example = ["Cuisines", "Restaurant Name", "City"]
    missing_req = _ensure_columns(df, [c for c in required_example if c in df.columns])
    # (We won't raise — we only warn; code continues if some are missing)
    print("Columns available:", ", ".join(df.columns[:20]))
    if not lat_col or not lon_col:
        print("⚠️ Warning: Latitude/Longitude columns not detected. Map and spatial plots will be limited.")
    else:
        print(f"Using lat/lon columns: {lat_col}, {lon_col}")
        df = coerce_latlon(df, lat_col, lon_col)

    # Create a normalized Locality column if exists
    if 'Locality' not in df.columns and 'Locality Verbose' in df.columns:
        df['Locality'] = df['Locality Verbose']

    # create a simple coordinate availability flag
    if lat_col and lon_col:
        df['has_coords'] = df[lat_col].notna() & df[lon_col].notna()
    else:
        df['has_coords'] = False

    # Save a cleaned sample for the app
    sample = sample_for_map(df[df['has_coords']]) if df['has_coords'].any() else df.head(2000)
    sample_path = os.path.join(OUTPUT_DIR, "restaurants_sample.csv")
    sample.to_csv(sample_path, index=False)
    print("Saved cleaned sample:", sample_path)

    # Aggregate by city
    city_col = 'City' if 'City' in df.columns else None
    if city_col:
        print("Aggregating by city...")
        city_stats = aggregate_by_city(df, city_col=city_col)
        city_stats_path = os.path.join(OUTPUT_DIR, "city_stats.csv")
        city_stats.to_csv(city_stats_path, index=False)
        print("City stats saved:", city_stats_path)
    else:
        print("City column not present; skipping city aggregation.")

    # Build folium map and save as HTML if coordinates exist
    if df['has_coords'].any():
        print("Building interactive folium map (may take a while for many points)...")
        try:
            popup_cols = []
            for c in ("Restaurant Name", "Cuisines", "Rating", "Average Cost for two", "Locality"):
                if c in df.columns:
                    popup_cols.append(c)
            m = make_folium_map(sample, lat_col=lat_col, lon_col=lon_col, popup_cols=popup_cols)
            folium_path = os.path.join(OUTPUT_DIR, "folium_map.html")
            m.save(folium_path)
            print("Saved folium map to:", folium_path)
        except Exception as e:
            print("Error building folium map:", str(e))
    else:
        print("No coordinates available; skipping folium map creation.")

    print("Done. Outputs stored in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
