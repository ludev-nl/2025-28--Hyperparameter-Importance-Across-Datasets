import unittest
import pandas as pd
from help import dictDFtoJSON, dictJSONtoDF

class TestDataFrameConversion(unittest.TestCase):

    def setUp(self):
        # Create sample DataFrames for testing
        self.df1 = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6]
        })
        
        self.df2 = pd.DataFrame({
            "X": [7, 8, 9],
            "Y": [10, 11, 12]
        })
        
        self.df_dict = {
            "df1": self.df1,
            "df2": self.df2
        }
        # Corresponding JSON representation
        self.json_dict = {
            "df1": [self.df1.to_json(index=False)],
            "df2": [self.df2.to_json(index=False)]
        }

    def test_dictDFtoJSON(self):
        # Convert DataFrames to JSON
        result = dictDFtoJSON(self.df_dict)
        
        # Check if the result matches the expected JSON dictionary
        self.assertEqual(result, self.json_dict)

    def test_dictJSONtoDF(self):
        # Convert JSON back to DataFrames
        result = dictJSONtoDF(self.json_dict)
        
        # Check if the result matches the original DataFrames
        pd.testing.assert_frame_equal(result["df1"], self.df1)
        pd.testing.assert_frame_equal(result["df2"], self.df2)

    def test_dictDFtoJSON_empty(self):
        # Test with an empty dictionary
        empty_dict = {}
        result = dictDFtoJSON(empty_dict)
        
        # Check if the result is also an empty dictionary
        self.assertEqual(result, {})

    def test_dictJSONtoDF_empty(self):
        # Test with an empty JSON dictionary
        empty_json_dict = {}
        result = dictJSONtoDF(empty_json_dict)
        
        # Check if the result is also an empty dictionary
        self.assertEqual(result, {})

    def test_dictJSONtoDF_invalid(self):
        # Test handling of invalid JSON format (empty string in place of valid JSON)
        invalid_json_dict = {
            "df1": [""]
        }
        with self.assertRaises(ValueError):
            dictJSONtoDF(invalid_json_dict)

if __name__ == "__main__":
    unittest.main()
