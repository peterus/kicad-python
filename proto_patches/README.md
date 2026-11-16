# CopperChat proto patches

KiCad API additions that CopperChat's KiCad build carries (copperchat repo,
`docker/kicad-base/patches/`) but the `kicad` submodule does not have yet. `build.py`
applies the `api/proto/` hunks of every `*.patch` here (in name order) to a copy of the
submodule's protos before generating the Python classes. Drop a patch once KiCad upstream
has the change and the submodule is bumped past it.
