# Balance integrado: Simpson y límites conservados

Productor/protocolo congelados en `3bebc4b`, el 2 de octubre de 2026.
Se integran 496 últimos intervalos reconstruidos y un soporte completo
mixto, sin solves nuevos del circuito. Parámetros y leyes siguen siendo
condicionales/sintéticos; no se publica una trayectoria nueva.

Los 496 intervalos pasan precisión Decimal80/100, identidades de balance,
conservación y cierre de la carga constitutiva en todos los niveles
8/16/32/64. Sus dominios exponenciales completos se certifican por
Bernstein. Las diferencias Qp frente a Q(v) se conservan sin sustituir
las memorias originales. Q(v) consistente no elimina el residual estático.

El contraste estático final **32/64 pasa 125/496** y conserva **371 fallos**.
La comparación relativa se aplica también a componentes pequeñas y se
mantiene intacta. El máximo error normalizado de 32/64 es 140,129 en ataque.
Los 105 residuales medios bajo 10 pA y los 391 restantes son observaciones
del diagnóstico de 64 subintervalos, sin admisión de error de cuadratura.
Máximo medio en ataque: 3,52891693342e-8 A (dos subpasos),
8,81308470189e-9 A (cuatro). No se convierten en cotas de voltaje.

El soporte mixto se integra en dos piezas y un puente de carga constitutiva
por extremos del bracket. El cierre de carga pasa en los cuatro niveles.
El contraste estático de 8 subintervalos falla (12,6909 normalizado);
16/32 frente a 64 pasan (0,790275 y 0,0464868). El contraste final del
soporte pasa. El puente no requiere elegir una raíz física ni suavizar
la ley del knee.

## Validación y fallos

La primera suite falla la comparación independiente Gauss4/Simpson64,
prefijo de dos subpasos, índice 2: error normalizado 7,29116. Además, un
testigo de polinomio constante evalúa Decimal 0^0 y produce InvalidOperation.
Se conserva la fuente completa, salida y SHA de ese intento (13,85923 s).

El testigo usa explícitamente el valor constante uno. La comprobación
Simpson queda como control negativo y registra las 24 comparaciones de
Gauss4 seleccionadas, con todas las discrepancias. No se cambian datos,
cuadraturas ni gates para convertir Simpson en una integral admitida.
Cinco pruebas pasan en el segundo intento (34,5697805 s); todos los hashes
de entradas permanecen idénticos dentro de cada intento. Sólo cambia la
fuente de prueba identificada; se archivará su versión anterior por recibo.

La variante [Gauss declarada](BIESTABLE_BALANCE_GAUSS_PROTOCOLO.md) estudia
4/8/16 puntos sobre el mismo problema. El informe Simpson permanece.

[Datos](../evidence/loudness_latch_bdf_static_precision_charge_balance.json.gz):
18.679.995 bytes; SHA comprimido
`67da2085ab205b381735ec15d70279e1b2e4496259baba8270f44b26b462a253`;
SHA canónico
`6d1402e750597b4af3779a307dc430e2922ba5a36576cea51ea3e13e366f1ddd`.
El [recibo](../evidence/loudness_latch_bdf_static_precision_charge_balance_validation.json)
conserva ambos intentos y los controles negativos.

Los intervalos seleccionados no cubren de forma contigua el recorrido
desde DC. El gate global de 1 mV, física, audio y deadline siguen abiertos.
