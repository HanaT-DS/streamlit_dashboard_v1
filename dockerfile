FROM python:3.12-slim

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le projet
COPY . .

# Port Streamlit
EXPOSE 8501

# Commande démarrage
CMD ["streamlit", "run", "test1.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]