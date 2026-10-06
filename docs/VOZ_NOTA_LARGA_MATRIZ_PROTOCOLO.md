# Observar el rechazo de la nota larga sin cambiar el solve

2026-10-06. Protocolo fijado antes de preparar/compilar/medir el observador.
El banco de 350 ms sigue en curso. Trap2/125 ns ya conserva un rechazo de
Q7: último estado aceptado a 15.94042072898988 ms, siete cruces de rampa.
Su recibo privado y export SHA `6890b80c903e9154b3ffc79817727c882b362f04bc7cf7fe5372423fe1f0c392`
son la referencia de reproducción. El tiempo del mensaje de aborto está
redondeado; no se presenta como un timestamp exacto de Newton.

## Compilación de observación

Copiar build08 a build09 y conservar RFLinearSolve, rfdd.h, tres correcciones,
factores KLU, publicación y todo código de dispositivos/integración.
Cambiar sólo la selección del observador de matriz ya existente: ventana
15.94035–15.94045 ms, delta ≤1e-17 s, iteraciones 100/101. Limitar a dieciséis
capturas por proceso mediante contador exclusivo de observación. No cambiar
el criterio de convergencia, itl4, pasos, tolerancias o parámetros eléctricos.
Auditar inventario completo: sólo `src/maths/ni/niiter.c` puede diferir.

Usar configuración heredada y GCC identificado por SHA, CFLAGS
`-O2 -g -m64`, LDFLAGS `-m64`, sin fast-math. Guardar comando, log y exit code
tanto si compila como si falla; el build inicial y sus fuentes se conservan.
Revisar espacio para la copia antes de crearla, sin borrar bancos anteriores.

## Orden de gates

1. Con build09 activo y observación apagada, repetir el nominal conjunto
   corto Gear2/500 ns de 40 ms, con el mismo deck salvo export. Exigir las
   191714 filas, reloj y 18 vectores idénticos al build08 admitido. Presupuesto
   fijo 900 s. Ninguna captura todavía. Si falla, detener la observación.
2. Sólo después, activar `RF_D_MATRIX_TRACE=1` en build09 y repetir el deck
   largo Trap2/125 ns, cambiando sólo export. Presupuesto fijo 900 s; el
   objetivo es reproducir el rechazo ya medido, no admitir 350 ms. Exigir
   exactamente las 155680 filas y 18 vectores del export parcial original,
   mismo estado final y mismo mensaje de fallo. Mantener otros observers y
   replay apagados. Un timeout o trayectoria diferente rechaza la captura.
3. Conservar matrices completas, mapa new→old, RHS, x anterior, solve
   original, residual/corrección/pareja en las tres iteraciones y x publicada.
   Agrupar por contexto time/delta/iteración/orden/modo. Capturas antes de
   factorizar y después de resolver no se confunden; declarar gmin efectivo.
   Si se agota el límite de dieciséis, informar cobertura truncada. No afirmar
   que la última captura es el último intento si el contexto no lo demuestra.

La instrumentación es de lectura y salida a log. Que su control sea exacto
no identifica la causa del aborto. Una captura de sistema lineal no es KCL
no lineal independiente ni trayectoria de un nuevo solver. El análisis
posterior comparará raíces precisas sólo de sistemas completos seleccionados,
con publicación original/compensada separadas y ninguna corrección añadida.
El banco largo necesita las cuatro políticas y todos sus gates; este
diagnóstico no autoriza audio ni promueve los prefijos.
