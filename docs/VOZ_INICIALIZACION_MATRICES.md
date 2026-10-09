# Convenciones del diagnóstico de matrices

2026-10-09, antes de evaluar las matrices exportadas. Gate de Jacobiano
heredado del banco `chain_charge`:1e-8 S+2e-5|FD|. FD central1e-6 V
del oráculo anterior. C compara1e-15 F+1e-12|referencia|. Las18 columnas
de incidencia incluyen C10 y las17 capacitancias anteriores, con BUS66
y C10-left67; ninguna fuente de señal VCO se suma al diagnóstico de cadena.

Para AC sustituir fila BUS por BUS=1 y anular su fila C. El valor1 V
es normalización de ganancia infinitesimal V/V, no una entrada finita
cuya respuesta no lineal se haya simulado. La corriente de esa frontera
queda fuera de la fila reemplazada; las demás filas siguen físicas.

Para polos usar18 coordenadas de carga, T=√D Eᵀ G^-1 E' √D, con E'
sin fila BUS y G con su fila de restricción. Los autovalores son tiempos
τ y polos−1/τ. Reconstruir el autovector exterior y comprobar residuo
en G^-1 C, además del sistema reducido. No contar los50 modos algebraicos
como polos finitos ni inferir estabilidad de toda la trayectoria no lineal.
Residuos relativos<=1e-8, con denominador(||M||₂+|τ|)||v||₂.
Conservar todos los18 autovalores, incluso pequeños, complejos o inestables;
no descartarlos para obtener una estimación de asentamiento favorable.
