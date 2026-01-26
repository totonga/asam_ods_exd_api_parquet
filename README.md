# ASAM ODS EXD-API pyarrow plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Python package](https://github.com/totonga/asam_ods_exd_api_parquet/actions/workflows/python-package.yml/badge.svg)](https://github.com/totonga/asam_ods_exd_api_parquet/actions/workflows/python-package.yml)
[![Docker Image](https://ghcr-badge.egpl.dev/totonga/asam-ods-exd-api-parquet/latest_tag?trim=major&label=latest)](https://github.com/totonga/asam_ods_exd_api_parquet/pkgs/container/asam-ods-exd-api-parquet)

This repository contains a [ASAM ODS EXD-API](https://www.asam.net/standards/detail/ods/) plugin that uses [pyarrow](https://arrow.apache.org/docs/python/) to read the [parquet files](https://parquet.apache.org/docs/file-format/) files. To implement the plugin [ods_exd_api_box](https://github.com/totonga/ods-exd-api-box) is used.

## Content

### `external_data_file.py`

Implements the EXD-API interface to access [parquet files *.parquet](https://parquet.apache.org/docs/file-format/) files using [pyarrow](https://arrow.apache.org/docs/python/).

### `example_access_exd_api.ipynb`

jupyter notebook that shows communication done by ASAM ODS server or Importer using the EXD-API plugin.

### Docker Image Details

The Docker image for this project is available at:

`ghcr.io/totonga/asam-ods-exd-api-parquet:latest`

This image is automatically built and pushed via a GitHub Actions workflow. To pull and run the image:

```
docker pull ghcr.io/totonga/asam-ods-exd-api-parquet:latest
docker run -v /path/to/local/data:/data -p 50051:50051 ghcr.io/totonga/asam-ods-exd-api-parquet:latest
```

### Using the Docker Container

To build the Docker image locally:
```
docker build -t asam-ods-exd-api-parquet .
```

To start the Docker container:
```
docker run -v /path/to/local/data:/data -p 50051:50051 asam-ods-exd-api-parquet
```