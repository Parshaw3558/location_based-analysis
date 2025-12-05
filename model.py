# model.py
import os
import re
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_PATH = "Dataset.csv"   # <- ensure file is here (in same folder)

def load_dataset(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at {path}")
    return pd.read_csv(path, low_memory=False)

def basic_cleaning(df):
    # strip column names and drop exact duplicate rows
    df.columns = [c.strip() for c in df.columns]
    df = df.drop_duplicates().reset_index(drop=True)
    df = df.replace({"\\N": np.nan, "": np.nan})
    return df

def detect_latlon_cols(df):
    lat_col = None
    lon_col = None
    for c in df.columns:
        lower = c.lower()
        if lower in ("latitude", "lat"):
            lat_col = c
        if lower in ("longitude", "lon", "long"):
            lon_col = c
    return lat_col, lon_col

def coerce_latlon(df, lat_col, lon_col):
    # Coerce both to numeric (if present) and normalize names to 'Latitude'/'Longitude'
    if lat_col:
        df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
        if lat_col != "Latitude":
            df.rename(columns={lat_col: "Latitude"}, inplace=True)
    if lon_col:
        df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
        if lon_col != "Longitude":
            df.rename(columns={lon_col: "Longitude"}, inplace=True)
    return df

def extract_rating_num(series):
    # Accept strings like '3.4', '3.4 /5', 'Rated 4.1', '4', etc.
    s = series.astype(str).fillna("")
    # extract first numeric occurrence (with optional decimal)
    extracted = s.str.extract(r'([0-9]+(?:\.[0-9]+)?)', expand=False)
    return pd.to_numeric(extracted, errors="coerce")

def sample_for_map(df, n=5000, random_state=42):
    # If lat/lon present, take all with coords or sample
    if "Latitude" in df.columns and "Longitude" in df.columns:
        has_coords = df.dropna(subset=["Latitude", "Longitude"])
        if len(has_coords) > n:
            return has_coords.sample(n=n, random_state=random_state).copy()
        return has_coords.copy()
    return df.head(n).copy()

def make_folium_map(df_with_coords, popup_cols=None, lat_col="Latitude", lon_col="Longitude"):
    if df_with_coords.empty:
        return None
    center = [df_with_coords[lat_col].median(), df_with_coords[lon_col].median()]
    m = folium.Map(location=center, zoom_start=12)
    mc = MarkerCluster().add_to(m)
    for _, r in df_with_coords.iterrows():
        lat = r.get(lat_col)
        lon = r.get(lon_col)
        if pd.isna(lat) or pd.isna(lon):
            continue
        popup = ""
        if popup_cols:
            parts = []
            for col in popup_cols:
                if col in r.index:
                    parts.append(f"<b>{col}:</b> {r.get(col, '')}")
            popup = "<br>".join(parts)
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="blue",
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300) if popup else None
        ).add_to(mc)
    return m

def aggregate_by_city(df, city_col="City"):
    if city_col not in df.columns:
        return pd.DataFrame()
    # ensure rating and cost numeric (if present)
    if "Rating" in df.columns:
        df["Rating_num_for_agg"] = pd.to_numeric(df["Rating"], errors="coerce")
    else:
        df["Rating_num_for_agg"] = np.nan
    if "Average Cost for two" in df.columns:
        df["Average Cost for two"] = pd.to_numeric(df["Average Cost for two"], errors="coerce")
    grouped = (
        df.groupby(city_col)
        .agg(
            restaurants_count = ("Restaurant Name", "nunique") if "Restaurant Name" in df.columns else ("Cuisines", "count"),
            avg_rating = ("Rating_num_for_agg", "mean"),
            avg_cost = ("Average Cost for two", "mean")
        )
        .reset_index()
    )
    return grouped

def main():
    print("Loading dataset...")
    df = load_dataset(DATA_PATH)
    print("Initial rows:", len(df))

    df = basic_cleaning(df)

    # detect lat/lon and coerce
    lat_col, lon_col = detect_latlon_cols(df)
    if lat_col and lon_col:
        df = coerce_latlon(df, lat_col, lon_col)
        print("Detected coordinates -> Latitude & Longitude")
    else:
        print("Latitude/Longitude not detected (map will be limited).")

    # normalize Locality if alternate column name present
    if "Locality" not in df.columns and "Locality Verbose" in df.columns:
        df["Locality"] = df["Locality Verbose"]

    # parse rating into numeric column (if rating present)
    rating_candidates = [c for c in df.columns if c.lower() in ("aggregate rating","rating","rating text")]
    if rating_candidates:
        rating_col = rating_candidates[0]
        df["rating_num"] = extract_rating_num(df[rating_col])
        print(f"Parsed ratings from column: {rating_col}")
    else:
        df["rating_num"] = np.nan
        print("No rating column found to parse.")

    # mark coords availability
    df["has_coords"] = df.get("Latitude").notna() & df.get("Longitude").notna() if "Latitude" in df.columns and "Longitude" in df.columns else False

    # Save sample for app
    sample = sample_for_map(df[df["has_coords"]] if df["has_coords"].any() else df)
    sample_path = os.path.join(OUTPUT_DIR, "restaurants_sample.csv")
    # include rating_num in sample to speed-up plotting
    sample.to_csv(sample_path, index=False)
    print("Saved cleaned sample:", sample_path)

    # Aggregation by city
    city_stats = aggregate_by_city(df)
    city_stats_path = os.path.join(OUTPUT_DIR, "city_stats.csv")
    city_stats.to_csv(city_stats_path, index=False)
    print("Saved city stats:", city_stats_path)

    # Build folium map (if coords exist)
    if df["has_coords"].any():
        try:
            popup_cols = [c for c in ("Restaurant Name", "Cuisines", "rating_num", "Average Cost for two", "Locality") if c in df.columns or c == "rating_num"]
            m = make_folium_map(sample, popup_cols=popup_cols)
            if m:
                folium_path = os.path.join(OUTPUT_DIR, "folium_map.html")
                m.save(folium_path)
                print("Saved folium map:", folium_path)
        except Exception as e:
            print("Error building folium map:", e)
    else:
        print("No coordinates available; skipping folium map creation.")

    print("Done. Outputs stored in:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
