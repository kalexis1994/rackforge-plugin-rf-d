# Próximo bloque: continuación con reconstrucción curva

El [octavo soporte](BIESTABLE_REFERENCIA_CURVA_RESULTADOS.md) conserva sus
extremos y certifica hasta ≈25 µs: pico local ≤0,327 µV, global ≤0,793 µV.
Usar sus 22 memorias finales reales, selección [1,1] y P fija. La referencia
curva interior no modifica los estados publicados; conservar su identidad.

## Experimento que debe congelarse antes de ejecutar

1. Intentar primero índice 8, ≈25→50 µs, y declarar límite contiguo,
   variantes, radios, orden y parada en el primer hueco. No transportar
   la afín rechazada del octavo soporte ni una cota no soportada de 10 µV.
2. Conservar la receta de la burbuja: X candidata del punto medio de cada
   afín, f0=-X_C7*R_poly completo, A=(f0(0)-f0(1))/2 y p=A*h*u*(1-u).
   Reconstruir las leyes con tiempo físico y preservar endpoints exactos.
   No reutilizar X, acciones, recintos o tasas del soporte anterior.
3. Renovar las 119 ecuaciones y los recintos del descriptor medio en cada
   curva, inversas, tasas y acciones en las mismas normas. P fija no prueba
   estabilidad futura. Conservar expansión completa, Q por piezas y RC.
4. Encadenar únicamente cierres estrictos reales y sus 22 memorias finales;
   comprobar interfaces, reloj, hash del certificado y selección. Registrar
   pico local y pico acumulado separados. Parar en el primer hueco.
5. Si reaparece forcing temporal dominante, identificar memoria/nodo/celda
   y su contribución antes de elegir otra referencia o cambio auxiliar.
   Mantener límites de kernel e integer_text_limit=0 explícitos; no elevar
   radio o dominio para obtener una admisión.
6. Congelar fuentes, datos y tests por etapas; ampliar corpus y preservar
   cada intento. Probar soportes variables, curva/signo, interfaces,
   transporte y recertificación completa. Los gates globales permanecen
   independientes de cualquier prefijo nominal más largo.
