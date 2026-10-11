"""Canonical normalizers and path resolution for the Supermarket Platform.

Stdlib-first library mirroring ielib.py. Centralizes SKU resolution, unit
conversions, dealer identification, and path routing so all skills and agents
operate on clean, consistent relational keys.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parent

# --- Path Resolution --------------------------------------------------------
_ENV_DATA_ROOT = os.getenv("STORE_DATA_ROOT")
DATA_ROOT = Path(_ENV_DATA_ROOT).resolve() if _ENV_DATA_ROOT else (REPO_ROOT / "data")


def data_path(*parts: str) -> Path:
    """Resolve a path inside the data store (defaults to ./data)."""
    p = DATA_ROOT.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def code_path(*parts: str) -> Path:
    """Resolve a path inside the code repository."""
    return REPO_ROOT.joinpath(*parts)


# --- Canonical SKU & Product Mapping ----------------------------------------
# Canonical SKU catalogue mapping barcodes/aliases to standardized SKU identifiers
SKU_CATALOGUE = {
    "SKU-OIL-SUN-001": {
        "name": "Sunflower Oil 1L",
        "category": "Edible Oils",
        "base_unit": "pcs",
        "aliases": ["sunflower oil", "sunflower oil 1l", "oil-sun-1l", "8901030000011"],
    },
    "SKU-GROC-SUG-001": {
        "name": "White Refined Sugar 1kg",
        "category": "Staples",
        "base_unit": "kg",
        "aliases": ["white sugar", "sugar 1kg", "refined sugar", "8901030000028"],
    },
    "SKU-GROC-RICE-001": {
        "name": "Basmati Rice Premium 5kg",
        "category": "Staples",
        "base_unit": "kg",
        "aliases": ["basmati rice", "basmati rice 5kg", "rice premium", "8901030000035"],
    },
    "SKU-DAIR-GHEE-001": {
        "name": "Pure Cow Ghee 500ml",
        "category": "Dairy & Ghee",
        "base_unit": "pcs",
        "aliases": ["cow ghee", "pure ghee 500ml", "ghee 500ml", "8901030000042"],
    },
    "SKU-GROC-ATTA-001": {
        "name": "Chakki Fresh Atta 10kg",
        "category": "Staples",
        "base_unit": "kg",
        "aliases": ["atta", "wheat flour", "atta 10kg", "8901030000059"],
    },
    "SKU-DRYF-CAS-001": {
        "name": "Whole Cashews (Kaju) 500g",
        "category": "Dry Fruits",
        "base_unit": "kg",
        "aliases": ["cashews", "kaju", "kaju 500g", "8901030000066"],
    },
}


def norm_sku(val: str | None) -> str:
    """Normalize any product name, barcode, or raw code to canonical SKU ID.
    
    If already a canonical SKU (e.g. 'SKU-OIL-SUN-001'), returns uppercase trimmed.
    Otherwise searches aliases in SKU_CATALOGUE.
    """
    if not val:
        return ""
    clean = str(val).strip()
    if clean.upper() in SKU_CATALOGUE:
        return clean.upper()

    needle = clean.lower()
    for sku_id, meta in SKU_CATALOGUE.items():
        if needle == sku_id.lower() or needle == meta["name"].lower():
            return sku_id
        for alias in meta.get("aliases", []):
            if needle == alias or alias in needle:
                return sku_id

    # Fallback: clean alphanumeric slug
    slug = re.sub(r"[^A-Za-z0-9]+", "-", clean).strip("-").upper()
    return f"SKU-GEN-{slug[:12]}"


# --- Quantity & Unit Normalizer ---------------------------------------------
def norm_qty(val: float | int | str, unit_str: str | None = None) -> Tuple[float, str]:
    """Normalize quantities into standard base units (kg, pcs, L).
    
    Examples:
        norm_qty('500g')      -> (0.5, 'kg')
        norm_qty(5, 'kg')     -> (5.0, 'kg')
        norm_qty('1000ml')    -> (1.0, 'L')
        norm_qty(12, 'pcs')   -> (12.0, 'pcs')
    """
    if isinstance(val, str):
        # Match pattern like "500 g" or "1.5kg"
        m = re.match(r"^([0-9.]+)\s*([a-zA-Z]+)?$", val.strip())
        if m:
            num = float(m.group(1))
            extracted_unit = (m.group(2) or unit_str or "pcs").lower()
            return _convert_unit(num, extracted_unit)
        try:
            num = float(val.strip())
            return _convert_unit(num, (unit_str or "pcs").lower())
        except ValueError:
            return (0.0, unit_str or "pcs")

    return _convert_unit(float(val), (unit_str or "pcs").lower())


def _convert_unit(qty: float, unit: str) -> Tuple[float, str]:
    unit = unit.lower()
    if unit in {"g", "gram", "grams"}:
        return (round(qty / 1000.0, 3), "kg")
    if unit in {"kg", "kgs", "kilo", "kilogram"}:
        return (round(qty, 3), "kg")
    if unit in {"ml", "milliliter"}:
        return (round(qty / 1000.0, 3), "L")
    if unit in {"l", "liter", "liters", "ltr"}:
        return (round(qty, 3), "L")
    if unit in {"pcs", "pc", "piece", "pieces", "units", "unit", "nos"}:
        return (round(qty, 1), "pcs")
    return (qty, unit)


# --- Dealer Normalizer ------------------------------------------------------
DEALER_MAP = {
    "sri lakshmi": "DLR-001",
    "sri lakshmi traders": "DLR-001",
    "lakshmi traders": "DLR-001",
    "dlr-001": "DLR-001",
    "metro wholesale": "DLR-002",
    "metro": "DLR-002",
    "dlr-002": "DLR-002",
    "annapoorna provisions": "DLR-003",
    "annapoorna": "DLR-003",
    "dlr-003": "DLR-003",
}


def norm_dealer(val: str | None) -> str:
    """Normalize dealer name or reference to canonical DLR-XXX code."""
    if not val:
        return ""
    clean = str(val).strip().lower()
    for alias, code in DEALER_MAP.items():
        if alias in clean or clean == code.lower():
            return code
    m = re.search(r"(\d+)", clean)
    if m:
        return f"DLR-{int(m.group(1)):03d}"
    return f"DLR-GEN-{re.sub(r'[^A-Za-z0-9]', '', clean).upper()[:6]}"


# --- Communication Channel Normalizer ---------------------------------------
def norm_channel(val: str | None) -> str:
    """Normalize communication channel to 'whatsapp' or 'email'."""
    if not val:
        return "email"
    c = str(val).strip().lower()
    if any(k in c for k in ["wa", "whats", "phone", "mobile", "sms"]):
        return "whatsapp"
    return "email"
