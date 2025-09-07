# --- Etapa 1: imagem base ---
FROM python:3.11-slim

# --- Variáveis de ambiente ---
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Atualiza e instala dependências do sistema ---
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Diretório de trabalho ---
WORKDIR /app

# --- Copia arquivos de requirements ---
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Copia todo o projeto ---
COPY . /app/

# --- Expõe porta padrão do Render ---
EXPOSE 8000

# --- Comando para rodar Django com Gunicorn ---
CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
