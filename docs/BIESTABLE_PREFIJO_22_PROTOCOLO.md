# Protocolo: prefijo real con transporte de 22 cotas

Modelo nominal documental CA3046 y parámetros sintéticos sin cambios.
Fuente identificada antes de medir: certificado secundario [1,1], radio
1 µV y anclaje refinado del banco de memoria por coordenada. Su trayectoria
ya está probada hasta 390,625 ns. La selección primaria histórica [1,0]
permanece intacta. No escoger otra fuente a partir del resultado nuevo.

Intentar como máximo ocho intervalos adicionales, rows 2..9 del arranque
publicado. Detener en el primer intervalo sin cierre. Radios fijos en orden
0,1; 1; 10 µV, sin cambiarlo después de observar datos. Por radio hay una
sola variante: 21 errores lineales individuales y cuatro junturas en la
misma norma cuadrática P/(2a). Seleccionar el primer radio aceptado.

## Historia, norma y anclaje

Usar tiempos absolutos reales, h exacto y current/previous contiguos.
Reconstruir 94 potenciales y 21 cargas lineales afines; junturas con Q(v),
tasas C(v)*v', conservando la ley. Verificar todas las interfaces, clocks
y hashes de estados. No desplazar tiempos ni fabricar historias o resets.

Transportar las 22 memorias finales: endpoint_anchor+endpoint_forced por
coordenada, sin sustituir las 17 primeras por su máximo. Sólo una prueba
aceptada de error DAE real puede ser fuente. Mantener P, pesos, escala y
normalización exactamente; no convertir memorias a otra norma. El pico
nodal total entrante se hereda y se incluye en el cierre nuevo.

## Certificados nuevos

Ocho celdas por intervalo. Evaluar H119 Decimal100 en puntos medios y
proponer inversas binary64, una por celda compartida entre radios. Escalas
de tasa 2^-30 s. Compilar coeficientes y envolver el tubo medio completo;
certificar q<1 y la inversa ideal, conservar certificado y SHA completos.
No computar recintos si la cota nodal conocida no cabe estrictamente en
el radio. Rechazo no significa que el error real exceda el radio.

Residual constitutivo grado seis con resto exterior y ocho subceldas
internas, restricciones lineales exactas y forcing L1 y puntual completos.
Consultas Decimal100 u=0,1/2,1 diagnósticas, no sustituyen los recintos.

P retenida no certifica las tasas futuras: generar certificados
isotrópico, dirigido y balanceado para cada nuevo generador de junturas,
con intersección en la misma métrica. Registrar todas las consultas LDL.
No resolver candidatos nuevos de métrica. Recalcular para la partición
de 22 grupos todas las diagonales firmadas, acoplamientos, forcing y
ganancias nodales con normas primal/dual P/P^-1.

Propagar kernels exteriores de endpoint y pico, con forcing tardío.
Sumar anclaje y forcing por nodo antes de maximizar. Admitir sólo si todas
las inversas medias y la comparación completa prueban inclusión nodal
estricta, origen incluido. Mantener la justificación de continuación
implícita y dominio de los protocolos anteriores. Conservar todos los
radios, datos y rechazos; memoria rechazada no alimenta el siguiente tramo.

## Validación y alcance

Congelar fuentes antes de medir; datos, tests y validator antes de validar.
Validar sucesión no lineal conocida con cambios de h y memoria dirigida,
parada en primer hueco, fuente secundaria e identidad de norma, clocks,
interfaces, recintos, residual, inversas y tasas, cierres y selección.
Preservar todos los intentos fallidos y ampliar la reconstrucción de
entradas. Registrar duraciones intentada y certificada y costes nuevos.
No cambiar gates: KCL 10 pA, corrección 10 nV, rama lineal 10 fV,
backward 1e-10 y error global 1 mV. Este ensayo no identifica circuito
físico, sonido vintage, voz nativa o deadline.
