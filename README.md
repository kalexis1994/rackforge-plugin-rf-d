# RF-D

RecreaciÃ³n de circuito del Minimoog Model D clÃ¡sico para RackForge, bajo
[RACE](https://github.com/kalexis1994/rackforge-race/blob/main/README.md). Primer perfil: placa osciladora CA3046
nominal documentada; [revisiÃ³n y alcance](docs/OBJETIVO.md). No hay ni habrÃ¡
un instrumento fÃ­sico de referencia. La equivalencia numÃ©rica de un modelo
no acredita identidad sonora con una unidad vintage.

## Estado actual â€” 2026-10-07

| Ruta | Resultado disponible | Alcance pendiente |
|---|---|---|
| Cargas BE/BC y GS/GD | [Primitiva nativa](docs/VCO_CARGA_JUNTURA_RESULTADOS.md), 1280 vectores y derivadas | Transporte/difusión, binding térmico y dispositivos completos |
| Cargas BE/BC y GS/GD | [Primitiva nativa](docs/VCO_CARGA_JUNTURA_RESULTADOS.md), 1280 vectores y derivadas | Transporte/difusión, binding térmico y dispositivos completos |
| VCO1 de referencia | [Circuito funcional, convergencia y calibraciÃ³n](docs/VCO1_RESULTADOS_CIRCUITO.md) | ImplementaciÃ³n nativa y carga cerrada con la cadena; osciladores 2/3 |
| Mezclador ON y C27 | [Puerto dinÃ¡mico con memoria](docs/MEZCLADOR_C27_RESULTADOS.md), 837 casos nodales | OFF, taper e impedancias reales de generadores |
| Entradaâ†’ladderâ†’VCAsâ†’J7 | [Entrada directa nativa](docs/MEZCLADOR_DIRECTO_RESULTADOS.md), 12 escenas/192 pasos a 500/250/125 ns | Contornos y generadores todavÃ­a impuestos |
| Carga vista por las fuentes | [Puerto directo 5Ã—5 a 125 ns](docs/MEZCLADOR_DIRECTO_RESULTADOS.md), candidatos y tangentes | Cerrar VCO real con estas corrientes y tangentes |
| Contorno de volumen | [Puerto C2/reset y cadena cargada](docs/PUERTO_CONTORNO_CADENA_71.md), laboratorio de conmutaciÃ³n | IntegraciÃ³n estable del contorno completo y contorno de filtro |
| Voz monolÃ­tica SPICE | [Banco corto admitido](docs/VOZ_SEIS_ACTIVO_RESULTADOS.md); [largo rechazado](docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md) | Nota larga completa con sus tres contrastes |
| Producto | NÃºcleos y herramientas de laboratorio | Voz nativa completa, recursos, MIDI/host y paquete instalable |

La [QA nativa vigente](evidence/voice_junction_charge_tests01.json) cubre
193 controles: ocho tests nuevos ejecutados en el Ãºltimo bloque y 185
heredados por identidad. Los bloques anteriores conservan sus propias
regresiones y lÃ­mites; ese nÃºmero no representa 197 nuevas ejecuciones.

La campaÃ±a serial de 350 ms comenzÃ³ tras pasar el
[preflight02](evidence/voice_serial_preflight02.json). Gear500 y Gear250
se detuvieron a 136,630269 y 150,293268 ms; Trap125 a 15,940421 ms.
Gear125 completÃ³ 350 ms. Los cuatro exports quedaron archivados y auditados;
las tres parejas no se midieron por falta de escenas completas. El
[banco largo queda rechazado](docs/VOZ_SERIAL_CAMPANA_RESULTADOS.md). No hay audio nuevo.

## Siguiente trabajo

1. Completar transporte/difusión y estados internos de VCO1; la
   [carga de depleción](docs/VCO_CARGA_JUNTURA_RESULTADOS.md) ya pasó su banco. La
   [entrada directa Q29/C27](docs/MEZCLADOR_DIRECTO_RESULTADOS.md) ya tiene
   contraste a 500/250/125 ns.
2. Implementar [VCO1 nativo](docs/VCO1_NATIVO_PROTOCOLO.md) con el
   [puerto cargado](docs/MEZCLADOR_PUERTO_CARGADO_PROTOCOLO.md), manteniendo carga,
   unidades e historia. Primero VCO1 y controles impuestos.
3. Cerrar contornos, controles y fuentes restantes; despuÃ©s comprobar la voz,
   plazos y adaptadores de escucha/host para su alcance declarado.

## DocumentaciÃ³n y verificaciÃ³n

- [Contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md).
- [Plan vigente](docs/PLAN.md) y [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
- [Fuentes](docs/FUENTES.md), [revisiones](docs/REVISIONES.md) y
  [validaciÃ³n sin hardware](docs/VALIDACION_SIN_HARDWARE.md).
- [Bloques](docs/BLOQUES.md), [hallazgos](docs/HALLAZGOS.md) y
  [escenas de captura](docs/CAPTURAS.md).

Regresiones pÃºblicas de los dos cierres nativos recientes:

```powershell
cargo test --offline --locked -p rf-d-circuit --test junction_charge --test junction_charge_no_alloc
```

Los recibos de producciÃ³n registran compiler, flags, outputs y hashes.
Sus herramientas preservan intentos: una repeticiÃ³n debe preparar un recibo
nuevo, sin sobrescribir una campaÃ±a congelada. Heap cero no prueba RT.

El objetivo musical es una voz mono para bajos, leads y articulaciÃ³n en vivo.
Presets/MIDI y automatizaciÃ³n son adaptadores de RackForge; no representan
memoria del instrumento clÃ¡sico. AÃºn no hay paquete RF-D instalable ni
admisiÃ³n de fidelidad fÃ­sica o deadline de la voz.

## Historial y material local

El [historial de esta portada](README_HISTORICO_2026-10-07.md) conserva
exactamente los estados anteriores y sus enlaces. Los
[snapshots](evidence/voice_documentation_snapshot01.json) no cambian cÃ³digo,
modelos, datos o gates; cada resultado histÃ³rico conserva su protocolo.

Manuales, esquemas, fuentes originales, WAV y binarios privados se conservan
en directorios locales ignorados. No se incluyen en Git o el paquete.
RF-D no implica afiliaciÃ³n con Moog Music.

La [QA de publicaciÃ³n](evidence/voice_junction_charge_tests01.json) verifica
inputs protegidos, nuevos tests y archivos privados. El
[snapshot previo](evidence/voice_junction_charge_documentation01.json) conserva
las tres portadas anteriores por bytes exactos. El rechazo largo sigue vigente.
