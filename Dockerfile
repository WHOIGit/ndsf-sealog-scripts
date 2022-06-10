FROM python:3.9

# Uncomment this section to install our CA certificate to the container, and use
#   --build-arg http_proxy=http://199.92.162.241:3128 \
#   --build-arg https_proxy=http://199.92.162.241:3128
#RUN wget -O /usr/local/share/ca-certificates/squid-ca-cert.crt \
#        http://199.92.162.241/squid-ca-cert.crt \
# && update-ca-certificates

# Use the CA bundle mounted from the host, rather than those that come with
# the certifi package.
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Likewise when using the ssl module
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Disable buffering so that output appears in logs immediately
ENV PYTHONUNBUFFERED=1


WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
