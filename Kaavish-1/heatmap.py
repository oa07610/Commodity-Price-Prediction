import pandas as pd
import folium
from folium.plugins import HeatMap
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from branca.colormap import LinearColormap

def create_heatmap_from_csv(csv_file, output_file):
    # Load the data
    data = pd.read_csv(csv_file)

    # Check for required columns
    required_columns = ["province", "district", "price"]
    for column in required_columns:
        if column not in data.columns:
            raise ValueError(f"Missing required column: {column}")

    # Add latitude and longitude if not present
    if "latitude" not in data.columns or "longitude" not in data.columns:
        geolocator = Nominatim(user_agent="geoapiExercises")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        def get_coordinates(row):
            location = geocode(f"{row['district']}, {row['province']}, Pakistan")
            if location:
                return pd.Series([location.latitude, location.longitude])
            else:
                return pd.Series([None, None])

        data[["latitude", "longitude"]] = data.apply(get_coordinates, axis=1)

    # Ensure latitude, longitude, and price are numeric
    data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
    data['price'] = pd.to_numeric(data['price'], errors='coerce')

    # Drop rows with missing or invalid data
    data.dropna(subset=['latitude', 'longitude', 'price'], inplace=True)

    # Prepare heatmap data
    heat_data = data[['latitude', 'longitude', 'price']].values.tolist()

    # Initialize the map
    m = folium.Map(location=[30.3753, 69.3451], zoom_start=6)

    # Define the color scale for the legend
    min_price, max_price = data['price'].min(), data['price'].max()
    colormap = LinearColormap(colors=['blue', 'lime', 'red'], vmin=min_price, vmax=max_price)
    colormap.caption = "Wheat Price (PKR)"

    # Add heatmap
    HeatMap(data=heat_data, radius=15, min_opacity=0.5, max_zoom=13).add_to(m)

    # Add the color scale (legend) to the map
    colormap.add_to(m)

    # Save the map to an HTML file
    m.save(output_file)
    print(f"Heatmap saved to {output_file}")

# Example usage
create_heatmap_from_csv('wheat_updated_data_with_coordinates.csv', 'sugar_price_heatmap_with_legend.html')
