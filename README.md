# Marketing to Commuters

Find out which commuters drive past your business every day — using free U.S. Census data and Google Maps.

This tool downloads public data about where people live and work, computes their actual driving routes, and tells you which ones pass near your business. You get a list of ZIP codes, commuter counts, and an interactive map.

Based on the strategy described in *"Marketing to Commuters: A Practical Guide for Local Businesses"* by Furkat Kasimov.

---

## How It Works (3 Steps)

1. Downloads free commuter data from the U.S. Census Bureau (home location + work location for every worker in a state)
2. Computes real driving routes between home and work using Google Maps
3. Checks which routes pass within 5 miles of your business

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/marketing-to-commuters.git
cd marketing-to-commuters
pip install -r requirements.txt
```

Edit `config.yaml` with your business location and Google Maps API key (see instructions below), then:

```bash
python main.py
```

Open `output/commuter_map.html` in a browser to see the results.

---

## How to Set Up Your Google Maps API Key

The Google Maps Directions API calculates driving routes. You get 10,000 free requests per month (more than enough for this tool). Here's how to get a key:

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Sign in with your Google account
3. Click **Select a project** at the top, then **New Project**, name it anything, click **Create**
4. In the left menu, go to **APIs & Services** then **Library**
5. Search for **Directions API**, click it, click **Enable**
6. In the left menu, go to **APIs & Services** then **Credentials**
7. Click **Create Credentials** then **API Key**
8. Copy the key that appears

Now open `config.yaml` and paste your key:

```yaml
routing:
  engine: "google"
  google_api_key: "AIzaSyB1234567890abcdefg"   # <-- paste your key here
```

If you don't want to use Google Maps, change the engine to `osrm` (free, no key needed, but slightly less accurate):

```yaml
routing:
  engine: "osrm"
```

---

## How to Change the Settings

All settings are in one file: **`config.yaml`**. Open it in any text editor.

### Change the state and year

```yaml
lodes:
  state: "va"       # two-letter state code: "va", "dc", "ca", "tx", etc.
  year: 2022         # available years: 2002-2022 for most states
```

### Change your business location

Find your coordinates on Google Maps: right-click any location, and the latitude/longitude appear at the top of the menu.

```yaml
business:
  name: "Joe's Dry Cleaning"
  latitude: 38.9072
  longitude: -77.0369
```

### Change the search radius

The default is 5 miles (8047 meters). To change it:

```yaml
business:
  buffer_meters: 8047    # 5 miles (default)
```

Common values: 1600 (1 mile), 3200 (2 miles), 4828 (3 miles), 8047 (5 miles), 16093 (10 miles).

### Change how many commuters to analyze

```yaml
routing:
  max_routes: 200    # increase for more results, decrease for faster testing
```

Each route uses one Google Maps API call. You get 10,000 free per month.

---

## About the Dataset

This project uses the **LEHD Origin-Destination Employment Statistics (LODES)** dataset from the U.S. Census Bureau.

**What it is:** A free, public dataset that shows how many people commute between every pair of census blocks in each state. A census block is roughly the size of a city block.

**What it contains:** For each home-to-work pair, you get: the number of jobs (workers), broken down by age group, earnings bracket, and industry sector.

**What it does NOT contain:** No individual names, no street addresses, no personal information. It is aggregate count data at the census block level.

**Where to download it:** [lehd.ces.census.gov/data/lodes](https://lehd.ces.census.gov/data/lodes/)

**Citation:**
> U.S. Census Bureau, LEHD Origin-Destination Employment Statistics, Version 8, https://lehd.ces.census.gov/data/lodes

### Using Your Own Dataset

If you have your own data (for example, a customer list with home and work addresses that you purchased from a data broker), you can use it instead of LODES.

Create a CSV file called `output/commuter_pairs.csv` with these columns:

```
h_geocode,w_geocode,S000,h_lat,h_lon,h_zcta,w_lat,w_lon,w_zcta
home_id_1,work_id_1,1,38.90,-77.03,20001,38.88,-77.01,20003
home_id_2,work_id_2,1,38.92,-77.05,20007,38.89,-77.02,20004
```

Column meanings:
- `h_lat`, `h_lon` — home latitude and longitude (REQUIRED)
- `w_lat`, `w_lon` — work latitude and longitude (REQUIRED)
- `S000` — number of people for this pair (set to 1 if one person per row)
- `h_geocode`, `w_geocode` — any ID for the home and work location
- `h_zcta`, `w_zcta` — home and work ZIP codes (optional, for display)

Then run with `--skip-download` to skip the Census data download and use your file directly:

```bash
python main.py --skip-download
```

---

## Output Files

After running, you'll find these files in the `output/` folder:

| File | What it is |
|------|------------|
| `commuter_pairs.csv` | All home-to-work pairs with coordinates |
| `commuters_passing_business.csv` | Only the pairs whose driving route passes near your business |
| `commuters_passing_business.geojson` | Same data with route lines (for mapping software) |
| `commuter_map.html` | Interactive map — open this in a browser |

---

## Project Structure

```
marketing-to-commuters/
    main.py                  # Run this to start the pipeline
    config.yaml              # All your settings (edit this)
    requirements.txt         # Python packages needed
    README.md                # This file
    LICENSE                  # MIT License
    .gitignore               # Keeps large files out of git
    scripts/
        download_lodes.py    # Downloads Census data
        analyze_commutes.py  # Routes commuters and checks proximity
        generate_map.py      # Creates the interactive HTML map
    data/                    # Downloaded Census files (not in git)
    output/                  # Results (not in git)
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

The LODES data is published by the U.S. Census Bureau and is in the public domain.
