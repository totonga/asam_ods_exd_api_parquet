# Prepare python to use GRPC interface:
# python -m grpc_tools.protoc --proto_path=proto_src --pyi_out=. --python_out=. --grpc_python_out=. ods.proto ods_external_data.proto
import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import logging
import pathlib
import unittest
from datetime import datetime
import tempfile
from pathlib import Path

import numpy as np

import ods_pb2 as ods
import ods_external_data_pb2 as oed

from external_data_reader import ExternalDataReader
from google.protobuf.json_format import MessageToJson

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class TestDataTypes(unittest.TestCase):
    log = logging.getLogger(__name__)

    def _get_example_file_path(self, file_name):
        example_file_path = pathlib.Path.joinpath(pathlib.Path(__file__).parent.resolve(), '..', 'data', file_name)
        return pathlib.Path(example_file_path).absolute().resolve().as_uri()

    def test_datatype(self):
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            file_path = os.path.join(temporary_directory_name, "all_datatypes.parquet")

            df = pd.DataFrame({
                "int8_data": np.array([-2, 4], np.int8),
                "uint8_data": np.array([2, 4], np.uint8),
                "int16_data": np.array([-2, 4], np.int16),
                "uint16_data": np.array([2, 4], np.uint16),
                "int32_data": np.array([-2, 4], np.int32),
                "uint32_data": np.array([2, 4], np.uint32),
                "int64_data": np.array([-2, 4], np.int64),
                "uint64_data": np.array([2, 4], np.uint64),
                "date_data": np.array([datetime(2017, 7, 9, 12, 35, 0), datetime(2017, 7, 9, 12, 36, 0)], np.datetime64),
                "float32_data": np.array([1.1, 1.2], np.float32),
                "float64_data": np.array([2.1, 2.2], np.float64),
                "string_data": ["abc", "def"]
                })
            pq.write_table(pa.Table.from_pandas(df), file_path)
            table = pq.read_table(file_path)

            service = ExternalDataReader()
            handle = service.Open(oed.Identifier(
                url = Path(file_path).resolve().as_uri(),
                parameters = ""), None)
            try:
                structure = service.GetStructure(oed.StructureRequest(handle=handle), None)
                self.log.info(MessageToJson(structure))

                self.assertEqual(structure.name, 'all_datatypes.parquet')
                self.assertEqual(len(structure.groups), 1)
                self.assertEqual(structure.groups[0].number_of_rows, 2)
                self.assertEqual(len(structure.groups[0].channels), 12)

                self.assertEqual(structure.groups[0].channels[0].data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertEqual(structure.groups[0].channels[1].data_type, ods.DataTypeEnum.DT_BYTE)
                self.assertEqual(structure.groups[0].channels[2].data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertEqual(structure.groups[0].channels[3].data_type, ods.DataTypeEnum.DT_LONG)
                self.assertEqual(structure.groups[0].channels[4].data_type, ods.DataTypeEnum.DT_LONG)
                self.assertEqual(structure.groups[0].channels[5].data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertEqual(structure.groups[0].channels[6].data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertEqual(structure.groups[0].channels[7].data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertEqual(structure.groups[0].channels[8].data_type, ods.DataTypeEnum.DT_DATE)
                self.assertEqual(structure.groups[0].channels[9].data_type, ods.DataTypeEnum.DT_FLOAT)
                self.assertEqual(structure.groups[0].channels[10].data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertEqual(structure.groups[0].channels[11].data_type, ods.DataTypeEnum.DT_STRING)

                values = service.GetValues(oed.ValuesRequest(handle=handle, group_id=0, start=0, limit=2, channel_ids=[0,1,2,3,4,5,6,7,8,9,10,11]), None)
                self.assertEqual(values.channels[0].values.data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertSequenceEqual(values.channels[0].values.long_array.values, [-2, 4])
                self.assertEqual(values.channels[1].values.data_type, ods.DataTypeEnum.DT_BYTE)
                self.assertSequenceEqual(values.channels[1].values.byte_array.values, [2, 4])
                self.assertEqual(values.channels[2].values.data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertSequenceEqual(values.channels[2].values.long_array.values, [-2, 4])
                self.assertEqual(values.channels[3].values.data_type, ods.DataTypeEnum.DT_LONG)
                self.assertSequenceEqual(values.channels[3].values.long_array.values, [2, 4])
                self.assertEqual(values.channels[4].values.data_type, ods.DataTypeEnum.DT_LONG)
                self.assertSequenceEqual(values.channels[4].values.long_array.values, [-2, 4])
                self.assertEqual(values.channels[5].values.data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertSequenceEqual(values.channels[5].values.longlong_array.values, [2, 4])
                self.assertEqual(values.channels[6].values.data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertSequenceEqual(values.channels[6].values.longlong_array.values, [-2, 4])
                self.assertEqual(values.channels[7].values.data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertSequenceEqual(values.channels[7].values.double_array.values, [2.0, 4.0])
                self.assertEqual(values.channels[8].values.data_type, ods.DataTypeEnum.DT_DATE)
                self.assertSequenceEqual(values.channels[8].values.string_array.values, ['20170709123500', '20170709123600'])
                self.assertEqual(values.channels[9].values.data_type, ods.DataTypeEnum.DT_FLOAT)
                self.assertSequenceEqual(values.channels[9].values.float_array.values, [1.100000023841858, 1.2000000476837158])
                self.assertEqual(values.channels[10].values.data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertSequenceEqual(values.channels[10].values.double_array.values, [2.1, 2.2])
                self.assertEqual(values.channels[11].values.data_type, ods.DataTypeEnum.DT_STRING)
                self.assertSequenceEqual(values.channels[11].values.string_array.values, ['abc', 'def'])

            finally:
                service.Close(handle, None)


if __name__ == '__main__':
    unittest.main()