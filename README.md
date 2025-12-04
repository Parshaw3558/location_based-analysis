

📍 Location-Based Restaurant Analysis
Interactive Streamlit Dashboard + Data Processing Pipeline
This project provides a complete Location-Based Restaurant Analysis System built using Python, Streamlit, Folium, Altair, and Pandas.
It helps visualize restaurants on a map, explore city-wise insights, filter cuisine/city data, and generate summary statistics.

🚀 Features
✔ Data Processing (model.py)
Cleans and preprocesses raw dataset (Dataset.csv)

Detects and converts latitude/longitude columns

Generates:

restaurants_sample.csv → Sampled, cleaned dataset for app

city_stats.csv → City-wise aggregates

folium_map.html → Interactive map with markers

Handles missing columns and auto-detects common column names

✔ Streamlit Web App (app.py)
City & Cuisine Sidebar Filters

Interactive Map (Streamlit Map + Folium fallback)

Data Table Viewer

Aggregated Insights:

City-wise restaurant count

Average rating

Cost for two

Rating Distribution (Altair Histogram)

Top 10 Localities Bar Chart

📂 Project Structure

📁 project/
│── app.py                 
│── model.py               
│── Dataset.csv            
│── reqire.txt             
│── outputs/               
│     ├── restaurants_sample.csv
│     ├── city_stats.csv
│     ├── folium_map.html

🛠️ Installation
1️⃣ Clone the repository
git clone https://github.com/Parshaw3558/location_based_analysis.git
cd C:\Users\parsh\OneDrive\location_based analysis
2️⃣ Create & activate virtual environment
python -m venv venv
venv\Scripts\activate     # Windows

3️⃣ Install dependencies
pip install -r reqire.txt

🔄 Generate Outputs
Before running the Streamlit app, generate cleaned data & map:

python model.py
This will create the outputs/ folder with:

restaurants_sample.csv

city_stats.csv

folium_map.html

▶ Run the Streamlit App
streamlit run app.py
Then open the local URL (usually):
https://locationbased-analysis-76hsr7zwoh4oitegj5xwrj.streamlit.app/

📊 Visualizations Included
🔹 Restaurant Map
Points plotted by latitude/longitude

Marker clustering for high-density areas

Folium map saved as HTML

🔹 Rating Histogram
Distribution of numeric ratings

🔹 Top Localities
Bar chart showing highest number of restaurants

🔹 City Summary Table
Total restaurants

Average rating

Average cost for two

📁 Required Columns 
Your dataset should contain some of the following columns:

Latitude

Longitude

City

Restaurant Name

Cuisines

Rating

Average Cost for two

Locality or Locality Verbose

Missing columns will be handled gracefully.

🧩 Tech Stack
Python 3.9+

Streamlit

Pandas

Altair

Folium + MarkerCluster

Matplotlib

📝 Future Enhancements
Add clustering of cuisines

Build recommendation system

AI-based popularity prediction

Add user-upload dataset feature

🤝 Contributions
Feel free to fork the repo and submit PRs.

📬 Contact
Developer: Parshaw Patil

