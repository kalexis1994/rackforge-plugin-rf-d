# RF-D working rules

Follow RACE at `../rackforge-race/` for circuit modeling, evidence, capture, and promotion gates. This repository owns RF-D's sound engine, state, tests, UI, and package; RackForge owns host routing and lifecycle.

- Keep the Model D documentary revision explicit in `docs/OBJETIVO.md`. There is no physical reference unit for this project. Do not silently combine vintage boards or 2016/2022 reissues.
- For every audible constant or algorithm, record source ID/page or capture, electrical derivation, units, valid domain, uncertainty, and a regression in the relevant block documentation.
- Distinguish controls, topology, numerical transfer, and external vintage audio in `docs/MATRIZ_DE_FIDELIDAD.md`. A working renderer is not evidence of fidelity. Follow `docs/VALIDACION_SIN_HARDWARE.md` for allowable claims.
- Store downloaded manuals, schematics, photos, ROMs, recordings, and other private evidence only in ignored local directories. Never put them in Git or the package.
- JSON restores tuples as lists. Compare packed/restored evidence with canonical JSON bytes or unpacked typed states; never use raw Python container equality for that gate. Preserve failed validation attempts and keep numerical gates unchanged when correcting a serialization adapter.
- Keep original monophonic behavior as the sound target. Mark host presets, MIDI mappings, and other stage conveniences as RackForge extensions.
- In audio processing, avoid allocation, file access, locks, logging, and serialization. Measure both audio differences and deadlines before admitting optimizations.
