# Mezclador ON con memoria de C27: resultados

El [puerto nativo](../crates/rf-d-circuit/src/mixer_c27.rs) elimina BUS
entre la red ON nominal y C27 ideal de 10 µF. Entrega las seis corrientes
y su Jacobiano para OSC1/2/3, NOISE, EXT y BASE_Q29, la tensión de BUS y
la próxima memoria `BASE−BUS`. El caller confirma esta memoria sólo al
aceptar la solución conjunta del filtro; cada trial conserva la historia.
Fuentes, unidades, hipótesis y gates se fijaron en el
[protocolo previo](MEZCLADOR_C27_PROTOCOLO.md).

## Resultados ejecutados

El [oráculo nodal](../tools/mixer_c27_vectors.py) usa Decimal de 80 dígitos
con resistores originales, cursores interiores, C27 y fuente de historia.
Sus [837 vectores](../evidence/voice_mixer_c27_vectors01.json) cubren 31
conjuntos ON, nueve perfiles de α y tres dt. No calcula la reducción Rust.

| Magnitud | Error máximo | Gate absoluto |
|---|---:|---:|
| BUS, Δv y próxima memoria | 4,440892098500626×10⁻¹⁶ V | 10⁻¹⁰ V |
| Corrientes de seis terminales | 1,084202172485504×10⁻¹⁹ A | 10⁻¹³ A |
| Jacobiano 6×6 | 5,421010862427522×10⁻²⁰ S | 10⁻¹² S |

El [intento nativo](../evidence/voice_mixer_c27_native_attempt01.json)
compila la biblioteca completa y ejecuta cuatro tests de puerto más uno
aislado de heap. Además del oráculo: tangentes por diferencias simétricas,
simetría/pasividad, 64 pasos con historia confirmada, repetición de trials
sin confirmar, identidad de energía/disipación de Euler y rechazo de
entradas fuera del dominio. **10 000 evaluaciones sin asignaciones**.
Compilación directa con rustc, sin cache Cargo nuevo; tres binarios
privados conservados por hash. No se volvieron a ejecutar tests heredados.

La [QA](../evidence/voice_mixer_c27_tests01.json) conserva 173 controles
anteriores por identidad y añade cinco ejecutados: **178 cubiertos**.
Sólo se agrega un export de módulo al lib anterior; el mezclador ON y
todos los algoritmos anteriores permanecen idénticos. Las reglas LF de
los tres nuevos Rust y bytes del fixture quedan explícitas.

## Alcance y siguiente paso

Admitido: **reducción de la red ON con C27 nominal y carga conservada**.
El puerto puede aportar la corriente a la ecuación BASE_Q29 del solver;
todavía falta insertarlo en su sistema conjunto y contrastar la trayectoria
hasta la salida. Las fuentes de tensión aquí son impuestas: también falta
cerrar sus impedancias, los contactos OFF y taper. No se mide el transistor
de entrada ni se cambia R61. No hay fidelidad física, audio nuevo o admisión
de tiempo real.

La campaña SPICE monolítica de 350 ms se inició tras pasar un nuevo
[preflight serial](../evidence/voice_serial_preflight02.json) con XZ y un
margen de 2 GiB. Conserva sus fuentes, executable, init y gates congelados;
este avance nativo no modifica el ensayo en curso. Su resultado completo
se publicará con una auditoría separada, sin contar prefijos como cobertura.
