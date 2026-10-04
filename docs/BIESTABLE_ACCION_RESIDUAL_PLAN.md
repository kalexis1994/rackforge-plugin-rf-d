# Próximo bloque: certificar la acción algebraica del residual

El [prefijo de 22 grupos](BIESTABLE_PREFIJO_22_RESULTADOS.md) conserva
tres intervalos realmente probados hasta aproximadamente 781,25 ns.
Su cuarto tramo rechaza en 1 µV por ≈4,374301 nV de exceso; el término
algebraico directo domina. Fuente futura: último resultado admitido
de ese prefijo, con las mismas 22 memorias, P, norma e interfaz.

## Antes de medir

1. Mantener trayectoria, circuito, parámetros y gates. Investigar primero
   la dirección del residual; no cambiar el radio del ensayo anterior ni
   seleccionar resultados de otro banco como si ya hubieran cerrado.
2. Conservar los coeficientes firmados de su polinomio y las incidencias
   terminales de cada ley. Las cotas nodales absolutas anteriores siguen
   válidas como comparación de control. Toda correlación nueva debe
   derivarse de la misma expresión eléctrica y sus restos certificados.
3. Diseñar un recinto de Hbar^-1 aplicado al RHS completo, con defecto
   y cola de Neumann rigurosos. Comparar acciones sobre direcciones
   vectoriales con suma de columnas absolutas, incluyendo todas las
   ecuaciones nodales y restricciones. No confiar en X_binary*RHS sin
   encerrar el defecto, ni cancelar intervalos independientes.
4. Cubrir el punto y L1 en todo el tubo y tiempo; distinguir el residual
   reconstruido de los coeficientes variables del descriptor medio.
   Conservar los demás términos de memoria y las conversiones P/P^-1.
5. Fijar partición, radios, orden y costes antes de ejecutar un banco.
   Si una action sólo mejora un diagnóstico, no promoverla a prueba de
   trayectoria. Un rechazo sigue cortando la cadena en el cuarto soporte.
6. Validar sistemas conocidos con modo común sensible y residual dirigido,
   un caso sin cancelación, incertidumbre de matriz y restos correlacionados
   e independientes. Reproducir certificados y conservar todos los fallos,
   sin modificar los datos o fuentes congelados de cortes anteriores.

Los nodos 27/28 incluyen R35-VCA1 y terminales de Q16/Q15/Q18-VCA1.
No asumir conservación de una pareja sin contabilizar esos terminales.
Si el nuevo recinto no mejora, registrar el resultado y estudiar el
residual/reconstrucción con un protocolo separado. La meta global de
1 mV y la admisión física, sonora y nativa permanecen pendientes.
