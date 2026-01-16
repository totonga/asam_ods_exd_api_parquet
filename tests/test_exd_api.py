import unittest
import pathlib
import logging

from ods_exd_api_box import ExternalDataReader, FileHandlerRegistry, exd_api, ods
from external_data_file import ExternalDataFile
from tests.mock_servicer_context import MockServicerContext

# pylint: disable=no-member


class TestExdApi(unittest.TestCase):
    log = logging.getLogger(__name__)

    def setUp(self):
        """Register ExternalDataFile handler before each test."""
        FileHandlerRegistry.register(
            file_type_name="test", factory=ExternalDataFile)
        self.context = MockServicerContext()

    def _get_example_file_path(self, file_name: str) -> str:
        example_file_path = pathlib.Path.joinpath(pathlib.Path(
            __file__).parent.resolve(), '..', 'data', file_name)
        return pathlib.Path(example_file_path).absolute().resolve().as_uri()

    def test_open(self):
        service = ExternalDataReader()
        handle = service.Open(exd_api.Identifier(
            url=self._get_example_file_path('all_datatypes.parquet'),
            parameters=""), self.context)
        try:
            pass
        finally:
            service.Close(handle, self.context)

    def test_structure(self):
        service = ExternalDataReader()
        handle = service.Open(exd_api.Identifier(
            url=self._get_example_file_path('all_datatypes.parquet'),
            parameters=""), self.context)
        try:
            structure = service.GetStructure(
                exd_api.StructureRequest(handle=handle), self.context)

            self.assertEqual(structure.name, 'all_datatypes.parquet')
            self.assertEqual(len(structure.groups), 1)
            self.assertEqual(structure.groups[0].number_of_rows, 2)
            self.assertEqual(len(structure.groups[0].channels), 12)
            self.assertEqual(structure.groups[0].id, 0)
            self.assertEqual(structure.groups[0].channels[0].id, 0)
            self.assertEqual(structure.groups[0].channels[1].id, 1)
            self.assertEqual(
                structure.groups[0].channels[0].data_type, ods.DataTypeEnum.DT_SHORT)
            self.assertEqual(
                structure.groups[0].channels[1].data_type, ods.DataTypeEnum.DT_BYTE)
        finally:
            service.Close(handle, self.context)

    def test_get_values(self):
        service = ExternalDataReader()
        handle = service.Open(exd_api.Identifier(
            url=self._get_example_file_path(
                'all_datatypes.parquet'),
            parameters=""), self.context)
        try:
            values = service.GetValues(exd_api.ValuesRequest(handle=handle,
                                                             group_id=0,
                                                             channel_ids=[
                                                                 0, 1],
                                                             start=0,
                                                             limit=4), self.context)
            self.assertEqual(values.id, 0)
            self.assertEqual(len(values.channels), 2)
            self.assertEqual(values.channels[0].id, 0)
            self.assertEqual(values.channels[1].id, 1)

            self.assertEqual(
                values.channels[0].values.data_type, ods.DataTypeEnum.DT_SHORT)
            self.assertSequenceEqual(
                values.channels[0].values.long_array.values, [-2, 4])
            self.assertEqual(
                values.channels[1].values.data_type, ods.DataTypeEnum.DT_BYTE)
            self.assertSequenceEqual(
                values.channels[1].values.byte_array.values, b'\x02\x04')

        finally:
            service.Close(handle, self.context)
