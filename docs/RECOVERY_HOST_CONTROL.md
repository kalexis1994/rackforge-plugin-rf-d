# Control de igual longitud para Steam WASAPI

2026-11-07. El banco Steam con DSP de 4800 devoluciones registró 572
intervalos mayores que 1.5 veces el plazo. El control original tenía
1200 devoluciones. Repetir el control silencioso durante 4800 en el
mismo endpoint y con la misma configuración y política de hilo.
Conservar la primera medición y las filas completas.

Comparar los intervalos por tamaño efectivo y calcular cuánto tiempo
transcurrió entre el final de la sección cronometrada anterior y el
inicio de la siguiente. Las campañas son secuenciales. Su diferencia
no atribuye causalidad al DSP ni identifica pérdidas del dispositivo.
