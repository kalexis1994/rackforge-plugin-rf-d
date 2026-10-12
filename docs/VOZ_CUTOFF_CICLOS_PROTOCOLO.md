# Continuación del cutoff abierto hasta dos resets

2026-10-12, antes de medir. Misma escena CA3046/cutoff1/RANGE0,1/R61=200 Ω
del [banco temporal](VOZ_CUTOFF_TEMPORAL_RESULTADOS.md). Se cargan sus
checkpoints finales propios a250 µs, con todos los floats HIGH/LOW,
elapsed/propuesta/settings. Los parámetros se reconstruyen con cutoff1.
No recondicionar ni sustituir cargas por el DC del panel nuevo.

Dos calendarios propios, máximos125/62,5 ns; continuar250 µs→5,25 ms.
Guardar anclas comunes cada250 µs, ambos brackets de reset x43=−2,
control C18/cola/KCL/integrales, traza completa y final. Se heredan el
prefijo0→250 µs y sus auditorías por identidad, sin volver a simularlo.
El primer checkpoint nuevo debe ser idéntico por bytes al final heredado.
El llamador elimina el solve startup de VCO que la fábrica scene anterior
calculaba pero descartaba; conserva parámetros y devuelve un estado dummy
que sigue sin utilizarse. Ninguna nueva raíz inicial se aplica al recorrido.

Presupuesto: dos procesos de laboratorio, stack32 MiB cada uno, RAM
inicial≥1 GiB/CPU≥2; compile120 s, perfil2400 s/60000 intervalos,
éxito2600 s, administrativo3200 s, auditor300 s. Disco reservado1 GiB,
estimación64 MiB, vigilancia250 ms. Rechazo: checkpoint exacto y replay
del advance fallido con cutoff1 antes de cambiar fuentes/gates.

Gates anteriores de ecuaciones/corrección, LTE, KCL, balances y comparación
al mismo reloj se conservan. Dos restores nuevos por perfil:250 µs y
2,5 ms. Auditor independiente en primer intervalo,20 anclas y dos resets:
23 selecciones por perfil,138 candidatos/55200 ecuaciones,92 corrientes
y46 LTE. Verificar los eventos por pertenencia a medios pasos seleccionados;
Decimal100 observa su fase/tiempo y deriva de18 ramas/J7, sin exigir
periodicidad. Estimar periodo con cada calendario y comparar≤1 cent.

El ledger C18 continúa desde su nuevo estado inicial; al unir prefijo y
continuación, sumar integrales sin duplicar el endpoint. C1/C27 y medias
Radau se verifican por segmento y recorrido completo. Medir J7 y BUS en
el intervalo entre resets. No interpretar una ventana finita como nivel
estacionario ni54× como factor garantizado de una onda grande.

## Escucha opcional del intervalo observado

Sólo después de admitir ambas escenas completas. Repetir el intervalo
J7 entre sus dos cruces del perfil62,5 ns mediante el renderer Fourier
ya contrastado: integrales exactas del interpolante lineal por tramos,
omitir DC y armónicos por encima0,45 Fs.48 kHz, PCM16 mono,2 s,
fades10 ms. Escala fija0,1 V/full scale de **inspección** (80× respecto
del adaptador8 V/FS). No normalización individual, no clipping, no señal
analítica añadida. Publicar voltios/DC retirado/ganancia/PCM/WAV por bytes.
No es escala de producto ni2 s de simulación del circuito.

Gate previo para repetir: discontinuidad J7 entre fronteras de fase≤1 %
del rango del intervalo en ambos perfiles, y diferencia RMS de armónicos
alineados en fase≤1 % de RMS del perfil fino +1e−7 V. Si no pasa, informar
escucha no admitida y conservar la escena/deriva sin relajar el criterio.
No prueba periodicidad asintótica, timbre vintage, contornos o RT.
