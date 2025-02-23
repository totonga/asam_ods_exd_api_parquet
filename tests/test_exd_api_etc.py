# Prepare python to use GRPC interface:
# python -m grpc_tools.protoc --proto_path=proto_src --pyi_out=. --python_out=. --grpc_python_out=. ods.proto ods_external_data.proto
import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import logging
import pathlib
import unittest

import ods_pb2 as ods
import ods_external_data_pb2 as oed

from external_data_reader import ExternalDataReader
from google.protobuf.json_format import MessageToJson

class TestExdApiEtc(unittest.TestCase):
    log = logging.getLogger(__name__)

    def _get_example_file_path(self, file_name):
        example_file_path = pathlib.Path.joinpath(pathlib.Path(__file__).parent.resolve(), '..', 'data', file_name)
        return pathlib.Path(example_file_path).absolute().resolve().as_uri()

    def test_file_all_datatypes(self):
        service = ExternalDataReader()
        handle = service.Open(oed.Identifier(
            url = self._get_example_file_path('all_datatypes.parquet'),
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

            values = service.GetValues(oed.ValuesRequest(handle=handle,
                                                         group_id=0,
                                                         channel_ids=[0,1],
                                                         start=0,
                                                         limit=4), None)
            self.assertEqual(len(values.channels), 2)
            self.log.info(MessageToJson(values))
            self.assertEqual(values.channels[0].values.data_type, ods.DataTypeEnum.DT_SHORT)
            self.assertSequenceEqual(values.channels[0].values.long_array.values, [-2, 4])
            self.assertEqual(values.channels[1].values.data_type, ods.DataTypeEnum.DT_BYTE)
            self.assertSequenceEqual(values.channels[1].values.byte_array.values, b'\x02\x04')

        finally:
            service.Close(handle, None)

if __name__ == '__main__':
    unittest.main()