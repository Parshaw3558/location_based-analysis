import streamlit as st
import pandas as pd
import os
import altair as alt

st.set_page_config(layout="wide", page_title="Location-based Analysis")

OUTPUT_DIR = "outputs"
SAMPLE_PATH = os.path.join(OUTPUT_DIR, "restaurants_sample.csv")
CITY_STATS_PATH = os.path.join(OUTPUT_DIR, "city_stats.csv")
FOLIUM_PATH = os.path.join(OUTPUT_DIR, "folium_map.html")

st.title(" Location-Analysizer — Restaurants")

# ----------------------------------------------------------
# Load dataset
# ----------------------------------------------------------
if not os.path.exists(SAMPLE_PATH):
    st.error("Run model.py (analysis.py) first to generate outputs in the outputs/ folder.")
    st.stop()

df = pd.read_csv(SAMPLE_PATH)

# ----------------------------------------------------------
# Sidebar Filters
# ----------------------------------------------------------
st.sidebar.header("Filters")

city_col = 'City' if 'City' in df.columns else None
cuisine_col = 'Cuisines' if 'Cuisines' in df.columns else None

# City filter
if city_col:
    cities = sorted(df[city_col].dropna().unique().tolist())
    selected_city = st.sidebar.selectbox("City", ["All"] + cities)
else:
    selected_city = "All"

# Cuisine filter
if cuisine_col:
    cuisines = sorted(df[cuisine_col].dropna().unique().tolist())
    selected_cuisine = st.sidebar.selectbox("Cuisine", ["All"] + cuisines)
else:
    selected_cuisine = "All"

# ----------------------------------------------------------
# Apply Filters
# ----------------------------------------------------------
df_filtered = df.copy()

if selected_city != "All" and city_col:
    df_filtered = df_filtered[df_filtered[city_col] == selected_city]

if selected_cuisine != "All" and cuisine_col:
    df_filtered = df_filtered[df_filtered[cuisine_col] == selected_cuisine]

st.write(f"Showing **{len(df_filtered)} restaurants** after filtering.")

# ----------------------------------------------------------
# Map Visualization
# ----------------------------------------------------------
if 'Latitude' in df_filtered.columns and 'Longitude' in df_filtered.columns:
    st.subheader(" Map View")

    try:
        st.map(
            df_filtered[['Latitude', 'Longitude']].rename(
                columns={'Latitude': 'lat', 'Longitude': 'lon'}
            ),
            zoom=11
        )
    except:
        if os.path.exists(FOLIUM_PATH):
            import streamlit.components.v1 as components
            st.write("Interactive map (folium):")
            with open(FOLIUM_PATH, 'r', encoding='utf-8') as f:
                html = f.read()
            components.html(html, height=600)
        else:
            st.info("No interactive map available.")
else:
    st.info("Dataset missing 'Latitude' or 'Longitude' columns.")

# ----------------------------------------------------------
# Data Table
# ----------------------------------------------------------
with st.expander(" Show Data Table"):
    st.dataframe(df_filtered.reset_index(drop=True), height=300)

# ----------------------------------------------------------
# Insights Section
# ----------------------------------------------------------
st.subheader(" Aggregations & Insights")

# City-level stats
if os.path.exists(CITY_STATS_PATH):
    city_stats = pd.read_csv(CITY_STATS_PATH)
    st.write("### City-wise Summary")
    st.dataframe(city_stats.sort_values("restaurants_count", ascending=False).head(10))
else:
    st.info("City summary not found. Run model.py first.")

# ----------------------------------------------------------
# Top Localities - ERROR FREE VERSION
# ----------------------------------------------------------
if "Locality" in df.columns:
    st.subheader(" Top Localities (Overall)")
    top_loc = df["Locality"].value_counts().head(10).reset_index()
    top_loc.columns = ["Locality", "count"]
    st.bar_chart(top_loc.set_index("Locality")["count"])
else:
    st.error("Locality column missing from dataset.")

# ----------------------------------------------------------
# Rating distribution
# ----------------------------------------------------------
rating_col = None
for col in ["Aggregate rating", "Rating", "Rating text"]:
    if col in df_filtered.columns:
        rating_col = col
        break

if rating_col:
    st.subheader(" Rating Distribution")

    df_filtered["rating_num"] = pd.to_numeric(df_filtered[rating_col], errors="coerce")

    chart = (
        alt.Chart(df_filtered.dropna(subset=["rating_num"]))
        .mark_bar()
        .encode(
            alt.X("rating_num:Q", bin=alt.Bin(maxbins=20)),
            y="count()"
        )
        .properties(height=250)
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Rating column not found.")

# ----------------------------------------------------------
st.markdown("---")
st.write("Run `python model.py` to regenerate outputs if dataset changes.")
