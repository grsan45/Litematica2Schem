# Litematica2Schem

Litematica2Schem converts modern `.litematic` schematics into pre-1.12 `.schematic`-style outputs. This is primarily used to create builds in modern versions and port them to old modpacks that have modern block support, like GregTech: New Horizons.

It currently supports:

- `schematica` output
- `worldedit` output
- optional `schemplus` output when using the `schematica` writer

### AI-Assisted Disclosure
In the interest of time, this project made extensive use of Codex to improve development speed. I didn't want to spend 10 hours developing a non-user-friendly script for a build that I was ready to place in my world. For that reason, I decided to make use of AI while creating this. However, these formats are not standardized and are very poorly documented, so I still had to reverse engineer the schematica mod & hand-hold the agent quite a bit. I have reviewed the code and have used this on my own builds by now, so I can confirm the logic is sound.

## Requirements

- Python 3.10+
- `numpy`
- `litemapy`
- `nbtlib`

## Setup

1. Create and activate a virtual environment.
2. Install the required packages.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install numpy litemapy nbtlib
```

```pwsh
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install numpy litemapy nbtlib
```

## Basic Usage

Run the converter with a `.litematic` file:

```bash
python ./main.py ./your-build.litematic
```

By default this uses:

- the `schematica` writer
- `blockmap.json` in the current directory
- an output filename based on the input name, such as `your-build_converted.schematic`

## Command Line Options

```bash
python ./main.py ./your-build.litematic --mappingFile ./blockmap.json --writer schematica
```

Supported options (All optional):

- `--mappingFile <path>`: use a custom block mapping file
- `--writer schematica|worldedit`: choose the output writer (default is `schematica`)
- `--useSchemPlus`: enable `.schemplus` output for the `schematica` writer
- `--verbose`: print the full detected blockstate palette

Notes:

- `--useSchemPlus` is only supported with `--writer schematica`
- if `--useSchemPlus` is enabled, the output extension becomes `.schemplus`
- otherwise the output extension is `.schematic`

## Block Mapping Setup

The converter needs a `blockmap.json` file that maps each modern blockstate in the source schematic to a legacy block ID.

On the first run, if the mapping file does not exist, Litematica2Schem will generate one for you and stop so you can fill it in.

Each key is a modern Minecraft blockstate string, and each value is either:

- `"id"`
- `"id:meta"`

Examples:

- `"minecraft:stone": "1"`
- `"minecraft:black_stained_glass": "95:15"`
- `"minecraft:air": "0"`

If metadata is omitted, it defaults to `0`.

If your mapping file is missing keys for a new schematic, the tool will add the missing keys and ask you to fill them in.

## Example blockmap.json

Here's an example of how this might look for an actual build:

```json
{
  "minecraft:air": "0",
  "minecraft:stone": "1",
  "minecraft:blackstone": "3056",
  "minecraft:light_gray_concrete": "2905:8",
  "minecraft:black_stained_glass": "95:15",
  "minecraft:polished_blackstone": "3056:1",
  "minecraft:smooth_stone": "2895",
  "minecraft:white_concrete": "2905",
  "minecraft:grass_block[snowy=false]": "2",
  "minecraft:sea_lantern": "1385"
}
```

## Output Behavior

`schematica` writer:

- writes standard `.schematic` output by default
- supports `--useSchemPlus` for higher block ID support
  - **Note: If you use the schemplus format, you must also enable it in your Schematica configuration file.**

`worldedit` writer:

- writes `.schematic` output
- uses WorldEdit-style packing
- does not support `--useSchemPlus`

## Typical Workflow

1. Run the converter on a `.litematic` file.
2. Let it generate `blockmap.json` if needed.
3. Fill in any missing mappings.
4. Run the converter again.
5. Import the generated `.schematic` or `.schemplus` file into your target tool.

---
<sub>This project is licensed under GPL v3.0</sub>