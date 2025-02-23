"""EXD API implementation for parquet files"""

import os
import re
import threading
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import grpc
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import ods_external_data_pb2 as exd_api
import ods_external_data_pb2_grpc
import ods_pb2 as ods

# pylint: disable=E1101


class ExternalDataReader(ods_external_data_pb2_grpc.ExternalDataReader):

    def Open(self, request, context):
        file_path = Path(self.__get_path(request.url))
        if not file_path.is_file():
            raise Exception(f'file "{request.url}" not accessible')

        connection_id = self.__open_file(request)

        rv = exd_api.Handle(uuid=connection_id)
        return rv

    def Close(self, request, context):
        self.__close_file(request)
        return exd_api.Empty()

    def GetStructure(self, request, context):

        if request.suppress_channels or request.suppress_attributes or 0 != len(request.channel_names):
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details("Method not implemented!")
            raise NotImplementedError("Method not implemented!")

        identifier = self.connection_map[request.handle.uuid]
        table = self.__get_file(request.handle)

        rv = exd_api.StructureResult(identifier=identifier)
        rv.name = Path(identifier.url).name
        new_group = exd_api.StructureResult.Group()
        new_group.name = "data"
        new_group.id = 0
        new_group.total_number_of_channels = table.num_columns
        new_group.number_of_rows = table.num_rows
        for channel_index, channel_name in enumerate(table.schema.names):
            channel_type = table.schema.types[channel_index]
            new_channel = exd_api.StructureResult.Channel()
            new_channel.name = channel_name
            new_channel.id = channel_index
            new_channel.data_type = self.__get_datatype(channel_type)
            new_channel.unit_string = ""
            new_group.channels.append(new_channel)
        rv.groups.append(new_group)
        return rv

    def GetValues(self, request, context):

        table = self.__get_file(request.handle)
        group_id = request.group_id
        if group_id < 0 or group_id >= 1:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid group id {request.group_id}!")
            raise NotImplementedError(f"Invalid group id {request.group_id}!")

        nr_of_rows = table.num_rows
        if request.start >= nr_of_rows:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                f"Channel start index {request.start} out of range!")
            raise NotImplementedError(
                f"Channel start index {request.start} out of range!")

        end_index = request.start + request.limit
        if end_index >= nr_of_rows:
            end_index = nr_of_rows

        rv = exd_api.ValuesResult(id=request.group_id)
        for channel_id in request.channel_ids:
            if channel_id >= table.num_columns:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(f"Invalid channel id {channel_id}!")
                raise NotImplementedError(f"Invalid channel id {channel_id}!")

            channel = table.columns[channel_id]
            ods_data_type = self.__get_datatype(channel.type)
            new_channel_values = exd_api.ValuesResult.ChannelValues()
            new_channel_values.id = channel_id
            new_channel_values.values.data_type = ods_data_type
            if ods.DataTypeEnum.DT_BYTE == ods_data_type:
                new_channel_values.values.byte_array.values = np.array(
                    channel[request.start: end_index], np.uint8
                ).tobytes()
            elif ods.DataTypeEnum.DT_SHORT == ods_data_type:
                new_channel_values.values.long_array.values[:] = np.array(
                    channel[request.start: end_index], np.int32)
            elif ods.DataTypeEnum.DT_LONG == ods_data_type:
                new_channel_values.values.long_array.values[:] = np.array(
                    channel[request.start: end_index], np.int32)
            elif ods.DataTypeEnum.DT_LONGLONG == ods_data_type:
                new_channel_values.values.longlong_array.values[:] = np.array(
                    channel[request.start: end_index], np.int64
                )
            elif ods.DataTypeEnum.DT_FLOAT == ods_data_type:
                new_channel_values.values.float_array.values[:] = np.array(
                    channel[request.start: end_index], np.float32
                )
            elif ods.DataTypeEnum.DT_DOUBLE == ods_data_type:
                new_channel_values.values.double_array.values[:] = np.array(
                    channel[request.start: end_index], np.float64
                )
            elif ods.DataTypeEnum.DT_DATE == ods_data_type:
                datetime_values = channel[request.start: end_index]
                string_values = []
                for datetime_value in datetime_values:
                    string_values.append(
                        self.__to_asam_ods_time(datetime_value))
                new_channel_values.values.string_array.values[:] = string_values
            elif ods.DataTypeEnum.DT_STRING == ods_data_type:
                new_channel_values.values.string_array.values[:] = np.array(
                    channel[request.start: end_index], np.bytes_
                )
            else:
                raise NotImplementedError(
                    f"Not implemented channel type {ods_data_type}!")

            rv.channels.append(new_channel_values)

        return rv

    def GetValuesEx(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def __to_asam_ods_time(self, datetime_value):
        return re.sub("[^0-9]", "", str(datetime_value))

    def __get_datatype(self, data_type):
        if pa.int8() == data_type:
            return ods.DataTypeEnum.DT_SHORT
        elif pa.uint8() == data_type:
            return ods.DataTypeEnum.DT_BYTE
        elif pa.int16() == data_type:
            return ods.DataTypeEnum.DT_SHORT
        elif pa.uint16() == data_type:
            return ods.DataTypeEnum.DT_LONG
        elif pa.int32() == data_type:
            return ods.DataTypeEnum.DT_LONG
        elif pa.uint32() == data_type:
            return ods.DataTypeEnum.DT_LONGLONG
        elif pa.int64() == data_type:
            return ods.DataTypeEnum.DT_LONGLONG
        elif pa.uint64() == data_type:
            return ods.DataTypeEnum.DT_DOUBLE
        elif pa.timestamp("us") == data_type:
            return ods.DataTypeEnum.DT_DATE
        elif pa.float32() == data_type:
            return ods.DataTypeEnum.DT_FLOAT
        elif pa.float64() == data_type:
            return ods.DataTypeEnum.DT_DOUBLE
        elif pa.string() == data_type:
            return ods.DataTypeEnum.DT_STRING
        raise NotImplementedError(f"Unknown type {data_type}!")

    def __init__(self):
        self.connect_count = 0
        self.connection_map = {}
        self.file_map = {}
        self.lock = threading.Lock()

    def __get_id(self, identifier):
        self.connect_count = self.connect_count + 1
        rv = str(self.connect_count)
        self.connection_map[rv] = identifier
        return rv

    def __uri_to_path(self, uri):
        parsed = urlparse(uri)
        host = "{0}{0}{mnt}{0}".format(os.path.sep, mnt=parsed.netloc)
        return os.path.normpath(os.path.join(host, url2pathname(unquote(parsed.path))))

    def __get_path(self, file_url):
        final_path = self.__uri_to_path(file_url)
        return final_path

    def __open_file(self, identifier):
        with self.lock:
            identifier.parameters
            connection_id = self.__get_id(identifier)
            connection_url = self.__get_path(identifier.url)
            if connection_url not in self.file_map:
                file_handle = pq.read_table(connection_url)
                self.file_map[connection_url] = {
                    "file": file_handle, "ref_count": 0}
            self.file_map[connection_url]["ref_count"] = self.file_map[connection_url]["ref_count"] + 1
            return connection_id

    def __get_file(self, handle):
        identifier = self.connection_map[handle.uuid]
        connection_url = self.__get_path(identifier.url)
        return self.file_map[connection_url]["file"]

    def __close_file(self, handle):
        with self.lock:
            identifier = self.connection_map[handle.uuid]
            connection_url = self.__get_path(identifier.url)
            if self.file_map[connection_url]["ref_count"] > 1:
                self.file_map[connection_url]["ref_count"] = self.file_map[connection_url]["ref_count"] - 1
            else:
                # self.file_map[connection_url]["file"].close()
                del self.file_map[connection_url]
