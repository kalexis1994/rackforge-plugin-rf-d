# Fila equivalente L2/R13/G4 con memoria original

2026-10-06. Experimento local posterior a la
[KCL observada](KCL_741_RESET_RESULTADOS.md). Preservar todos los builds y
recibos anteriores; copiar build/fuente en `newton-build05`.
No cambiar netlists, modelo TI, componentes, calibración, tolerancias o método.

## Transformación declarada

Orientaciones anteriores: `i` hacia 98→17, `g=gR>0`, `gm>0`.
Filas originales, en voltios o amperios según corresponda:

- `rL=v98-v17-req*i-veq`.
- `r17=g*(v17-v16)-i`.
- `r16=-g*(v17-v16)-gm*(v3-v49)`.

Reemplazar sólo la fila de rama por
`rL-req*(r17+r16)-r16/g`:
`v98-v16+(req+1/g)*gm*(v3-v49)=veq`.
Conservar ambas KCL y las contribuciones de corriente de L2 en sus terminales.
Es una operación de fila invertible para g>0; no elimina flujo, dispositivos
o corriente de rama. `req` está en ohm, g/gm en siemens; el nuevo factor es
adimensional. L2 sigue siendo un elemento artificial del macromodelo TI.

Una sola variante: definir `gain=(req+1/g)*gm` y dividir toda la fila y RHS
por `scale=max(1,abs(gain))`. No seleccionar la escala mirando resultados.
En DC req=veq=0; la operación conserva la raíz original. En Gear 1/2 req y
veq proceden del NIintegrate original. No modificar cálculo/publicación de
flujo, dos historiales, estado DC, arranque, truncamiento o recuperación.
Una historia fija no se reconstruye desde una señal ideal.

## Implementación y comprobaciones previas

Cambiar sólo INDsetup/INDload, campos privados y sus bindings KLU. Habilitar
explícitamente por `RF_D_741_REDUCE=1`, sólo para `l.xic3.l2` de esta netlist.
Obtener g/gm de R13/G4 reales y comprobar las conexiones. Crear nuevos
elementos dispersos sólo al habilitar. En modo desactivado conservar matriz
y carga originales. Mantener el runner de 240 s congelado y logging temporal
apagado. Registrar una confirmación de activación en setup.

Probar identidad racional de filas arbitrarias, raíz DC, estados Gear 1/2
con historiales compartidos, escala y signos. La historia aceptada no puede
cambiar al evaluar un candidato rechazado. Las pruebas escalares no admiten
el VCO ni establecen fidelidad física.

## Orden de medición y gates

1. Build nuevo desactivado: BUS cero completo y BUS variable rechazado, con
   todos los tiempos/seis vectores exactamente iguales al baseline anterior.
   Si falla, detener sin medir la variante activa.
2. Variante activa con BUS cero: 40 ms completos; primer punto DC de cinco
   voltajes ≤1 µV y corriente de puerto ≤1 pA frente al baseline. Grilla
   absoluta 0..40 ms de 5 µs, máximo de los cinco voltajes ≤5 mV, frecuencia
   ≤1 cent, igual cantidad de cruces de reset de rampa a −2 V y máximo
   desfase ≤10 ns. Sin realinear, normalizar ni recortar el primer reset.
   Frecuencia medida con cruces a partir de 5 ms. Si falla, conservar y parar.
3. Sólo si pasa el control, medir BUS variable completo 40 ms. Un prefijo,
   otro reloj de fallo o más iteraciones no admiten la trayectoria.

Auditar bytes de fuente/build/runtime/binario antes/después, la identidad de
decks salvo ruta de export y bandera de ejecución, y todos los rechazos.
No transferir automáticamente el resultado al ejecutable oficial. Ni esta
reducción ni el logging constituyen una ruta de audio o un benchmark RT.
Si pasa BUS variable, todavía cerrar R45/contorno, refinamiento y contraste
entre builds antes de promoción. Si falla, no ajustar escalas o tolerancias.
