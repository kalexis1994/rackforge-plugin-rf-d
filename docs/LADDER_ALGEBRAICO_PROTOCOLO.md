# Reconstrucción algebraica local del ladder

## Objetivo, procedencia y dominio

Derivar del grafo admitido una reconstrucción local exacta antes de insertarla
en la voz. Fuente SVC-9 p.13/Fig.9-11, revisión documental CA3046 y tarjetas
nominales vigentes; las leyes son las de `prepared_audio_stamp.rs`, sin cambio
de beta finita, BE/BC o exponenciales. No hay identificación de una unidad
física. Este ensayo local no acredita trayectoria global, costo o RT.

Antes de ejecutar, gates: corriente 20 pA, reconstrucción 2 nV; residual del
solve local 1 pA y corrección 2 nV. Jacobiano 2 nS+2e-5·abs(FD), diferencias
centrales de 1 µV. Escenarios: 48 etapas admitidas, 24 pares de ROOT de los
dos perfiles directos 64/32 µs de `hybrid_direct_native03.json`, sin nuevas
trayectorias o sonido. Solve de siete variables: máximo 80 Newton/24 búsquedas
por Newton; pivote escalado mínimo relativo 1e-12. Estado físico compensado
HIGH/LOW, finito, canónico y dentro de ±40 V. Las coordenadas diferenciales
pueden alcanzar ±80 V siempre que su reconstrucción física sea válida.

Preparación inmutable por receta: Is, BF, BR y temperatura positivos finitos;
R61=200 o 200000 Ω, R30 entre 330 y 1330 Ω. La prueba de precisión se limita
a la tarjeta nominal Is=1e-14 A, BF=100, BR=5, T=298,15 K, R61=200 Ω y
R30=830 Ω; aceptar parámetros no demuestra precisión en otras recetas.
Masa evaluada con el mismo dominio de h de la cadena (4 ticks a 1 ms).

## Ledger antes de derivar

Nodos físicos 0–15, numeración del audio de 66 nodos. Puertos: 5 TAIL,
6/7 entradas, 11/15 salidas. Alimentaciones: +10 V y masa fija.

| Propietario | Componentes / incidencias | Unidades y tratamiento |
| --- | --- | --- |
| Local DC | +10→0:220; 0→1→2→3→4:150 cada tramo; 4→masa:R61; 4→6:470; 4→7:R30 | Ω; todas las reacciones conservadas |
| Local DC | NPN (B,C,E): (6,8,5), (3,9,8), (2,10,9), (1,11,10), (0,+10,11), (7,12,5), (3,13,12), (2,14,13), (1,15,14), (0,+10,15) | A/S; misma ley original |
| Local carga | (8,12), (9,13), (10,14), (11,15):68 nF | Cuatro incidencias, última entre salidas |
| Local carga | (4,masa):220 µF | Memoria de bias retenida explícitamente |
| Padre | (6,BUS66):10 µF; (16,11)/(17,15):0,22 µF | Acoplamiento de entrada y recuperación una vez |
| Padre | (C10_LEFT67,7):10 µF en la rama nominal | Mantener también conmutación/alias original de la cadena |
| Padre | TAIL/contornos, recuperación, VCA, alimentación restante | Ninguna carga o control eliminado |

**Corrección del plan previo:** también existe el capacitor de bias de
220 µF. Omitirlo convertiría una memoria en restricción algebraica. La
partición correcta tiene cuatro memorias internas y siete incógnitas
algebraicas; el capacitor entre salidas es una incidencia de puertos.

## Coordenadas y ecuaciones

`z=[V0,V1,V2,V3,V8,V9,V10]` (7 V algebraicos).
`y=[V8−V12,V9−V13,V10−V14,V4,V5,V6,V7,V11,V15]` (9 V retenidos).
Reconstruir V12=V8−y0, V13=V9−y1, V14=V10−y2 con pares compensados;
los demás nodos se copian. Es una transformación invertible `x=T[z,y]`.

Para residual físico F en A, el residual transformado es `TᵀF`:
las filas z son `[F0,F1,F2,F3,F8+F12,F9+F13,F10+F14]` y no tienen carga.
Las reacciones y son `[-F12,-F13,-F14,F4,F5,F6,F7,F11,F15]`.
Las tres primeras son fuerzas conjugadas de voltajes diferenciales;
no se suman como si fueran nueve terminales de KCL. La conservación
de corriente usa las seis últimas más las fuentes fijas.

Transformar J en `TᵀJT`, resolver `Fz=0`, y derivar
`dz/dy=−Jzz⁻¹Jzy`, `Jreacción=Jyy−Jyz Jzz⁻¹Jzy` (S).
Cada columna de fuentes usa la misma reconstrucción implícita. El factor
pertenece a ese Jacobiano; no persiste entre estados, h o recetas.
Los valores locales se devuelven sólo al concluir; un rechazo no modifica
el estado del llamador. No hay asignaciones de heap, IO o locks en el kernel.

## Carga e historial

Usar el incremento físico HIGH/LOW original, no diferencias de endpoints
redondeados. Las tres diferencias internas aportan `68nF·Δd/h`, el bias
`220µF·ΔV4/h`. Entre salidas: `±68nF·Δ(V11−V15)/h`.
La masa y tiene esos tres diagonales, el diagonal de bias, y la incidencia
2×2 de salidas. La carga de masa fija es menos la de bias. Las filas z
de `TᵀΔQ/h` y de la masa transformada son cero. El historial anterior y
las etapas de Radau seguirán siendo entradas del integrador global.

## Comprobaciones y límites de admisión

Contrastar todos los residuos/J locales con las primeras 16 filas del
audio completo; comprobar la ausencia de enlaces DC externos en esas filas.
Reconstruir cada etapa y resolver desde su semilla y perturbaciones ±1/±10 mV.
Contrastar nueve columnas FD de reacciones, reconstrucción y fuentes en
etapas seleccionadas. Comprobar conservación, cinco incidencias de carga,
masa y ledger de acoplamientos del padre contra las fuentes admitidas.
Probar parámetros/estado/h/presupuesto no válidos, singularidad, overflow,
rechazo y recuperación exacta. Guardar fuentes, input y replay sin modificar
en cada fallo antes de corregir o retirar el área temporal única.

Admisión local exige estos gates. La siguiente integración global debe
conservar las ecuaciones de 118 nodos, ambas etapas, trayectoria 40–100 ms,
J7/C2/C5/BUS/cargas, rechazo atómico y heap. Sólo después medir con control
fresco y gate de costo 0,90. El motor directo sigue activo hasta entonces.
