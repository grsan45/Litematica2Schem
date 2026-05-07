import json
from enum import Enum
from pathlib import Path

import numpy as np

from Models import ConversionModel, SchematicModel


class MappingFileCheckResult(Enum):
    CHECK_SUCCESS = "CHECK_SUCCESS"
    CHECK_FAILURE_NOT_EXISTS = "CHECK_FAILURE_NOT_EXISTS"
    CHECK_FAILURE_INVALID_KEYS = "CHECK_FAILURE_INVALID_KEYS"
    CHECK_FAILURE_INVALID_SYNTAX = "CHECK_FAILURE_INVALID_SYNTAX"


class BlockIdMapper:
    block_map_file: Path

    def __init__(
        self,
        conversion_model: ConversionModel,
        blockMapFile: str | Path | None = None,
    ) -> None:
        self.conversion_model = conversion_model
        self.block_map_file = Path(blockMapFile) if blockMapFile is not None else Path("blockmap.json")

    def convert_block_ids(self) -> SchematicModel:
        mapping_data = json.loads(self.block_map_file.read_text(encoding="utf-8"))
        id_to_blockstate = {
            block_id: blockstate
            for blockstate, block_id in self.conversion_model.blockstate_to_id.items()
        }

        blocks = np.empty(self.conversion_model.rawData.shape, dtype=np.uint16)
        block_metadata = np.empty(self.conversion_model.rawData.shape, dtype=np.uint8)
        uint16_limits = np.iinfo(np.uint16)
        uint8_limits = np.iinfo(np.uint8)

        for index, raw_block_id in enumerate(self.conversion_model.rawData):
            blockstate = id_to_blockstate.get(int(raw_block_id))
            if blockstate is None:
                raise ValueError(f"No blockstate found for raw block ID {raw_block_id}.")

            mapped_value = mapping_data.get(blockstate)
            if not isinstance(mapped_value, str):
                raise ValueError(f'Mapping for "{blockstate}" must be a string in the format "id" or "id:meta".')

            parts = mapped_value.split(":")
            if len(parts) not in {1, 2}:
                raise ValueError(f'Mapping for "{blockstate}" must be in the format "id" or "id:meta".')

            try:
                block_value = int(parts[0])
                metadata_value = int(parts[1]) if len(parts) == 2 else 0
            except ValueError as exc:
                raise ValueError(
                    f'Mapping for "{blockstate}" must contain integer values in the format "id" or "id:meta".'
                ) from exc

            if not uint16_limits.min <= block_value <= uint16_limits.max:
                raise ValueError(f'Block ID {block_value} for "{blockstate}" is outside the uint16 range.')

            if not uint8_limits.min <= metadata_value <= uint8_limits.max:
                raise ValueError(f'Block metadata {metadata_value} for "{blockstate}" is outside the uint8 range.')

            blocks[index] = block_value
            block_metadata[index] = metadata_value

        return SchematicModel(
            blocks=blocks,
            block_metadata=block_metadata,
            width=self.conversion_model.width,
            length=self.conversion_model.length,
            height=self.conversion_model.height,
        )

    def create_mapping_file(self) -> None:
        mapping_data = {
            blockstate: "" for blockstate in self.conversion_model.blockstate_to_id.keys()
        }

        self.block_map_file.write_text(json.dumps(mapping_data, indent=2), encoding="utf-8")

    def add_missing_keys_to_mapping_file(self) -> None:
        mapping_data = json.loads(self.block_map_file.read_text(encoding="utf-8"))

        for blockstate in self.conversion_model.blockstate_to_id.keys():
            mapping_data.setdefault(blockstate, "")

        self.block_map_file.write_text(json.dumps(mapping_data, indent=2), encoding="utf-8")

    def check_mapping_file(self) -> MappingFileCheckResult:
        if not self.block_map_file.is_file():
            return MappingFileCheckResult.CHECK_FAILURE_NOT_EXISTS

        try:
            mapping_data = json.loads(self.block_map_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return MappingFileCheckResult.CHECK_FAILURE_INVALID_SYNTAX

        if not isinstance(mapping_data, dict):
            return MappingFileCheckResult.CHECK_FAILURE_INVALID_SYNTAX

        expected_keys = set(self.conversion_model.blockstate_to_id.keys())
        actual_keys = set(mapping_data.keys())
        if not expected_keys.issubset(actual_keys):
            return MappingFileCheckResult.CHECK_FAILURE_INVALID_KEYS

        return MappingFileCheckResult.CHECK_SUCCESS
