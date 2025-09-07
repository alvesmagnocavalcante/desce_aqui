from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
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

    # --- Geocodificação usando LocationIQ ---
    if destino:
        url = "https://us1.locationiq.com/v1/search.php"
        params = {
            "key": settings.LOCATIONIQ_API_KEY,
            "q": destino,
            "format": "json",
            "limit": 1
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return JsonResponse({"error": "Destino não encontrado"}, status=404)
            dest_lat = float(data[0]["lat"])
            dest_lng = float(data[0]["lon"])
        except requests.RequestException as e:
            return JsonResponse({"error": f"Erro no LocationIQ: {str(e)}"}, status=500)
    else:
        dest_lat, dest_lng = lat, lng  # se não informar destino, usar localização atual

    # --- Buscar paradas de ônibus via Overpass API ---
    query = f"""
    [out:json][timeout:25];
    node["highway"="bus_stop"](around:{raio_m},{dest_lat},{dest_lng});
    out;
    """
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        return JsonResponse({"error": f"Erro ao buscar paradas: {str(e)}"}, status=500)

    elements = response.json().get("elements", [])
    if not elements:
        return JsonResponse({"error": "Nenhuma parada encontrada"}, status=404)

    # --- Encontrar a parada mais próxima do destino ---
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
