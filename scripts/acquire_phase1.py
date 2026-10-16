"""Download auditable Phase 1 inputs. Existing cache is reused, not silently refreshed."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

import httpx
import ssl
import truststore

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.clock import LiveClock

RAW = ROOT / "data/raw"
RAW.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "LakhimpurFloodResearch/0.1 (local educational prototype)", "Accept": "*/*"}


def fetch(name, url, *, params=None, data=None, license_note="See provider terms", timeout=120):
    path = RAW / name
    metadata = RAW / (name + ".metadata.json")
    if path.exists() and metadata.exists():
        expected = json.loads(metadata.read_text(encoding="utf-8"))["sha256"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Cache checksum mismatch for {name}; archive damaged file before reacquiring")
        print(f"CACHED {name}", flush=True)
        return path
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=HEADERS,
                      verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)) as client:
        response = client.post(url, data=data) if data is not None else client.get(url, params=params)
        response.raise_for_status()
        content = response.content
        if not content:
            raise ValueError(f"Empty response for {name}")
        if name.endswith(".json"):
            parsed = response.json()
            if isinstance(parsed, dict) and parsed.get("remark"):
                raise ValueError(f"Incomplete Overpass response: {parsed['remark']}")
        if name.endswith(".pdf") and not content.startswith(b"%PDF"):
            raise ValueError(f"Not a PDF: {name}")
        path.write_bytes(content)
        metadata.write_text(json.dumps({"file": name, "url": str(response.url), "request_body": data,
            "retrieved_at": LiveClock().now().isoformat(), "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content), "content_type": response.headers.get("content-type"),
            "license_note": license_note}, indent=2), encoding="utf-8")
    print(f"SAVED {name}: {len(content):,} bytes", flush=True)
    return path


def boundary():
    return fetch("district_search.json", "https://nominatim.openstreetmap.org/search", params={
        "q": "Lakhimpur district, Assam, India", "format": "jsonv2", "polygon_geojson": 1,
        "addressdetails": 1, "limit": 5}, license_note="OpenStreetMap ODbL 1.0; attribution required")


def osm():
    # Regional extraction is intentionally wider than the eventual bounded graph.
    bbox = "27.00,93.85,27.42,94.35"
    query = f'''[out:json][timeout:180];(
      way["highway"]["area"!="yes"]["highway"!~"footway|path|steps|cycleway|construction|proposed|pedestrian"]({bbox});
      nwr["place"~"city|town|village|hamlet"]({bbox});
      nwr["amenity"~"school|college|community_centre|shelter"]({bbox});
      way["waterway"~"river|stream|canal"]({bbox});
    );out body;>;out skel qt;'''
    errors = []
    for server in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"):
        try:
            return fetch("osm_region.json", server, params={"data": query}, timeout=240,
                         license_note="OpenStreetMap ODbL 1.0; © OpenStreetMap contributors")
        except Exception as error:
            errors.append(f"{server}: {type(error).__name__}: {error}")
    raise RuntimeError("; ".join(errors))


def official():
    fetch("lakhimpur_ddmp_2025.pdf", "https://asdma.assam.gov.in/sites/default/files/swf_utility_folder/departments/asdma_revenue_uneecopscloud_com_oid_70/menu/document/lakhimpur_2025_26.pdf",
          license_note="Government of Assam/DDMA published document; cite source, redistribution terms not independently verified")
    fetch("district_profile.html", "https://lakhimpur.assam.gov.in/about-us/district-profile")


def weather():
    fetch("weather_live.json", "https://api.open-meteo.com/v1/forecast", params={
        "latitude": 27.23, "longitude": 94.10, "hourly": "precipitation,rain,temperature_2m",
        "past_days": 7, "forecast_days": 3, "timezone": "UTC", "models": "gfs_seamless"},
        license_note="Open-Meteo weather data CC BY 4.0; noncommercial API terms; model output, not station measurement")
    fetch("weather_historical_2024.json", "https://archive-api.open-meteo.com/v1/archive", params={
        "latitude": 27.23, "longitude": 94.10, "start_date": "2024-06-25", "end_date": "2024-07-05",
        "hourly": "precipitation,rain,temperature_2m", "models": "era5", "timezone": "UTC"},
        license_note="Open-Meteo CC BY 4.0 / ERA5 reanalysis; NOT an as-issued historical forecast")


def imd():
    errors = []
    for url in ("https://api.imd.gov.in/api/v1/districtrainfall", "https://mausam.imd.gov.in/api/districtwise_rainfall_api.php"):
        try:
            return fetch("imd_district_rainfall.json", url, timeout=60)
        except Exception as error:
            errors.append(str(error))
    raise RuntimeError("; ".join(errors))


def terrain():
    for lon in (93, 94):
        tile = f"Copernicus_DSM_COG_30_N27_00_E0{lon}_00_DEM"
        fetch(f"dem_n27_e{lon}.tif", f"https://copernicus-dem-90m.s3.amazonaws.com/{tile}/{tile}.tif",
              license_note="Copernicus DEM GLO-90 2021; free public Copernicus DEM license; DSM includes surface objects")


def pbf():
    fetch("north-eastern-zone.osm.pbf", "https://download.geofabrik.de/asia/india/north-eastern-zone-261009.osm.pbf",
          timeout=300, license_note="OpenStreetMap ODbL 1.0, extract by Geofabrik dated 2026-10-09")


def district_map():
    fetch("official_district_map.jpg", "https://lakhimpur.assam.gov.in/sites/default/files/styles/large/public/public_utility/LAKHIMPUR-Administrative_Map.jpg.jpeg")


def historical():
    errors = []
    for host in ("www.asdma.gov.in", "asdma.gov.in"):
        try:
            return fetch("flood_report_2024_07_02.pdf", f"https://{host}/pdf/flood_report/2024/Daily_Flood_Report_02.07.2024.pdf")
        except Exception as error:
            errors.append(str(error))
    raise RuntimeError("; ".join(errors))


def memorandum():
    fetch("assam_flood_memorandum_2024.pdf", "https://asdma.assam.gov.in/sites/default/files/swf_utility_folder/departments/asdma_revenue_uneecopscloud_com_oid_70/menu/document/assam_flood_memorandum_2024_.pdf",
          license_note="Government of Assam flood memorandum 2024; published historical evidence, not road-level labels")


def geonames():
    fetch("geonames_IN.zip", "https://download.geonames.org/export/dump/IN.zip", timeout=240,
          license_note="GeoNames CC BY 4.0; populated-place gazetteer; accuracy not warranted")


def nwic_boundary():
    fetch("district_nwic_geojson.zip", "https://nwdp.nwic.gov.in/dataset/6c1af675-1dec-4927-882c-c1ba9d73f76b/resource/8d9aa2e9-9806-4f26-a4ac-48ba21e9b96d/download/district_nwic_geojson.zip",
          timeout=300, license_note="NWIC public District Boundary dataset; resource license Other (Open), updated May 2025; cite NWIC")


def weather_study():
    places = json.loads((ROOT / "data/processed/settlements.geojson").read_text(encoding="utf-8"))["features"]
    params = {"latitude": ",".join(str(f["geometry"]["coordinates"][1]) for f in places),
              "longitude": ",".join(str(f["geometry"]["coordinates"][0]) for f in places),
              "hourly": "precipitation,rain,temperature_2m", "timezone": "UTC", "models": "gfs_seamless",
              "past_days": 7, "forecast_days": 3}
    fetch("weather_settlements_live.json", "https://api.open-meteo.com/v1/forecast", params=params,
          license_note="Open-Meteo CC BY 4.0, GFS seamless numerical model; grid locations may repeat")
    params.pop("past_days")
    params.pop("forecast_days")
    params.update(models="era5", start_date="2024-06-25", end_date="2024-07-05")
    fetch("weather_settlements_historical.json", "https://archive-api.open-meteo.com/v1/archive", params=params,
          license_note="Open-Meteo CC BY 4.0 / ERA5; historical reanalysis, not as-issued forecasts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tasks", nargs="*", default=["boundary", "pbf", "official", "district_map", "weather", "terrain", "memorandum", "geonames", "nwic_boundary"])
    args = parser.parse_args()
    tasks = {name: globals()[name] for name in args.tasks}
    failure_path = RAW / "acquisition_failures.json"
    failures = json.loads(failure_path.read_text(encoding="utf-8")) if failure_path.exists() else {}
    run_failed = False
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {name: pool.submit(task) for name, task in tasks.items()}
        for name, future in futures.items():
            try:
                future.result()
                failures.pop(name, None)
            except Exception as error:
                failures[name] = f"{type(error).__name__}: {error}"
                run_failed = True
                print(f"FAILED {name}: {failures[name]}", flush=True)
    (RAW / "acquisition_failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
    sys.exit(run_failed)
