# Evaluación eléctrica e interfaces: cuatro rechazos de costo

**Sigue activo el directo admitido en 7c0524273048099f3fd246562c9b87d7cadffb61.**
Las variantes inline/compact son experimentales y no se promueven. El
[cierre QA](../evidence/hybrid_compact_tests01.json) conserva esa admisión;
passed verifica el cierre, no implica que los candidatos pasen costo.

## Perfil y transformaciones

El [perfil eléctrico](../evidence/hybrid_electrical_profile01.json) separa
FULL/residual, con cuatro replays y timers internos:

| Sección | FULL | Residual |
|---|---:|---:|
| Validación y candidato | 0,1108 s | 0,0706 s |
| Audio y sus proyecciones | 1,4385 s | 0,6121 s |
| Contorno y sus proyecciones | 1,0017 s | 0,5325 s |
| Construcción/transferencia | 1,6897 s | 0,1739 s |

El último timer termina antes del retorno al caller; la tabla no desglosa
todo el costo de la voz ni demuestra copias concretas en el binario.
El benchmark de costo se compila sin esos timers.

| Candidato, techo full 32 µs | Control fresco | Candidato | Ratio |
|---|---:|---:|---:|
| Cinco fronteras inline | 16,1224618 s | 16,2147763 s | 1,005726 |
| Inline y transferencia contigua | 16,2243524 s | 15,7735019 s | 0,972211 |
| Filas compactas DC/masa | 16,2357894 s | 14,8935203 s | 0,917327 |
| Compacto por referencia y constructores inline | 16,1385677 s | 15,9686968 s | 0,989474 |

Mismos 60 ms simulados. **Todos fallan el gate previo ≤0,90**; el mejor
ahorro es 8,27 % en este ensayo. No se modifica el gate ni se adopta
retroactivamente el mejor. Los cuatro conservan fuentes/entrada y replay
sin cambios. Los recibos [inline 01](../evidence/hybrid_inline_native01.json),
[inline 02](../evidence/hybrid_inline_native02.json),
[compact 01](../evidence/hybrid_compact_native01.json) y
[compact 02](../evidence/hybrid_compact_native02.json) fijan sus identidades.
Una medición por candidato no identifica variación estadística o causalidad
de cache, vectorización, copias y layout de stack.

Inline sólo añade anotaciones. Su segundo candidato copia todos los
coeficientes por tramos de la permutación y conserva sumas de filas
compartidas/finitud. El compacto parte del evaluador directo original,
inspecciona toda DC/masa y guarda su unión no nula en filas ascendentes,
con metadatos privados y capacidad 2048. El solver recorre esas filas sin
máscara aprendida. Reconstruye como +0 los ceros omitidos, igual al CSR
anterior; no promete igualdad de signo para cada cero de matrices hijas.
El último ajuste pasa Parts por referencia y expande los constructores.
No cambia ninguna ley eléctrica, constante audible, carga o estado.

## Verificación y alcance

- Inline: 48 etapas, DC/dQ/Jacobiano/masa iguales al directo, FULL/residual
  iguales; 472 columnas FD, máximo 0,000625 del gate. Tres configuraciones
  inválidas, 26 rechazos de etapa y retries exactos en ambos modos.
- Compactos: al menos 48 snapshots de DC/masa reconstruidos, entradas
  no nulas bit a bit y ceros numéricamente iguales. 24 matrices Radau,
  1.336.704 coeficientes bit a bit; 192 direcciones bit a bit al directo y
  máximo 0,972279 del gate frente al monolítico refinado.
- 33 rechazos/retries lineales, 24 enlaces legales restaurados y probe
  de cancelación; 16 RHS de fill-in/swaps/puertos. Overflow de factores y
  capacidad global rechazados con recuperación exacta, además del límite
  de etapa. Máximo de etapa en los fixtures seleccionados: 481 entradas.
- Por candidato: dos trayectorias propias, 962 observaciones, ROOT/GRID/
  SOLVER serializados y estados finales iguales al control. Heap cero,
  ocho replays y diez rechazos atómicos; 99.922 solves/499 refinamientos.
  Newton, backward, estimador, voz completa y refinamiento temporal pasan.
- [Auditoría](../evidence/hybrid_compact_audit01.json) de compact 02:
  5712 filas originales con Amount, ≤0,719007 pA/0,325050 nV. Los endpoints
  de los otros candidatos coinciden con el mismo control; no se produce
  otra trayectoria original independiente.

Dominio nominal CA3046/SVC-204D, 40–100 ms, KEY OFF 75 ms, misma semilla,
perfil VCO, reloj, 118 estados HIGH/LOW y cargas. Fuentes físicas heredadas
SVC-9 pp.9/13/19 y p.10. Sin ampliar arranque/CV o fidelidad física.
Compiler/rlib congelados; sin Cargo, biblioteca, WAV ni inputs privados
nuevos. Un tmp/lab-current vacío; recibos comprimidos, sin nuevas carpetas
de muestras. Recibos de 11,62 MB antes de QA, bajo presupuesto de 16 MiB;
se conservan las 4074 fuentes y 8769 inputs previos.

La cadena sigue offline. La [siguiente reducción](LADDER_REDUCCION_ALGEBRAICA_PLAN.md)
aborda las coordenadas de carga y variables algebraicas del ladder;
estas pruebas de representación quedan como experimentos, sin promoción.
