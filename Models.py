from dataclasses import dataclass, field

import numpy as np


@dataclass
class ConversionModel:
    blockstate_to_id: dict[str, int] = field(default_factory=dict)
    rawData: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.uint32))
    width: int = 0
    length: int = 0
    height: int = 0


@dataclass
class SchematicModel:
    blocks: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.uint16))
    block_metadata: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.uint8))
    width: int = 0
    length: int = 0
    height: int = 0
