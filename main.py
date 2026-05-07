import argparse
from pathlib import Path

from LitematicaLoader import LitematicaLoader
from Mapper import BlockIdMapper, MappingFileCheckResult
from Writers import SchematicaWriter, WorldEditWriter


def format_model_output(model, verbose: bool = False) -> str:
    if verbose:
        blockstate_lines = [f"    {blockstate!r}: {block_id}," for blockstate, block_id in model.blockstate_to_id.items()]
    else:
        preview_items = list(model.blockstate_to_id.items())[:5]
        blockstate_lines = [f"    {blockstate!r}: {block_id}," for blockstate, block_id in preview_items]
        remaining = len(model.blockstate_to_id) - len(preview_items)
        if remaining > 0:
            blockstate_lines.append(f"    ... ({remaining} more entries)")

    lines = [
        "ConversionModel(",
        f"  width={model.width},",
        f"  length={model.length},",
        f"  height={model.height},",
        f"  paletteSize={len(model.blockstate_to_id)},",
        "  blockstate_to_id={",
    ]

    lines.extend(blockstate_lines)

    lines.extend(
        [
            "  },",
            (
                "  rawData="
                f"array(shape={model.rawData.shape}, dtype={model.rawData.dtype}, "
                f"min={model.rawData.min()}, max={model.rawData.max()}, "
                f"preview={model.rawData[:16].tolist()})"
            ),
            ")",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert modern Litematica schematics to pre-1.12 MCEdit schematics.")
    parser.add_argument("inputFile", help="Path to the .litematic file to load.")
    parser.add_argument(
        "--mappingFile",
        dest="mappingFile",
        help='Path to the block mapping file. Defaults to "blockmap.json".',
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the full blockstate_to_id mapping.",
    )
    parser.add_argument(
        "--useSchemPlus",
        action="store_true",
        help="Use the schemplus format to support more blockIDs. Schematica must also have the schemplus config option enabled.",
    )
    parser.add_argument(
        "--writer",
        choices=("schematica", "worldedit"),
        default="schematica",
        help="Choose which schematic writer to use.",
    )
    args = parser.parse_args()

    if args.writer == "worldedit" and args.useSchemPlus:
        print("The --useSchemPlus option is not supported with the worldedit writer.")
        return

    loader = LitematicaLoader(args.inputFile)
    model = loader.load()

    print(format_model_output(model, verbose=args.verbose))

    mapper = BlockIdMapper(model, args.mappingFile)
    check_result = mapper.check_mapping_file()

    if check_result == MappingFileCheckResult.CHECK_FAILURE_NOT_EXISTS:
        mapper.create_mapping_file()
        print(f'Mapping file "{mapper.block_map_file}" was created. Fill it out and run the program again.')
        return

    if check_result == MappingFileCheckResult.CHECK_FAILURE_INVALID_KEYS:
        mapper.add_missing_keys_to_mapping_file()
        print(f'Mapping file "{mapper.block_map_file}" was updated with missing keys. Fill them out and run the program again.')
        return

    if check_result == MappingFileCheckResult.CHECK_FAILURE_INVALID_SYNTAX:
        print(f'Mapping file "{mapper.block_map_file}" is invalid.')
        replace_file = input("Delete it and replace it with a new one? [y/N]: ").strip().lower()
        if replace_file in {"y", "yes"}:
            Path(mapper.block_map_file).unlink(missing_ok=True)
            mapper.create_mapping_file()
            print(f'Replaced "{mapper.block_map_file}". Fill it out and run the program again.')
        return

    try:
        schematic_model = mapper.convert_block_ids()
    except ValueError as exc:
        print(exc)
        return

    input_path = Path(args.inputFile)
    output_extension = ".schemplus" if args.useSchemPlus else ".schematic"
    output_file_name = input_path.with_name(f"{input_path.stem}_converted{output_extension}")

    if args.writer == "worldedit":
        writer = WorldEditWriter(schematic_model, output_file_name)
    else:
        writer = SchematicaWriter(
            schematic_model,
            output_file_name,
            use_schem_plus=args.useSchemPlus,
        )

    writer.write()
    print(f'Wrote converted schematic to "{output_file_name}".')


if __name__ == "__main__":
    main()
