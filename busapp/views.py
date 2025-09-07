import logging
from django.shortcuts import render
from django.http import JsonResponse
import requests
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter"
]

HEADERS = {"User-Agent": "MeuAppBuscaOnibus/1.0"}

def index(request):
    return render(request, "index.html")

def nearest_stop(request):
    try:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
        destino = request.GET.get("destino", "")
        raio_m = int(request.GET.get("raio", 500))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Parâmetros inválidos"}, status=400)

    # --- Geocodificar destino se informado ---
    if destino:
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": destino, "format": "json", "limit": 1},
                headers=HEADERS,
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return JsonResponse({"error": f"Destino '{destino}' não encontrado"}, status=404)
            dest_data = data[0]
            dest_lat = float(dest_data["lat"])
            dest_lng = float(dest_data["lon"])
        except Exception as e:
            logger.error(f"Erro no Nominatim: {e}")
            return JsonResponse({"error": "Falha ao geocodificar destino"}, status=500)
    else:
        dest_lat, dest_lng = lat, lng

    # --- Buscar paradas no Overpass ---
    query = f"""
    [out:json][timeout:25];
    node["highway"="bus_stop"](around:{raio_m},{dest_lat},{dest_lng});
    out;
    """

    elements = []
    last_error = None
    for server in OVERPASS_SERVERS:
        try:
            r = requests.post(server, data={"data": query}, headers=HEADERS, timeout=30)
            r.raise_for_status()
            elements = r.json().get("elements", [])
            if elements:
                break
        except Exception as e:
            logger.error(f"Erro no servidor {server}: {e}")
            last_error = str(e)
            continue

    if not elements:
        return JsonResponse({"error": f"Erro ao buscar paradas no Overpass: {last_error}"}, status=500)

    # --- Encontrar a parada mais próxima ---
    nearest = min(elements, key=lambda p: geodesic((dest_lat, dest_lng), (p["lat"], p["lon"])).meters)
    name = nearest.get("tags", {}).get("name", "Sem nome")

    return JsonResponse({
        "id": nearest["id"],
        "lat": nearest["lat"],
        "lng": nearest["lon"],
        "name": name,
        "dest_lat": dest_lat,
        "dest_lng": dest_lng
    })
