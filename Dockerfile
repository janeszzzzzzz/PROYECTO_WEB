FROM python:3.12-slim

# Evitar preguntas interactivas
ENV DEBIAN_FRONTEND=noninteractive

# Dependencias del sistema (ssh + ansible)
RUN apt-get update && apt-get install -y \
    ssh \
    sshpass \
    git \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el proyecto
COPY . .

# Puerto Flask
EXPOSE 5000

# Comando de arranque
CMD ["python", "app.py"]
