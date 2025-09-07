# --- Imagem base ---
FROM python:3.11-slim

# --- Variáveis de ambiente ---
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Instalar dependências do sistema ---
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Diretório de trabalho ---
WORKDIR /app

# --- Copia requirements e instala ---
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Copia o projeto ---
COPY . /app/

# --- Expor porta ---
EXPOSE 8000

# --- Rodar Gunicorn para produção ---
CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]
