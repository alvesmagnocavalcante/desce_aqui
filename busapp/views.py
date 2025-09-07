from django.shortcuts import render
from django.http import JsonResponse
import requests
from geopy.distance import geodesic

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
        headers = {"User-Agent": "MeuAppBuscaOnibus/1.0"}
        resp = requests.get(url, params=params, headers=headers)
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
    response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query})
    if response.status_code != 200:
        return JsonResponse({"error": "Erro ao buscar paradas"}, status=500)

    elements = response.json().get("elements", [])
    if not elements:
        return JsonResponse({"error": "Nenhuma parada encontrada"}, status=404)

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
