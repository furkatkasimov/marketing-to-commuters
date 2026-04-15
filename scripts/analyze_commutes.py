"""
analyze_commutes.py
-------------------
For each commuter pair (home to work), request a driving route from
Google Maps Directions API (or OSRM as a free alternative), then check
whether the route passes within a configured distance of the target
business location.
"""

import time
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, Point
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def get_route_google(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    api_key: str,
) -> Optional[LineString]:
    """
    Call the Google Maps Directions API and return the route as a
    Shapely LineString. Requires a valid API key.
    """
    import polyline as pl

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin_lat},{origin_lon}",
        "destination": f"{dest_lat},{dest_lon}",
        "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] != "OK":
            return None
        overview = data["routes"][0]["overview_polyline"]["points"]
        decoded = pl.decode(overview)  # list of (lat, lon)
        coords = [(lon, lat) for lat, lon in decoded]
        if len(coords) < 2:
            return None
        return LineString(coords)
    except Exception:
        return None


def get_route_osrm(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    osrm_url: str = "http://router.project-osrm.org",
) -> Optional[LineString]:
    """
    Call the OSRM route service (free, no API key needed) and return
    the route as a Shapely LineString. Returns None on failure.
    """
    url = (
        f"{osrm_url}/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=geojson"
    )
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok":
            return None
        coords = data["routes"][0]["geometry"]["coordinates"]
        if len(coords) < 2:
            return None
        return LineString(coords)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def route_passes_near_business(
    route: LineString,
    business_point: Point,
    buffer_meters: float,
) -> bool:
    """
    Check whether a route passes within buffer_meters of a business.
    Projects both geometries to UTM for accurate distance measurement.
    """
    route_gdf = gpd.GeoDataFrame(geometry=[route], crs="EPSG:4326")
    biz_gdf = gpd.GeoDataFrame(geometry=[business_point], crs="EPSG:4326")

    # Pick the right UTM zone based on the business location
    utm_zone = int((business_point.x + 180) / 6) + 1
    hemisphere = "north" if business_point.y >= 0 else "south"
    epsg = 32600 + utm_zone if hemisphere == "north" else 32700 + utm_zone
    crs_proj = f"EPSG:{epsg}"

    route_proj = route_gdf.to_crs(crs_proj)
    biz_proj = biz_gdf.to_crs(crs_proj)

    biz_buffer = biz_proj.geometry.iloc[0].buffer(buffer_meters)
    return route_proj.geometry.iloc[0].intersects(biz_buffer)


def analyze_commuters(
    commuters: pd.DataFrame,
    business_lat: float,
    business_lon: float,
    buffer_meters: float = 8047,
    routing_engine: str = "google",
    osrm_url: str = "http://router.project-osrm.org",
    google_api_key: str = "",
    max_routes: int = 200,
    request_delay: float = 1.0,
) -> gpd.GeoDataFrame:
    """
    For each commuter pair, get a driving route and check whether it
    passes near the target business.

    Parameters
    ----------
    commuters : DataFrame with h_lat, h_lon, w_lat, w_lon, S000, etc.
    business_lat, business_lon : location of the target business.
    buffer_meters : how close the route must pass (default 8047m = 5 miles).
    routing_engine : "google" or "osrm".
    max_routes : cap on how many routes to compute per run.
    request_delay : seconds to wait between API calls.

    Returns
    -------
    GeoDataFrame of commuter pairs whose routes pass near the business,
    with a route_geometry column containing the LineString.
    """
    business_point = Point(business_lon, business_lat)

    # Sort by job count descending - analyze highest-volume pairs first
    df = commuters.sort_values("S000", ascending=False).head(max_routes).copy()

    # Check API key if using Google
    if routing_engine == "google":
        if not google_api_key or google_api_key == "YOUR_GOOGLE_API_KEY_HERE":
            print("[ERROR] Google Maps API key is not set!")
            print("        Edit config.yaml and replace YOUR_GOOGLE_API_KEY_HERE")
            print("        with your actual API key.")
            print("        Or set engine to 'osrm' for free routing (no key needed).")
            return gpd.GeoDataFrame()

    results = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Routing commuters"):
        if routing_engine == "google":
            route = get_route_google(
                row["h_lat"], row["h_lon"],
                row["w_lat"], row["w_lon"],
                google_api_key,
            )
        else:
            route = get_route_osrm(
                row["h_lat"], row["h_lon"],
                row["w_lat"], row["w_lon"],
                osrm_url,
            )

        if route is None:
            continue

        passes = route_passes_near_business(route, business_point, buffer_meters)
        if passes:
            results.append(
                {
                    "h_geocode": row["h_geocode"],
                    "w_geocode": row["w_geocode"],
                    "S000": row["S000"],
                    "h_lat": row["h_lat"],
                    "h_lon": row["h_lon"],
                    "w_lat": row["w_lat"],
                    "w_lon": row["w_lon"],
                    "h_zcta": row.get("h_zcta", ""),
                    "w_zcta": row.get("w_zcta", ""),
                    "route_geometry": route,
                }
            )

        time.sleep(request_delay)

    if not results:
        print("[!] No commute routes pass near the business location.")
        return gpd.GeoDataFrame()

    gdf = gpd.GeoDataFrame(results, geometry="route_geometry", crs="EPSG:4326")
    total_commuters = gdf["S000"].sum()
    print(f"\n[OK] {len(gdf)} commuter pairs ({total_commuters:,} jobs) "
          f"pass within {buffer_meters}m of the business.")
    return gdf


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    commuters = pd.read_csv(
        Path(cfg["output"]["directory"]) / "commuter_pairs.csv",
        dtype={"h_geocode": str, "w_geocode": str, "h_zcta": str, "w_zcta": str},
    )

    biz = cfg["business"]
    routing = cfg["routing"]

    passing = analyze_commuters(
        commuters,
        business_lat=biz["latitude"],
        business_lon=biz["longitude"],
        buffer_meters=biz["buffer_meters"],
        routing_engine=routing["engine"],
        osrm_url=routing.get("osrm_url", ""),
        google_api_key=routing.get("google_api_key", ""),
        max_routes=routing["max_routes"],
        request_delay=routing["request_delay"],
    )

    if not passing.empty:
        out_dir = Path(cfg["output"]["directory"])
        passing.drop(columns=["route_geometry"]).to_csv(
            out_dir / "commuters_passing_business.csv", index=False
        )
        passing.to_file(
            out_dir / "commuters_passing_business.geojson", driver="GeoJSON"
        )
        print(f"[OK] Results saved to {out_dir}/")
