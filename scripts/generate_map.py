"""
generate_map.py
---------------
Create an interactive HTML map showing:
  - The target business location
  - Commute routes that pass near the business
"""

from pathlib import Path

import folium
import geopandas as gpd


def generate_map(
    business_name: str,
    business_lat: float,
    business_lon: float,
    routes_geojson: str = None,
    output_html: str = "output/commuter_map.html",
):
    """Build an interactive HTML map with routes and business location."""

    m = folium.Map(
        location=[business_lat, business_lon],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    # --- Business marker ---
    folium.Marker(
        location=[business_lat, business_lon],
        popup=f"<b>{business_name}</b><br>Target business",
        icon=folium.Icon(color="red", icon="store", prefix="fa"),
    ).add_to(m)

    # --- Commute routes ---
    if routes_geojson and Path(routes_geojson).exists():
        routes = gpd.read_file(routes_geojson)
        route_layer = folium.FeatureGroup(name="Commute Routes")
        for _, row in routes.iterrows():
            coords = [
                (lat, lon)
                for lon, lat in row.geometry.coords
            ]
            folium.PolyLine(
                coords,
                weight=2,
                color="#3388ff",
                opacity=0.6,
                popup=(
                    f"Home ZIP: {row.get('h_zcta', 'N/A')}<br>"
                    f"Work ZIP: {row.get('w_zcta', 'N/A')}<br>"
                    f"Jobs: {row.get('S000', 'N/A')}"
                ),
            ).add_to(route_layer)
        route_layer.add_to(m)
        print(f"[OK] Added {len(routes)} routes to map.")

    folium.LayerControl().add_to(m)

    Path(output_html).parent.mkdir(parents=True, exist_ok=True)
    m.save(output_html)
    print(f"[OK] Interactive map saved to {output_html}")


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    biz = cfg["business"]
    out_dir = cfg["output"]["directory"]

    generate_map(
        business_name=biz["name"],
        business_lat=biz["latitude"],
        business_lon=biz["longitude"],
        routes_geojson=f"{out_dir}/commuters_passing_business.geojson",
        output_html=f"{out_dir}/commuter_map.html",
    )
