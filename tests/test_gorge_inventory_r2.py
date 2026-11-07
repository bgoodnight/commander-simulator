import json
import unittest
from unittest.mock import patch
from tools.gorge_inventory_r2 import inventory, list_prefix

class InventoryTests(unittest.TestCase):
    def test_pagination(self):
        pages = [
            {"Contents":[{"Key":"warehouse/v1/b1/h/s/manifest.json","Size":99}],
             "IsTruncated":True,"NextContinuationToken":"next"},
            {"Contents":[{"Key":"warehouse/v1/b1/h/s/games.parquet","Size":100}],
             "IsTruncated":False},
        ]
        with patch("tools.gorge_inventory_r2.aws", side_effect=[json.dumps(p) for p in pages]) as call:
            objects=list_prefix("https://test.r2.cloudflarestorage.com","warehouse/",20)
        self.assertEqual(len(objects),2)
        self.assertIn("--continuation-token", call.call_args_list[1].args)
    def test_manifest_only_and_separate_counts(self):
        def mock_aws(endpoint,*args):
            if args[0]=="s3api":
                prefix=args[args.index("--prefix")+1]
                if prefix=="warehouse/":
                    return json.dumps({"Contents":[
                        {"Key":"warehouse/v1/batch1/mortarion_current/s0/manifest.json","Size":120},
                        {"Key":"warehouse/v1/batch1/mortarion_current/s0/games.parquet","Size":500}],
                        "IsTruncated":False})
                if prefix=="native/":
                    return json.dumps({"Contents":[{"Key":"native/experimental/corrected-pilot/v1/123-1/mortarion_current.tar.gz","Size":800}],
                                       "IsTruncated":False})
                return json.dumps({"Contents":[],"IsTruncated":False})
            self.assertEqual(args[:2],("s3","cp"))
            self.assertTrue(args[2].endswith("manifest.json"))
            return json.dumps({"schema":"gorge-warehouse-shard-v1","games":12,"native_events":120})
        with patch("tools.gorge_inventory_r2.aws", side_effect=mock_aws):
            result=inventory("https://test.r2.cloudflarestorage.com")
        self.assertEqual(result["warehouse_declared_games_total"],12)
        self.assertEqual(result["native_objects_total"],1)
        self.assertFalse(result["complete_game_count_claim"])
    def test_object_cap(self):
        with patch("tools.gorge_inventory_r2.aws",return_value=json.dumps({
            "Contents":[{"Key":"native/a","Size":1},{"Key":"native/b","Size":1}],
            "IsTruncated":False})):
            with self.assertRaisesRegex(ValueError,"object limit"):
                list_prefix("https://test.r2.cloudflarestorage.com","native/",1)

if __name__=="__main__":
    unittest.main()
