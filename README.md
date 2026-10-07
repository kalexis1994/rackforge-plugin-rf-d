# RF-D

Recreación de circuito del Minimoog Model D clásico para RackForge, bajo
[RACE](https://github.com/kalexis1994/rackforge-race/blob/main/README.md). Primer perfil: placa osciladora CA3046
nominal documentada; [revisión y alcance](docs/OBJETIVO.md). No hay ni habrá
un instrumento físico de referencia. La equivalencia numérica de un modelo
no acredita identidad sonora con una unidad vintage.

## Estado actual — 2026-10-07

| Ruta | Resultado disponible | Alcance pendiente |
|---|---|---|
| VCO1 de referencia | [Circuito funcional, convergencia y calibración](docs/VCO1_RESULTADOS_CIRCUITO.md) | Implementación nativa y carga cerrada con la cadena; osciladores 2/3 |
| Mezclador ON y C27 | [Puerto dinámico con memoria](docs/MEZCLADOR_C27_RESULTADOS.md), 837 casos nodales | OFF, taper e impedancias reales de generadores |
| Entrada→ladder→VCAs→J7 | [Cierre nativo](docs/MEZCLADOR_CADENA_RESULTADOS.md), cuatro escenas/64 pasos independientes | Contornos y generadores todavía impuestos |
| Carga vista por las fuentes | [Cinco corrientes, matriz 5×5 y candidatos provisionales](docs/MEZCLADOR_PUERTO_CARGADO_RESULTADOS.md) | Cerrar VCO real con estas corrientes y tangentes |
| Contorno de volumen | [Puerto C2/reset y cadena cargada](docs/PUERTO_CONTORNO_CADENA_71.md), laboratorio de conmutación | Integración estable del contorno completo y contorno de filtro |
| Voz monolítica SPICE | [Banco corto admitido](docs/VOZ_SEIS_ACTIVO_RESULTADOS.md); extensión serial en ejecución | Nota larga completa con sus tres contrastes |
| Producto | Núcleos y herramientas de laboratorio | Voz nativa completa, recursos, MIDI/host y paquete instalable |

La [QA nativa vigente](evidence/voice_mixer_chain_port_tests01.json) cubre
185 controles: tres tests nuevos ejecutados en el último bloque y 182
heredados por identidad. Los bloques anteriores conservan sus propias
regresiones y límites; ese número no representa 185 nuevas ejecuciones.

La campaña serial de 350 ms comenzó tras pasar el
[preflight02](evidence/voice_serial_preflight02.json). Gear500 y Gear250
se detuvieron a 136,630269 y 150,293268 ms; sus exports están preservados.
Gear125 sigue calculando y Trap125 queda pendiente. Ningún prefijo completa
la nota ni admite los contrastes. No se genera audio nuevo por estos bloques.

## Siguiente trabajo

1. Auditar la campaña serial al terminar: cobertura, archivos, cargas,
   contrastes y decisión; conservar cualquier rechazo.
2. Implementar el VCO nativo con el [puerto cargado](docs/MEZCLADOR_PUERTO_CARGADO_PROTOCOLO.md),
   manteniendo unidades, carga e historia. Primero VCO1 y controles impuestos.
3. Cerrar contornos, controles y fuentes restantes; después comprobar la voz,
   plazos y adaptadores de escucha/host para su alcance declarado.

## Documentación y verificación

- [Contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md).
- [Plan vigente](docs/PLAN.md) y [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
- [Fuentes](docs/FUENTES.md), [revisiones](docs/REVISIONES.md) y
  [validación sin hardware](docs/VALIDACION_SIN_HARDWARE.md).
- [Bloques](docs/BLOQUES.md), [hallazgos](docs/HALLAZGOS.md) y
  [escenas de captura](docs/CAPTURAS.md).

Regresiones públicas de los dos cierres nativos recientes:

```powershell
cargo test --offline --locked -p rf-d-circuit --test mixer_chain66 --test mixer_chain_no_alloc --test mixer_chain_port --test mixer_chain_port_no_alloc
```

Los recibos de producción registran compiler, flags, outputs y hashes.
Sus herramientas preservan intentos: una repetición debe preparar un recibo
nuevo, sin sobrescribir una campaña congelada. Heap cero no prueba RT.

El objetivo musical es una voz mono para bajos, leads y articulación en vivo.
Presets/MIDI y automatización son adaptadores de RackForge; no representan
memoria del instrumento clásico. Aún no hay paquete RF-D instalable ni
admisión de fidelidad física o deadline de la voz.

## Historial y material local

El [historial de esta portada](README_HISTORICO_2026-10-07.md) conserva
exactamente los estados anteriores y sus enlaces. Los
[snapshots](evidence/voice_documentation_snapshot01.json) no cambian código,
modelos, datos o gates; cada resultado histórico conserva su protocolo.

Manuales, esquemas, fuentes originales, WAV y binarios privados se conservan
en directorios locales ignorados. No se incluyen en Git o el paquete.
RF-D no implica afiliación con Moog Music.

La [QA de estas portadas](evidence/voice_documentation_tests01.json) verifica
los snapshots, enlaces e identidad de los 185 controles heredados, sin
volver a ejecutarlos ni cambiar los resultados de la campaña en curso.
