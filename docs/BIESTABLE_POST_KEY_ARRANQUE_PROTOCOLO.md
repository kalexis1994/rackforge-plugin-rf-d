# Protocolo congelado: publicación high+low y prefijo post-KEY

Reutilizar el centro racional y recinto primario post-KEY, sin nuevas
soluciones de DC/evento ni parámetros. Publicar cada potencial y tasa
auxiliar con high=float(valor), low=float(valor-F(high)), normalizando el
par con la rutina histórica. Medir error exacto racional de cada componente.
Conservar los 21 pares de memoria y cuatro cargas de juntura previos.
Reconstruir voltajes, aliases y rails de contour con los high nuevos;
mantener mirrors de condensadores y firma de circuito. No preparar cargas
nuevas desde el voltaje redondeado.

Crear esquema propio post-key-bdf-origin/v1 con identidad del evento y
historia previa. La History existente se usa como contenedor con t=0,
KEY=10 y previous=None; su texto histórico de guard menciona DC, pero
la procedencia externa declara expresamente el límite derecho del evento.
No modificar esa clase ni crear estado anterior BDF2. Las tasas auxiliares
no se usan como historial ni como sustituto de un paso.

## Gates de evento y cota inicial

Restaurar JSON a estado tipado; validar normalización y todos los mirrors.
Evaluar directamente KCL y restricciones sobre high+low más tasas high+low:
sellos intervalares exteriores racionales y contraste Decimal100. Gates
10 pA, 10 fV y exponente <=45, sin clamp. Agregar máximo error exacto de
publicación a la cota de potencial del evento; hacer lo mismo con tasas en
V/s. La caja y pesos de memoria DC permanecen iguales, por identidad.
Declarar anclaje local publicado conocido; no cota temporal global.

## Trayectoria nueva con reloj fijo

Ejecutar exactamente los primeros **512 intervalos** del archivo de reloj
completo compensado. No resolver DC ni re-ejecutar control adaptativo.
Usar CompensatedBdfNetwork y sus presupuestos históricos: primer paso BE,
después BDF2 con dos estados reales, crecimiento máximo de intervalo dos.
No fallback ni reducción de h tras fallo: conservar estado entrante y parar.
Registrar todos los estados, diagnósticos, SHA de historial entrante y reloj.

Aceptar cada paso sólo si pasa publicación histórica KCL 10 pA / ramas
lineales 10 fV, restauración canónica, reloj coincidente e inmutabilidad.
Añadir contraste independiente Decimal100 con derivada BDF de las cargas
almacenadas y potenciales high+low: KCL 10 pA y restricciones lineales
10 fV. Registrar desajuste constitutivo de junturas como diagnóstico en
coordenadas Q/S; no inventar un gate universal nuevo para él.

Comparar nodos y coordenadas de memoria con la trayectoria histórica en
los mismos 512 endpoints. Conservar gate diagnóstico previo 10 nV, todos
los fallos y valores por nodo/memoria. Diferencia entre trayectorias no es
error frente al DAE ideal. No interpolar cruzando el evento ni afirmar
cobertura temporal continua. La duración de error real certificado sigue
en cero y 1 mV global, resto temporal, física, audio y deadline abiertos.

## Validación y procedencia

Congelar helper, productor y protocolo antes de medir. Congelar datos,
tests y validator antes de validar. Probar redondeo de pares con casos
racionales conocidos, conservación de cargas, mirrors completos,
restauración y rechazo de origen adulterado, recinto puntual, sumas de
errores, arranque BE/BDF, linaje íntegro, todos los controles de publicación,
comparación en relojes exactos, fuentes y bytes. Preservar cada intento.
Ampliar el corpus con la evidencia nueva y reconstruir blobs históricos.
