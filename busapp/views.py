from django.shortcuts import render
from django.http import JsonResponse
import requests
from geopy.distance import geodesic

# Lista de servidores Overpass (fallback automático)
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter"
]

HEADERS = {"User-Agent": "MeuAppBuscaOnibus/1.0"}

# Página inicial
def index(request):
    return render(request, "index.html")

# Endpoint para buscar a parada mais próxima
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
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": destino, "format": "json", "limit": 1}
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
        except requests.RequestException:
            return JsonResponse({"error": "Erro de rede ao acessar Nominatim"}, status=500)

        if resp.status_code != 200 or not resp.json():
            return JsonResponse({"error": "Destino não encontrado"}, status=404)
        dest_data = resp.json()[0]
        dest_lat = float(dest_data["lat"])
        dest_lng = float(dest_data["lon"])
    else:
        dest_lat, dest_lng = lat, lng  # se não informar destino, usar localização atual

    # --- Buscar paradas de ônibus via Overpass API ---
    query = f"""
    [out:json][timeout:25];
    node["highway"="bus_stop"](around:{raio_m},{dest_lat},{dest_lng});
    out;
    """

    elements = []
    for server in OVERPASS_SERVERS:
        try:
            response = requests.post(server, data={"data": query}, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                elements = response.json().get("elements", [])
                if elements:
                    break  # sucesso, sai do loop
        except requests.RequestException:
            continue  # tenta o próximo servidor

    if not elements:
        return JsonResponse({"error": "Nenhuma parada encontrada ou erro no Overpass"}, status=404)

    # --- Encontrar a parada mais próxima do destino ---
    nearest = min(elements, key=lambda p: geodesic((dest_lat, dest_lng), (p["lat"], p["lon"])).meters)
    distance = geodesic((dest_lat, dest_lng), (nearest["lat"], nearest["lon"])).meters
    name = nearest.get("tags", {}).get("name", "Sem nome")

    return JsonResponse({
        "id": nearest["id"],
        "lat": nearest["lat"],
        "lng": nearest["lon"],
        "name": name,
        "distance_m": distance,
        "dest_lat": dest_lat,
        "dest_lng": dest_lng
    })
