# Required installs:
# pip install earthengine-api geemap streamlit pandas folium

import ee
import geemap
import streamlit as st
import pandas as pd

# --- Authenticate Earth Engine once separately:
# Uncomment and run this block once outside this app script to authenticate your Google account.
# After successful authentication, comment it out or remove before running the app.
ee.Authenticate()

# Initialize Earth Engine
ee.Initialize()

# Streamlit app UI
st.title("Global Plant Blooming Explorer")
st.markdown("Explore global plant blooming using NASA MODIS NDVI/EVI data.")

# Region selection
region_options = {
    "California": [-124.4, 32.5, -114.1, 42.0],
    "Amazon": [-74.0, -6.0, -54.0, 0.0],
    "Custom": NoneA
}
region_choice = st.selectbox("Select a region:", list(region_options.keys()))
if region_choice == "Custom":
    west = st.number_input("West longitude:", -180.0, 180.0, -120.0)
    south = st.number_input("South latitude:", -90.0, 90.0, 30.0)
    east = st.number_input("East longitude:", -180.0, 180.0, -110.0)
    north = st.number_input("North latitude:", -90.0, 90.0, 40.0)
    bounds = [west, south, east, north]
else:
    bounds = region_options[region_choice]
region_geom = ee.Geometry.BBox(bounds[0], bounds[1], bounds[2], bounds[3])

# Dates and index selection
start_date = st.date_input("Start date", pd.to_datetime("2023-04-01"))
end_date = st.date_input("End date", pd.to_datetime("2023-07-31"))
if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()
index_choice = st.selectbox("Vegetation index:", ["NDVI", "EVI"])

# Get MODIS vegetation index data
collection = (ee.ImageCollection('MODIS/006/MOD13A2')
              .filterDate(str(start_date), str(end_date))
              .filterBounds(region_geom)
              .select(index_choice))

# Bloom detection via rapid positive change in index
def detect_blooming(ic):
    imgs = ic.toList(ic.size())
    size = ic.size().getInfo()
    blooms = []
    for i in range(1, size):
        prev = ee.Image(imgs.get(i-1))
        curr = ee.Image(imgs.get(i))
        diff = curr.select(index_choice).subtract(prev.select(index_choice)).rename('diff')
        mask = diff.gt(400)
        bloom_img = curr.updateMask(mask).set('system:time_start', curr.get('system:time_start'))
        blooms.append(bloom_img)
    return ee.ImageCollection(blooms)

blooming_events = detect_blooming(collection)

# Create interactive map
Map = geemap.Map(center=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2], zoom=6)
Map.addLayer(collection.mean().clip(region_geom),
             {'min': 0, 'max': 9000, 'palette': ['white', 'green']}, f'Mean {index_choice}')
Map.addLayer(blooming_events.mean().clip(region_geom),
             {'min': 0, 'max': 9000, 'palette': ['yellow', 'red']}, 'Blooming Hotspots')
Map.to_streamlit(height=600)

# Timelapse animation button
if st.button("Show Timelapse Animation"):
    out_gif = f"{index_choice}_timelapse.gif"
    geemap.create_timelapse(collection, region_geom, out_gif, bands=[index_choice], fps=4)
    st.image(out_gif, caption=f"{index_choice} Timelapse Animation")

# Educational sidebar
st.sidebar.header("About this App")
st.sidebar.markdown("""
- **NDVI/EVI:** Satellite vegetation indices showing plant greenness and health.
- **Blooming Detection:** Sudden index rises mark leaf-out or bloom.
- **Satellite Data:** NASA MODIS 16-day composites balance detail and revisit frequency.
- **Timelapse:** Shows seasonal vegetation changes and phenology.
- **Phenology:** Climate-driven seasonal plant and animal life cycle events.

[Learn more about Phenology](https://en.wikipedia.org/wiki/Phenology)
""")

# Earth Engine authentication command - run once separately outside this script
# Uncomment the below line and run separately to authenticate:

