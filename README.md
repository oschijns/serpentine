# SnakeR

Build system based on **SCons** and **Jinja2** for retro console toolchains.


### Initialize

Create a python virtual environment
```sh
python3 -m venv builder/env
```


Activate the environment
```sh
source builder/env/bin/activate
```

If you are using **Csh**
```sh
source builder/env/bin/activate.csh
```

If you are using **Fish**
```sh
source builder/env/bin/activate.fish
```


Once in the environment, you can install dependencies
```sh
pip3 install -r builder/requirements.txt
```

You can also install the dependencies for the *music-tool*.
```sh
cd music-tool
npm install
cd ..
```


To build the *ROM*, simply run *SCons* at the root of the project.
```sh
scons
```

Then you can try the generated *ROM* with any emulator (e.g. *Ares*)
```
ares test.nes
```

