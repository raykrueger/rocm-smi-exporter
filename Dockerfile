FROM rocm/rocm-terminal:latest

USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir prometheus_client

COPY main.py .

USER rocm-user
EXPOSE 9393
CMD ["python3", "main.py"]
