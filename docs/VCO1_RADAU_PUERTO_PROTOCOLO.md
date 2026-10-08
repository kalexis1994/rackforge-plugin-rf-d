# Reconstrucción del aporte derivativo en ambas etapas Radau

Declarado antes de medir. Releer los bancos Radau01 y continuación01 completos, sin repetir las campañas. Cada par de etapas usa su historia entrante y h originales; en los tríos end la historia Decimal100 proviene de mid. Reevaluar F_i+Σ B_ij·ΔQ_j/h, corrección de las 268 ecuaciones, KCL/retorno y gates independientes anteriores. Contrastar la candidata nativa de cada etapa frente a Decimal100, todos los nodos/ramas con gates2e−7 V/2e−10 A; no usar sus raíces como nuevas semillas.

Para ambos 741 y cada etapa i: base Q2=p+_i+EOS−R13·iL2_i−L2/h·Σ_j B_ij·(iL2_j−iL2_0). Verificar también iL2_i=−G4·u_i, leyendo constantes de la tarjeta original. Gate de identidad1e−11 V y2e−14 A, no cambia gates previos de solve/LTE. Guardar aportes estáticos/dinámicos y diferencias full−end de IC3, sin seleccionar etapa o nodo después de observar. Reconstrucción algebraica sólo local; no error global de waveform.

Verificar R(z) por solución racional de (I−zA)k=1 para z=0,−1,−10,−100,−4000,−1000000 frente a la expresión publicada; condiciones A·c=c²/2 y orden3 por fracciones exactas. PDF primario privado por hash. No volver a medir eigenmodos o certificar estabilidad del circuito por este problema escalar. Conservar recibos/privados anteriores, fuentes/hash antes/después; cero nuevos SPICE/audio y tests Rust.
