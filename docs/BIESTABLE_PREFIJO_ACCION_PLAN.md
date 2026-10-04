# Próximo bloque: prolongar el prefijo con acciones dirigidas

El [cuarto intervalo](BIESTABLE_ACCION_RESIDUAL_RESULTADOS.md) dispone
de dos certificados aceptados. Declarar como fuente del próximo ensayo
la variante secundaria **[radio 1 µV, direct_and_memory]**, por sus 22
memorias finales con forcing refinado. Conservar la selección primaria
archivada [1,0]; ambas pertenecen a la misma trayectoria y norma.

## Protocolo que debe congelarse antes de medir

1. Intentar como máximo ocho intervalos adicionales reales desde
   ≈1,5625 µs, rows 4..11 del arranque publicado. Fijar radios, variante,
   orden y parada; no extrapolar recintos del cuarto soporte.
2. Transportar endpoint_anchor+endpoint_forced por cada una de las 22
   coordenadas, con la misma P, pesos y normalización y pico nodal
   entrante. Verificar hashes, reloj absoluto e interfaces completas.
3. Calcular nuevos precondicionadores candidatos y certificar recintos
   medios y tasas para cada intervalo. P retenida no implica disipación
   futura ni cubre otros tiempos. Identificar los costes nuevos.
4. Recalcular RHS firmado, restos uniformes y corrección constitutiva,
   conservando todas las ecuaciones. Aplicar acciones con defecto y cola
   exterior para punto y L1; intersectar con presupuestos anteriores del
   mismo soporte. No suponer cancelación de restos independientes.
5. Recalcular todos los acoplamientos, forcing, ganancias y conversiones
   correspondientes a la norma fija. Usar kernels de endpoint y pico,
   y admitir sólo un cierre nodal estricto, origen incluido.
6. Detener en el primer soporte sin cierre y guardar todos los radios,
   intentos, memorias y duraciones intentada/certificada. Una rama
   rechazada no alimenta otra etapa ni reinicia desde DC.
7. Validar sucesión conocida, cambios de h, matriz variable y acciones
   con restos; reproducir todo el prefijo y ampliar su corpus sin modificar
   evidencias previas. Mantener fuentes y datos congelados entre intentos.

Este plan investiga cobertura de error numérico del circuito nominal.
No sustituye identificación física, comparación sonora o deadline y
no cambia la meta global de 1 mV ni los gates algebraicos históricos.
