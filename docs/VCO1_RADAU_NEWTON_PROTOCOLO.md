# Rechazo Newton Radau: repetición local y criterio de búsqueda

Antes de medir. Conservar banco03 y export125 detenidos a12,171591857910155 ms,
6381419552 ticks, último estado hi/lo completo. Caso nominal anterior, tarjetas,
compiler y kernel inalterados. Repetir sólo full(8 ticks), mid(4), end(4),
y tamaños full16/32 ticks desde esa historia; no relanzar el banco30 ms.
Guardar comandos, stdout/stderr y replay por bytes del runner original.
Instrumentar después la copia privada de Newton con ratios por iteración:
residual, corrección y fila máxima. No inferir LTE del mensaje que agrupa
fallos no lineales; una raíz no aceptada no tiene error temporal publicado.

Resolver los tres pares full/mid/end por Decimal100 desde historia, sin
semilla nativa. Para end usar la raíz mid independiente. Reusar gates
anteriores para raíces, retorno/suelo e identidades de puerto. Diagnosticar
si existen raíces y el error full−end satisface2 µV/2 nA en todas134 filas.

Si la búsqueda basada en corrección se estanca, probar una copia distinta
con la misma dirección Newton y Armijo1e−4 sobre el residual normalizado;
64 iteraciones/24 halvings y todos los gates anteriores sin cambios.
No suprimir estados, ajustar física o ampliar tolerancias. Capturar cada
método original/replay y contrastar raíces con Decimal100 antes de continuar.
La recuperación de un intervalo admite sólo ese intervalo. Una continuación
futura conserva el prefijo125 por bytes y checkpoint, con protocolo propio,
y debe completar periodicidad/refinamiento bajo los gates congelados.
