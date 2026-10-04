# Próximo corte: estado consistente a la derecha del salto KEY

El [certificado de DC](BIESTABLE_DC_EVENTO_RESULTADOS.md) acota el modelo
KEY=0 y demuestra que conservar todos sus voltajes al pasar a KEY=10 viola
el dominio de CR10. Este plan prepara el próximo protocolo; no declara
resuelto el evento ni prescribe parámetros o tolerancias nuevos.

## Incógnitas y cargas iniciales

Usar 94 potenciales v y 25 tasas de coordenada de carga ydot, en el mismo
grafo documental. Mantener un vector de cargas iniciales y con recinto
derivado del DC y publicación. Las escalas son S_i=C_i para ramas lineales
y S_i=1e-12 C/V binario para junturas. El reloj sigue en t=0.
Conservar las fuentes antes/después del evento y declarar continuidad de
cargas bajo corrientes acotadas. No imponer continuidad a nodos sin memoria.

## Sistema de consistencia de 119 ecuaciones

- KCL: Fstatic(v,KEY=10)+sum_i incidence_i*S_i*ydot_i=0, en 94 filas.
- Ramas lineales: y_i - (Va-Vb-Vfixed) + R_i*C_i*ydot_i=0, en 21 filas.
  El término de tasa se conserva para C10 con R=25,5 kΩ; las demás ramas
  modeladas tienen R_i=0.
- Junturas: y_i-Q_i(v)/S_i=0, en cuatro filas, con las mismas leyes,
  transiciones y dominio exponencial ya declarados.

Derivar residual y Jacobiano del sistema, no de un paso con dt diminuto.
Separar candidato numérico, prueba de álgebra binary64 y certificado del
sistema ideal. No alterar el límite exponencial 45 ni usar clamp para
producir una solución. Conservar todos los candidatos fallidos y dominios.

## Prueba y publicación posteriores

1. Fijar semillas, política de Newton/line search y radios antes de medir.
   El límite V77>=8,26575090933 V es sólo una restricción de dominio.
2. Probar existencia/consistencia en un recinto y sensibilidad frente al
   recinto de cargas iniciales, con unidades de potencial y tasa separadas.
3. Comprobar cargas, KCL, ecuaciones de rama, dominio y memoria publicada
   restaurada con los gates existentes. Un pequeño residual no acota por
   sí solo el error de la proyección.
4. Registrar el evento como tal, conservando t=0, sin etiquetarlo como DC
   KEY=0 ni fabricar una historia anterior para BDF2. Preparar un arranque
   de orden declarado con el estado consistente posterior.
5. Comparar separadamente con el arranque histórico por backward Euler.
   Un historial distinto exige una trayectoria y evidencia propias.

Después del evento, fijar el primer tramo contiguo y su reconstrucción,
convertir la norma inicial explícitamente y propagar error/resto. Mantener
el inventario de huecos hasta cubrir toda la trayectoria. El cierre del
evento no admite automáticamente 1 mV global, física, audio o deadline.
