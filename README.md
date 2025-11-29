# Serpentine

Set of helper tools for building games for retro consoles.


## Content

The toolbox mostly contains scripts for converting data into formats compatible 
with the target system. Scripts are mostly made in Python so that they can be 
easily used with *Scons* build system and *Jinja2* templating.
Here is a short overview of the tools offered:
- `tileset_packer_spritesheet.py` Converts *Aseprite* animations into a tileset with metadata.
- `tileset_packer_tilemap.py` Converts generic ascii art into a tileset.
- `tileset_palette_variation.py` Generates palette variations for a given tileset so that it can be used in tools like *Tiled*.
- `tileset_to_binary.py` Generates *CHR* file to be embedded in the final *ROM*.
- `jump_trajectory.py` Computes ballistic trajectories based on parameters.
- `serial_to_asm.py` Generates *ASM* syntax for embedding arbitrary data.
- `serial_to_lang.py` Generates *C* or *Wiz* syntax for embedding arbitrary data.
- `text_formatter.py` Converts *ASCII* character set to an arbitrary character set.
- `jinja_build.py` Reads a *Jinja2* template file and generate a source file for the next build step.

Not yet complete
- `famistudio_parser.py` Convert *FamiStudio* text file format into *JSON*.
- `music` For parsing *VGM* files (require *nodeJS*).
- `dialog` For parsing *YarnSpinner* scripts (require *.NET*).



## Initialize

Create a python virtual environment
```sh
python3 -m venv .env
```

Activate the environment
```sh
source .env/bin/activate
```

If you are using **Csh**
```sh
source .env/bin/activate.csh
```

If you are using **Fish**
```sh
source .env/bin/activate.fish
```

Once in the environment, you can install dependencies
```sh
pip3 install -r requirements.txt
```

You can also install the dependencies for the *music*.
```sh
cd music
npm install
cd ..
```

