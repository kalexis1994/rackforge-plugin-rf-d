# Controles temporales del seguidor cargado

Contrato previo, 2026-10-12, Model D CA3046. Continuar el
[cierre205 admitido](VOZ_SEGUIDOR_RESULTADOS.md) sin cambiar su kernel,
componentes, leyes, Newton o gates. SVC-9 Fig.9-7 p.9, Figs.9-11/9-17
pp.13/19 y tablas7-6/7-8 pp.26–27/30–31; parámetros e incertidumbre
heredados del [puerto C2/reset](PUERTO_CONTORNO_CADENA_71.md).

Semillas: finales propios a2 µs del escenario C2=3,2 V/reset=0,7 V,
h=125/62,5 ns. Extraer410 componentes high/low por bytes del registro
nativo y contrastar con el recibo independiente antes de empaquetar.
Inicio absoluto2753560576 ticks, tick125 ns/65536, cinco tramos de
1048576 ticks (2 µs), duración nueva10 µs. Dos historias propias;
no tomar la memoria de otra resolución ni resolver nuevos DC.

| Tramo | C2 V | Base reset V | Función del escenario |
|---|---:|---:|---|
| 0 | 3,2 | 0,7 | Continuación nominal |
| 1 | 6 | 0,7 | Cambio de C2 |
| 2 | 6 | 0,01 | Cambio de reset |
| 3 | 0,8469345758149237 | 0,01 | Descenso de C2 |
| 4 | 3,2 | 0,7 | Retorno de controles |

Son fuentes ideales discontinuas de laboratorio, no ADSR ni conmutación
causal del biestable. Cada cambio conserva las410 coordenadas por bits,
incluidos los cinco nodos algebraicos como guess. Sólo cambian fuentes
y cursor del calendario. Resolver la transición con la memoria entrante
inmutable y publicar únicamente el candidato aceptado.

Checkpoint3320 bytes: magic RFLCTL01 (8), ticks u64, half_ticks u32,
phase u32, C2/reset f64 y410 f64. Receta fija de los otros parámetros
reconstruida explícitamente. Validar identidad de esquema, calendario,
paso, fuentes, estado finito y pares high/low normalizados. Roundtrip
por bytes y replay desde inicio/mitad de cada tramo; comparar todos los
pares hasta su final, ratios, iteraciones/trials y checkpoint final.
Veinte restores con continuación de tramo; no alegar replay de toda
la escena desde cualquier checkpoint. Rechazar cuatro corrupciones
por perfil: magic, NaN, fase/reloj y fuente discordante.

Archivar primer/último par de cada tramo. Oráculo205 anterior sin cambios:
20 pares/40 candidatos/8200 ecuaciones; corriente desconocida conserva
gate2e−10 V, KCL2e−11 A, corrección1 nA/1 µV. Comparar las tres corrientes
nativas en20 endpoints a1 nA y niveles por valor high+low. Refinamiento
de410 componentes combinados al mismo reloj:2 µV/2 nA en cinco finales,
con comparación adicional de las semillas propias.

Cuadratura Radau3/4,1/4 de DC195 y DC139: C18=100 pF a tierra y
C27=10 µF entre139/BUS12. Exigir ΔQ+∫I_dc=0 por tramo y total a
1 pA·duración. Integrar también corrientes de C2/reset hacia la red
cargada; esas integrales son intercambio con fuentes ideales, no cambio
de carga de un C2 todavía no integrado. Toda cuadratura nativa queda
declarada como tal; las ecuaciones seleccionadas tienen oráculo separado.

Compilación120 s, ejecución300 s, referencia300 s; stack32 MiB, reserva
1 GiB, salida estimada16 MiB. Fallos/inputs/replay conservados antes de
reparar; ningún gate relajado.248 tests Rust heredados por identidad,
sin recompilar biblioteca, nuevos tests Rust, audio, SPICE o admisión RT.
