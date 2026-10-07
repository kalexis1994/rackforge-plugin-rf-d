# Entrada Q29/C27 directa y puerto cargado

2026-10-07. Cadena nominal de 66 nodos ON/C27→ladder→VCAs→J7.
[Protocolo previo](MEZCLADOR_DIRECTO_PROTOCOLO.md). La fila BASE_Q29 se
construye con R54, corriente de base Q29 y puerto C27; se evita restar
la gran conductancia C27/dt. Los módulos anteriores y `circuit66` siguen
idénticos; se agregan dos exports públicos.

## Resultados de producción

[Oráculo independiente](../evidence/voice_mixer_direct_vectors01.json):
12 escenas, dos R61, una/cinco rutas ON y dt=500/250/125 ns. BUS y cursores
explícitos, 67/71 incógnitas, DC/historia propios. 192 pasos, todas las
memorias y seis corrientes; fuentes impuestas, α=0.5.

| Medida | Máximo observado | Gate |
| --- | ---: | ---: |
| Nodos de la trayectoria | 1.0134082462e−9 V | 1e−6 V |
| Corrientes de la trayectoria | 1.2650216775e−13 A | 1e−9 A |
| Nodos, 64 pasos de zona compartida a 48 kHz | 1.0124718841e−9 V | 1e−6 V |
| Corrientes, zona compartida | 2.2426671116e−15 A | 1e−9 A |
| Admitancia de cinco fuentes | 4.2515454238e−12 S | 1e−8 + 1e−3·abs(FD) S |
| Gradientes de nodos | 2.7982867872e−7 V/V | 1e−6 + 1e−3·abs(FD) V/V |

El [recibo de producción](../evidence/voice_mixer_direct_native01.json)
registra ocho tests ejecutados sobre el módulo público: trayectoria,
Jacobiano completo, fallos sin publicar estado, zona compartida, heap de
cadena, tangentes cargadas, fuentes omitidas/fallo de puerto y heap de puerto.
KCL <10 pA/corrección <10 nV con los gates anteriores. Se verifican todas
las 66 columnas del Jacobiano en doce estados a historia fija. Las tangentes
usan cinco pares de raíces nodales ±1 mV por estado, sin semillas nativas.

Por cada dt se ejecutan 32 pasos y 16 solves de puerto con **cero asignaciones**,
constructor fuera del conteo. Binarios y biblioteca permanecen privados,
con compiler, flags, comandos, stdout y hashes conservados. No hubo rechazo
nativo ni necesidad de reparar los datos o gates de este banco.

La [QA final](../evidence/voice_mixer_direct_tests01.json) recompone los
oráculos, verifica binarios, inputs anteriores y los snapshots de portadas.
**193 cubiertas: ocho ejecutadas y 185 heredadas por identidad.** Los
controles heredados no se ejecutan otra vez. La memoria y las corrientes
quedan provisionales hasta que el futuro generador cierre el conjunto.

## Alcance

Los nuevos `mixer_chain66_direct`/`mixer_chain_port_direct` admiten por contrato
**125 ns..1 ms**; se contrastaron las tres resoluciones indicadas y la zona
previa a 48 kHz. No es una cota continua de error en todo el intervalo.
El adaptador anterior conserva 0.5 µs..1 ms. Las leyes físicas, tarjetas,
R61 y demás algoritmos previos se conservan. No se admiten pasos menores,
VCO autónomo, contorno completo, OFF/taper, fidelidad física o deadline RT.

La [campaña larga SPICE](VOZ_SERIAL_CAMPANA_RESULTADOS.md) conserva su
rechazo y cuatro archivos auditados. Este banco no completa sus escenas
ni cambia sus gates. No se produce audio nuevo.

## Próximo bloque

Implementar los dispositivos con carga y estados internos requeridos por
[VCO1 nativo](VCO1_NATIVO_PROTOCOLO.md), luego cerrar convertidor, rampa,
Schmitt/reset, formadores y la cadena con esta carga eléctrica. Conservar
historia fija y confirmación conjunta; contrastar con la referencia acoplada.
