import os
import logging
import pathlib
import tempfile
import unittest
from datetime import datetime

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class TestFileAccess(unittest.TestCase):
    log = logging.getLogger(__name__)

    def __get_example_file_path(self, file_name):
        example_file_path = pathlib.Path.joinpath(pathlib.Path(__file__).parent.resolve(), "..", "data", file_name)
        return pathlib.Path(example_file_path).resolve()

    def test_create_example_all_datatypes(self):

        with tempfile.TemporaryDirectory() as temporary_directory_name:
            file_path = os.path.join(temporary_directory_name, "all_datatypes_test.parquet")

            df = pd.DataFrame(
                {
                    # "complex64_data": np.array([1+2j, 3+4j], np.complex64),
                    # "complex128_data": np.array([5+6j, 7+8j], np.complex128),
                    "int8_data": np.array([-2, 4], np.int8),
                    "uint8_data": np.array([2, 4], np.uint8),
                    "int16_data": np.array([-2, 4], np.int16),
                    "uint16_data": np.array([2, 4], np.uint16),
                    "int32_data": np.array([-2, 4], np.int32),
                    "uint32_data": np.array([2, 4], np.uint32),
                    "int64_data": np.array([-2, 4], np.int64),
                    "uint64_data": np.array([2, 4], np.uint64),
                    "date_data": np.array(
                        [datetime(2017, 7, 9, 12, 35, 0), datetime(2017, 7, 9, 12, 36, 0)], np.datetime64
                    ),
                    "float32_data": np.array([1.1, 1.2], np.float32),
                    "float64_data": np.array([2.1, 2.2], np.float64),
                    "string_data": ["abc", "def"],
                }
            )
            pq.write_table(pa.Table.from_pandas(df), file_path)
            table = pq.read_table(file_path)

            # 'int8_data', 'uint8_data', 'int16_data', 'uint16_data', 'int32_data', 'uint32_data', 'int64_data',
            # 'uint64_data', 'date_data', 'float32_data', 'float64_data', 'string_data'
            # DataType(int8), DataType(uint8), DataType(int16), DataType(uint16), DataType(int32),
            # DataType(uint32), DataType(int64), DataType(uint64), TimestampType(timestamp[us]),
            # DataType(float), DataType(double), DataType(string)]

            for channel_index, channel_name in enumerate(table.schema.names):
                channel_type = table.schema.types[channel_index]
                # print(f"Channel: {channel_name} - {channel_type}")
                if pa.int8() == channel_type:
                    print(f"  i8: {channel_name}")
                    pass
                elif pa.uint8() == channel_type:
                    print(f" ui8: {channel_name}")
                    pass

            print(f"nr col: {table.num_columns}")
            print(f"nr rows: {table.num_rows}")
            print(table.columns[1][1:2])


if __name__ == "__main__":
    unittest.main()
