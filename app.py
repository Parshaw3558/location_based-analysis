# app.py
import streamlit as st
import pandas as pd
import os
import altair as alt

st.set_page_config(layout="wide", page_title="Location-based Analysis")

OUTPUT_DIR = "outputs"
SAMPLE_PATH = os.path.join(OUTPUT_DIR, "restaurants_sample.csv")
CITY_STATS_PATH = os.path.join(OUTPUT_DIR, "city_stats.csv")
FOLIUM_PATH = os.path.join(OUTPUT_DIR, "folium_map.html")

st.title("📍 Location-Analyzer — Restaurants")

# ---------------------------
# Load dataset
# ---------------------------
if not os.path.exists(SAMPLE_PATH):
    st.error("Run model.py first to generate outputs in the outputs/ folder.")
    st.stop()

df = pd.read_csv(SAMPLE_PATH)

# ---------------------------
# Sidebar filters
# ---------------------------
st.sidebar.header("Filters")

city_col = "City" if "City" in df.columns else None
cuisine_col = "Cuisines" if "Cuisines" in df.columns else None

# City filter
if city_col:
    cities = sorted(df[city_col].dropna().unique().tolist())
    selected_city = st.sidebar.selectbox("City", ["All"] + cities)
else:
    selected_city = "All"

# Cuisine filter: build a cleaned list from comma-separated cuisine values
if cuisine_col:
    cuisine_list = sorted(
        set(
            c.strip()
            for row in df[cuisine_col].dropna().astype(str)
            for c in row.split(",")
            if c.strip()
        )
    )
    selected_cuisine = st.sidebar.selectbox("Cuisine", ["All"] + cuisine_list)
else:
    selected_cuisine = "All"

# ---------------------------
# Apply filters safely
# ---------------------------
df_filtered = df.copy()

if selected_city != "All" and city_col:
    df_filtered = df_filtered[df_filtered[city_col] == selected_city]

if selected_cuisine != "All" and cuisine_col:
    # match partial cuisine words within the original Cuisines column
    df_filtered = df_filtered[
        df_filtered[cuisine_col].astype(str).str.contains(rf'\b{pd.Series([selected_cuisine])[0]}\b', case=False, na=False)
    ]

st.write(f"Showing **{len(df_filtered)} restaurants** after filtering.")

# ---------------------------
# Map visualization
# ---------------------------
if "Latitude" in df_filtered.columns and "Longitude" in df_filtered.columns and df_filtered[["Latitude", "Longitude"]].dropna().shape[0] > 0:
    st.subheader("🗺 Map View")
    try:
        st.map(
            df_filtered[["Latitude", "Longitude"]].rename(columns={"Latitude": "lat", "Longitude": "lon"}),
            zoom=11
        )
    except Exception:
        if os.path.exists(FOLIUM_PATH):
            import streamlit.components.v1 as components
            st.write("Interactive map (folium):")
            with open(FOLIUM_PATH, "r", encoding="utf-8") as f:
                html = f.read()
            components.html(html, height=600)
        else:
            st.info("No interactive map available.")
else:
    st.info("Dataset missing Latitude/Longitude (or no points after filtering).")

# ---------------------------
# Data table
# ---------------------------
with st.expander("📄 Show Data Table"):
    st.dataframe(df_filtered.reset_index(drop=True), height=300)

# ---------------------------
# Aggregations & Insights
# ---------------------------
st.subheader("📊 Aggregations & Insights")

# City stats
if os.path.exists(CITY_STATS_PATH):
    city_stats = pd.read_csv(CITY_STATS_PATH)
    st.write("### City-wise Summary")
    st.dataframe(city_stats.sort_values("restaurants_count", ascending=False).head(15))
else:
    st.info("City summary not found. Run model.py first.")

# Top localities (overall) - use original df (not filtered) to show overall hotspots
if "Locality" in df.columns:
    st.subheader("🏙 Top Localities (Overall)")
    top_loc = df["Locality"].value_counts().head(10).reset_index()
    top_loc.columns = ["Locality", "Count"]
    st.altair_chart(
        alt.Chart(top_loc)
        .mark_bar()
        .encode(x=alt.X("Locality:N", sort="-y", axis=alt.Axis(labelAngle=-45)), y="Count:Q")
        .properties(height=300),
        use_container_width=True
    )
else:
    st.info("Locality column not found in dataset.")

# ---------------------------
# Rating distribution (uses parsed numeric rating if available)
# ---------------------------
# Try to find a numeric rating column first
if "rating_num" in df_filtered.columns:
    rating_col = "rating_num"
else:
    # fallback: try to find common rating-like columns
    candidates = [c for c in df_filtered.columns if c.lower() in ("aggregate rating", "rating", "rating text")]
    rating_col = candidates[0] if candidates else None

if rating_col:
    st.subheader("⭐ Rating Distribution")
    df_filtered["rating_for_plot"] = pd.to_numeric(df_filtered[rating_col], errors="coerce")
    plot_df = df_filtered.dropna(subset=["rating_for_plot"])
    if plot_df.empty:
        st.info("No numeric rating values available after filtering.")
    else:
        chart = (
            alt.Chart(plot_df)
            .mark_bar()
            .encode(
                alt.X("rating_for_plot:Q", bin=alt.Bin(maxbins=20), title="rating_num (binned)"),
                y="count()"
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)
else:
    st.info("Rating column not found or not parsable.")

st.markdown("---")
st.write("Run `python model.py` to regenerate outputs if dataset changes.")
