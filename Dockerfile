FROM python:3.12.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ src/
RUN python -m pip install --no-cache-dir --no-deps .
COPY configs/ configs/
ENTRYPOINT ["beyond-accuracy"]
CMD ["check-config", "--config", "configs/baseline.json"]
