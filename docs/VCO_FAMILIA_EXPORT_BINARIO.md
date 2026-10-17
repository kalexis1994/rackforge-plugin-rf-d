# Salida binaria tras rechazar el tamaño de texto

Decisión previa a nuevas mediciones. El extremo KEYBOARD=-.1/BUS=-.125
supera el límite ASCII de 256 MiB; fallo y replay quedan conservados en
oracle02. No se aumentan presupuesto, tolerancias, pasos o duración.
Se conservan seis ciclos válidos en su pack original sin copiarlos.
El driver retiró el export rechazado antes de guardar su tamaño exacto o
digest: sólo consta el límite inferior por la aserción. No se atribuye a
ese export identidad de bytes o posibilidad de reanálisis. Deck/log y
fuente/replay sí permanecen. Los nuevos exports registran digest/tamaño
antes de comprobar el límite.

Cambiar sólo wrdata por write binario nativo, mismo ngspice admitido y
float64 little endian. Derivar el lector estricto existente por una única
ampliación de unidad: reconocer i(Vsource) como corriente. No cambiar
cabeceras, escalas, orden canónico o conteos. El raw puede ordenar vectores
de otra manera; remapear por nombres explícitos, nunca por posición supuesta.

Control previo: mismo circuito en -.1/-.125, Gear2/125 ns, duración 4 us,
exportar ASCII y binario en el mismo proceso/plot. Exigir valores float64
iguales por bits, incluido cero con signo, conteos y nombres. No es un
nuevo ciclo estacionario o evidencia de fidelidad. Retirar ambos exports
tras digests, layout, métricas y comparación; una sola área temporal.

Después completar dos entrenamientos altos, tres CV reservados y dos
oráculos de método/refinamiento. Reusar exactamente las seis reducciones
y ventanas ya completas, con referencias a su pack y fuentes originales.
No usar el candidato rechazado por columnas. El generador consulta sólo
ocho entrenamientos. Ningún punto reservado entra al ajuste.
