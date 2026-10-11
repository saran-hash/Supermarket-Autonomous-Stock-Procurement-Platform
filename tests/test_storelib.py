import unittest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import storelib


class TestStorelib(unittest.TestCase):
    def test_norm_sku(self):
        self.assertEqual(storelib.norm_sku("Sunflower Oil"), "SKU-OIL-SUN-001")
        self.assertEqual(storelib.norm_sku("8901030000011"), "SKU-OIL-SUN-001")
        self.assertEqual(storelib.norm_sku("white sugar"), "SKU-GROC-SUG-001")
        self.assertEqual(storelib.norm_sku("SKU-DAIR-GHEE-001"), "SKU-DAIR-GHEE-001")

    def test_norm_qty(self):
        qty, unit = storelib.norm_qty("500g")
        self.assertEqual(qty, 0.5)
        self.assertEqual(unit, "kg")

        qty, unit = storelib.norm_qty("1000ml")
        self.assertEqual(qty, 1.0)
        self.assertEqual(unit, "L")

        qty, unit = storelib.norm_qty(15, "pcs")
        self.assertEqual(qty, 15.0)
        self.assertEqual(unit, "pcs")

    def test_norm_dealer(self):
        self.assertEqual(storelib.norm_dealer("Sri Lakshmi Traders"), "DLR-001")
        self.assertEqual(storelib.norm_dealer("metro"), "DLR-002")
        self.assertEqual(storelib.norm_dealer("Annapoorna Provisions"), "DLR-003")

    def test_norm_channel(self):
        self.assertEqual(storelib.norm_channel("whatsapp"), "whatsapp")
        self.assertEqual(storelib.norm_channel("WA"), "whatsapp")
        self.assertEqual(storelib.norm_channel("email"), "email")
        self.assertEqual(storelib.norm_channel("mail"), "email")


if __name__ == "__main__":
    unittest.main()
