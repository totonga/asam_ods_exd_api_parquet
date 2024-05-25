# ASAM ODS EXD-API pyarrow plugin

This repository contains a [ASAM ODS EXD-API](https://www.asam.net/standards/detail/ods/) plugin that uses [pyarrow](https://arrow.apache.org/docs/python/) to read the [parquet files](https://parquet.apache.org/docs/file-format/) files.

> This is only a prototype to check if it works with [pyarrow](https://arrow.apache.org/docs/python/).

## GRPC stub

Because the repository does not contain the ASAM ODS protobuf files the generated stubs are added.
The files that match `*_pb2*` are generated suing the following command. To renew them you must put the 
proto files from the ODS standard into `proto_src` and rerun the command.

```
python -m grpc_tools.protoc --proto_path=proto_src --pyi_out=. --python_out=. --grpc_python_out=. ods.proto ods_external_data.proto
```

## Content

### `exd_api_server.py`

Runs the GRPC service to be accessed using http-2.

### `external_data_reader.py`

Implements the EXD-API interface to access [parquet files *.parquet](https://parquet.apache.org/docs/file-format/) files using [pyarrow](https://arrow.apache.org/docs/python/).

### `exd_api_test.py`

Some basic tests on example files in `data` folder.

### `example_access_exd_api.ipynb`

jupyter notebook the shows communication done by ASAM ODS server or Importer using the EXD-API plugin.