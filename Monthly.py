from bokeh.plotting import figure, curdoc
from bokeh.models import (
    ColumnDataSource,
    Slider,
    HoverTool,
    LinearColorMapper,
    WMTSTileSource,
    Button,
)
from bokeh.layouts import column
import pandas as pd
import h3
import geopandas as gpd
from shapely.geometry import Polygon

# Load your crime data for all months into a DataFrame
crime_data = pd.read_csv(
    "Map/Violence_Sexual_Offences_Cleaned.csv",
    on_bad_lines="skip",
)
crime_data["Month"] = pd.to_datetime(crime_data["Month"])

# Initialize ColumnDataSource for the hexagon patches on the map
hexagons_source = ColumnDataSource({"xs": [], "ys": [], "crime_count": []})

# Configure the Bokeh plot with specific initial range for x and y axes
plot = figure(
    title="Crime Data Visualization in London (Violence and Sexual offences)",
    x_axis_type="mercator",
    y_axis_type="mercator",
    width=1000,
    height=800,
)

# Use the CartoDB Positron tile for a light-themed map
plot.add_tile(
    WMTSTileSource(
        url="https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{Z}/{X}/{Y}.png"
    )
)

# Add the HoverTool to the plot for labels to appear on hover
hover = HoverTool()
hover.tooltips = [("Crime Count", "@crime_count")]
plot.add_tools(hover)


# Function to update the data source with the monthly data
def update_data(month):
    monthly_data = crime_data[crime_data["Month"].dt.month == month].copy()
    monthly_data["h3_index"] = monthly_data.apply(
        lambda row: h3.geo_to_h3(row["Latitude"], row["Longitude"], 8), axis=1
    )
    crime_counts_by_hex = (
        monthly_data.groupby("h3_index").size().reset_index(name="count")
    )
    crime_counts_by_hex["geometry"] = crime_counts_by_hex["h3_index"].apply(
        lambda index: Polygon(h3.h3_to_geo_boundary(index, geo_json=True))
    )
    hexagons_gdf = gpd.GeoDataFrame(crime_counts_by_hex, geometry="geometry")
    hexagons_gdf.set_crs(epsg=4326, inplace=True)
    hexagons_gdf = hexagons_gdf.to_crs(epsg=3857)

    # Your extracted color palette
    extracted_colors = ["#6bb5c5", "#3f86b1", "#489cc0", "#2179b2"]

    # Create a LinearColorMapper with the extracted color palette
    color_mapper = LinearColorMapper(
        palette=extracted_colors,
        low=crime_counts_by_hex["count"].min(),
        high=crime_counts_by_hex["count"].max(),
    )

    hexagons_source.data = {
        "xs": [
            list(polygon.exterior.coords.xy[0]) for polygon in hexagons_gdf.geometry
        ],
        "ys": [
            list(polygon.exterior.coords.xy[1]) for polygon in hexagons_gdf.geometry
        ],
        "crime_count": crime_counts_by_hex["count"],
    }

    # Update the plot patches with the new color mapper each time the data is updated
    plot.patches(
        "xs",
        "ys",
        source=hexagons_source,
        fill_color={"field": "crime_count", "transform": color_mapper},
        line_color="black",
        line_width=1,
    )


# Function to toggle pause state
def toggle_pause():
    global pause
    pause = not pause


# Create a button to pause automatic updates
pause_button = Button(label="Pause", button_type="success")
pause_button.on_click(toggle_pause)

# Slider to select the month
slider = Slider(title="Select Month", start=1, end=12, step=1, value=1)
slider.on_change("value", lambda attr, old, new: update_data(new))

# Initialize the plot with data for the first month
update_data(1)


# Function to automatically update the slider
def auto_update():
    global pause
    if not pause:
        current_month = slider.value + 1
        if current_month > 12:
            current_month = 1
        slider.value = current_month


# Arrange the button, slider, and plot in a column layout
layout = column(pause_button, slider, plot)

# Add the layout to the current document
curdoc().add_root(layout)

# Schedule the auto_update function to run every 2000 milliseconds (2 seconds)
curdoc().add_periodic_callback(auto_update, 5000)
