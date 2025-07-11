#!/usr/bin/env sh

# update packages
apt-get update

apt --ys install tzdata

# certificate authorities for openssl?
# see https://serverfault.com/questions/639837/openssl-s-client-shows-alert-certificate-unknown-but-all-server-certificates-app
apt --yes install ca-certificates

# certbot new way to generate ssl keys?
apt --yes install certbot

# graphviz for generating mind/plot maps
apt --yes install graphviz

# popper tools for pdf to create images of cover page via pdf2image
apt --yes install poppler-utils

# imagemagick for image manipulation utility functionality
apt --yes install libjpeg-dev libpng-dev libtiff-dev
apt-get update
apt --yes install imagemagick
