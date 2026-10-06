# Expresión PWL en el puerto de VCO

Los tres [ensayos de relajación](PUERTO_VCO_CONTORNO_PROTOCOLO.md) mantienen
el rechazo. El ensayo 03 elimina el aviso del parser pero el VCO vuelve a
rechazar a aproximadamente 2.277 ms al recibir BUS calculado.

Se congela una sola alternativa de representación: la **misma** polilínea
del puerto VCO se evalúa con `B... V=pwl(time, ...)`, sintaxis documentada
en el [manual ngspice 46, sección 5.1.4, página 110](https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf).
Un contacto de 0 V permite medir la corriente con la orientación anterior.
No añade impedancia, filtrado, capacitancia ni una ley de conmutación.
El puerto de placa 4 conserva su fuente PWL independiente. R45 y las demás
ramas físicas no cambian. La diferencia ensayada es la representación
numérica de una fuente temporal dentro del subproblema VCO.

Se conservan semilla, diez iteraciones máximas, duración 40 ms, paso,
gates de tensión/corriente, contraste monolítico previo y cuatro escenas
posteriores del protocolo anterior. Las expresiones no heredan admisión
de las fuentes independientes. Se preserva todo rechazo y el banco termina
en el primer fallo. No se interpreta un éxito de arranque como cierre.

La hipótesis es que el tratamiento numérico de los puntos de cambio puede
interactuar con reset. Este ensayo puede refutar la utilidad de cambiar la
representación; no atribuye todavía el fallo a un mecanismo específico del
solver ni demuestra equivalencia temporal por igualdad del texto PWL.
