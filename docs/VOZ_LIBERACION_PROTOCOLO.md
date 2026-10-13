# Continuación de liberación y observación de conmutación

2026-10-13, base8110b38, antes de medir. Proteger3473 fuentes/8070 privados.
Continuar cada final ON propio1/2 µs de20.442→28.442 ms:8 ms adicionales,
12 ms en total desde KEY0/contactoabierto. Misma rlib, circuito229, controles,
fuentes y cargas. No reiniciar CV, cargas, historia o propuesta4096 ticks.

## Seam y calendario

Leer final3720 bytes RFHLD001 del ejemplo previo; validar clock, fase2,
decayON, KEY0, contactoabierto, representación y settings. Convertir sólo
magic aRFREL001 y etiqueta de receta a fase0; confirmar todos los otros bytes.
La etiqueta no es una fase ADSR física. Restaurar con Engine público y scratch
propio, sin aplicar un nuevo gatillo. I/O y serialización en caller offline.
Cortes cada.3 ms y final8 ms:27 targets,28 estados incluyendo el inicial.

Hasta3 probes de16 accepted por checkpoint inicial/interior/reset o transición,
sin acumular Accepted. Comparar Pair, observaciones y checkpoint por bits.
Cuatro corrupciones y destino inválido por perfil; errores preservan estado.
El rechazo de presupuesto del motor se hereda de la API anterior sin repetir
un estímulo artificial. Sin heap, stack máximo o deadline medidos de nuevo.

## Observaciones y gates

Selected triples al inicio/final, resets y accepted que contengan cruce de
VQ25c−VQ15c por0 o dC2/dt de positivo a no positivo. Son observaciones del
estado, no instrucciones que cambien el circuito o elijan otra raíz.
Derivada Radau final: (−4.5ΔC2stage1+2.5ΔC2stage2)/h. Inicial derivada inferida
de la KCL estática propia, sin imponerla al solver. Export RFRELFX1 con
u64tick+7f64[C2,dC2/dt,Iattack,Idecay,Ifollower,VQ25c−VQ15c,VQ20c].

Para decayON, C2 sólo conecta PANEL_R13(10 kΩ), PANEL_R16(100 kΩ) y R16deplaca
(10 kΩ); C2=10 µF a masa. Grafo original/SVC-9 p9/p19, mismo punto eléctrico
nominal que la receta previa, sin mapa de perilla inventado. Corrientes:

```text
Iattack=(V208−V205)/10000
Idecay=(V211−V205)/100000
Ifollower=(V205−V200)/10000
dC2/dt=(Iattack+Idecay−Ifollower)/10e−6
```

Auditor recomputa componentes con HIGH/LOW Decimal100 en las selecciones y
contrasta todos los records de flux/derivada con la suma de corrientes,
≤2e−6 V/s (20 pA/C2). No es una medida de todos los voltajes de ramas entre
selecciones. Grafo original/FD y cargas de juntura:458 ecuaciones por par,
LTE independiente; balances orientados de nueve memorias por continuación
y unidos con la trayectoria previa, gate1 pA·duración.

28 relojes comunes con229 estados: gate2 µV/2 nA original. Resets iguales y
brackets refinados≤10 ns. Cruces de biestable y pendiente: comparar número,
sentido y tiempos interpolados entre1/2 µs≤100 ns, conservando anchura del
bracket y definición. Ese margen específico de observación no cambia el
gate global de estado, LTE o los10 ns de resets del oscilador. Si no ocurre
la transición en8 ms, documentar ausencia; no cambiar raíz o estímulos.

## Contraste documental y escucha

Revisar visualmente SVC-204D PDF pp13–14 y SVC-9 p9: C4 acopla el pulso
hacia Q25; R36/CR8 llevan el reset hacia Q15. Descripción de servicio señala
reset/off tras liberar y operación equivalente del contorno de volumen.
Conservar diferencias de designadores del texto/esquema y candidatos BOM.
La revisión define la interpretación a comprobar; no identifica Is/β,
capacitancias de dispositivo ni tiempo de una unidad física.

Unir sólo después de verificar seam exacto, omitiendo la muestra duplicada.
20.004 ms de circuito propio total; WAV nativos20 ms/960 frames a48 kHz,
sinc18 kHz/Blackman,0.01 V/FS, sin loop/DC removal/normalización/fades.
Audio1/2 µs≤2 µV/7 LSB; cuadratura8/16≤.25 LSB/1 LSB y PCM completo.
Sin microscopio o repetición nuevos en este bloque. Un fragmento20 ms sigue
siendo corto y no implica voz completa o fidelidad física.

Ejemplo compile≤120 s; dos perfiles≤1590 s, guard1500 s, campaña≤3300 s.
Oráculo≤600 s; disco nuevo, incluidos PDFs/imágenes usados,≤96 MiB;
reserva1 GiB, stack experimental32 MiB. Preservar falla/replay antes de
reparar. Biblioteca, cache Cargo y SPICE sin cambios;255 tests Rust y dos
definiciones Python heredadas por identidad, nuevos checks de integración
sólo para riesgos de seam/observador/continuación.
