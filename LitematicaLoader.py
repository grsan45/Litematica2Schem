from pathlib import Path

import numpy as np
from litemapy.schematic import Schematic
from Models import ConversionModel


class LitematicaLoader:
    path: Path

    def __init__(self, filename: str) -> None:
        path = Path(filename)

        if path.suffix.lower() != ".litematic":
            raise ValueError("File must have a .litematic extension.")

        if not path.is_file():
            raise FileNotFoundError(f"Litematic file not found: {filename}")

        self.path = path

    def load(self) -> ConversionModel:
        schematic = Schematic.load(self.path)
        regions = tuple(schematic.regions.values())

        if not regions:
            raise ValueError("Schematic does not contain any regions.")

        region = regions[0]
        model = ConversionModel(
            width=abs(region.width),
            length=abs(region.length),
            height=abs(region.height),
        )

        for index, blockstate in enumerate(region.palette):
            model.blockstate_to_id[blockstate.to_block_state_identifier()] = index

        model.rawData = np.full(
            model.width * model.length * model.height,
            0,
            dtype=np.uint32,
        )

        for y_index, y in enumerate(region.range_y()):
            for z_index, z in enumerate(region.range_z()):
                for x_index, x in enumerate(region.range_x()):
                    blockstate = region[x, y, z]
                    blockstate_id = model.blockstate_to_id[blockstate.to_block_state_identifier()]
                    raw_index = (y_index * model.length + z_index) * model.width + x_index
                    model.rawData[raw_index] = blockstate_id

        return model
