"""EXD API implementation for parquet files"""

from __future__ import annotations

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ods_exd_api_box import ExdFileInterface, exd_api, ods


class ExternalDataFile(ExdFileInterface):
    """Class for handling for NI tdms files."""

    @classmethod
    @override
    def create(cls, file_path: str, parameters: str) -> ExdFileInterface:
        """Factory method to create a file handler instance."""
        return cls(file_path, parameters)

    @override
    def __init__(self, file_path: str, parameters: str = ""):

        if not file_path.is_file():
            raise Exception(f'file "{file_path}" not accessible')

        self.file_path = file_path
        self.parameters = parameters
        self.table = pq.read_table(file_path)

    @override
    def close(self):
        self.__close_file(request)
        return exd_api.Empty()

    @override
    def fill_structure(self, structure: exd_api.StructureResult) -> None:

        table = self.table

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
        structure.groups.append(new_group)
        return structure

    @override
    def get_values(self, request: exd_api.ValuesRequest) -> exd_api.ValuesResult:

        table = self.table
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


if __name__ == "__main__":

    from ods_exd_api_box import serve_plugin

    serve_plugin(
        file_type_name="PARQUET", file_type_factory=ExternalDataFile.create, file_type_file_patterns=["*.parquet"]
    )