from abc import ABC, abstractmethod
from pathlib import Path

import nbtlib
import numpy as np

from Models import SchematicModel


class Writer(ABC):
    output_file_name: Path

    def __init__(self, schematic_model: SchematicModel, output_file_name: str | Path) -> None:
        self.schematic_model = schematic_model
        self.output_file_name = Path(output_file_name)

    @abstractmethod
    def write(self) -> None:
        raise NotImplementedError


class SchematicaWriter(Writer):
    def __init__(
        self,
        schematic_model: SchematicModel,
        output_file_name: str | Path | None = None,
        use_schem_plus: bool = False,
    ) -> None:
        self.use_schem_plus = use_schem_plus
        if output_file_name is None:
            output_file_name = "output.schemplus" if use_schem_plus else "output.schematic"
        super().__init__(schematic_model, output_file_name)

    def write(self) -> None:
        blocks = self.schematic_model.blocks.astype(np.uint16, copy=False)
        lower_bytes = (blocks & 0xFF).astype(np.uint8).view(np.int8)
        upper_bytes = ((blocks >> 8) & 0xFF).astype(np.uint8)
        metadata_bytes = self.schematic_model.block_metadata.astype(np.uint8, copy=False).view(np.int8)

        if self.use_schem_plus:
            add_blocks = upper_bytes.view(np.int8)
        else:
            upper_nibbles = upper_bytes & 0x0F
            packed_add_blocks = np.zeros((upper_nibbles.size + 1) // 2, dtype=np.uint8)

            for index, nibble in enumerate(upper_nibbles):
                packed_index = index // 2
                if index % 2 == 0:
                    packed_add_blocks[packed_index] |= nibble << 4
                else:
                    packed_add_blocks[packed_index] |= nibble

            add_blocks = packed_add_blocks.view(np.int8)

        schematic = nbtlib.File(
            {
                "Width": nbtlib.Short(self.schematic_model.width),
                "Length": nbtlib.Short(self.schematic_model.length),
                "Height": nbtlib.Short(self.schematic_model.height),
                "Materials": nbtlib.String("Alpha"),
                "Blocks": nbtlib.ByteArray(lower_bytes.tolist()),
                "AddBlocks": nbtlib.ByteArray(add_blocks.tolist()),
                "Data": nbtlib.ByteArray(metadata_bytes.tolist()),
                "TileEntities": nbtlib.List(),
                "Entities": nbtlib.List()
            },
            gzipped=True,
            root_name="Schematic",
        )
        schematic.save(self.output_file_name)


class WorldEditWriter(Writer):
    def __init__(
        self,
        schematic_model: SchematicModel,
        output_file_name: str | Path = "output.schematic",
    ) -> None:
        super().__init__(schematic_model, output_file_name)

    def write(self) -> None:
        blocks = self.schematic_model.blocks.astype(np.uint16, copy=False)
        lower_bytes = (blocks & 0xFF).astype(np.uint8).view(np.int8)
        upper_nibbles = ((blocks >> 8) & 0x0F).astype(np.uint8)
        metadata_bytes = self.schematic_model.block_metadata.astype(np.uint8, copy=False).view(np.int8)
        packed_add_blocks = np.zeros((upper_nibbles.size + 1) // 2, dtype=np.uint8)

        for index, nibble in enumerate(upper_nibbles):
            packed_index = index // 2
            if index % 2 == 0:
                packed_add_blocks[packed_index] |= nibble
            else:
                packed_add_blocks[packed_index] |= nibble << 4

        schematic = nbtlib.File(
            {
                "Width": nbtlib.Short(self.schematic_model.width),
                "Length": nbtlib.Short(self.schematic_model.length),
                "Height": nbtlib.Short(self.schematic_model.height),
                "Materials": nbtlib.String("Alpha"),
                "Blocks": nbtlib.ByteArray(lower_bytes.tolist()),
                "AddBlocks": nbtlib.ByteArray(packed_add_blocks.view(np.int8).tolist()),
                "Data": nbtlib.ByteArray(metadata_bytes.tolist()),
                "TileEntities": nbtlib.List(),
                "Entities": nbtlib.List(),
            },
            gzipped=True,
            root_name="Schematic",
        )
        schematic.save(self.output_file_name)
