# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install wkhtmltopdf and dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    fontconfig \
    libfontconfig1 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up xvfb as a wrapper for wkhtmltopdf (X virtual framebuffer)
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf "$@"' > /usr/bin/wkhtmltopdf.sh && \
    chmod +x /usr/bin/wkhtmltopdf.sh && \
    ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["python", "api.py"]    