# Próximo bloque: cierre no lineal con comparación dirigida

## Hipótesis y datos que se conservan

Partir del [primer tubo rechazado](BIESTABLE_PRIMER_TUBO_RESULTADOS.md):
mismo soporte real, reloj, reconstrucción afín/constitutiva, radios,
recintos medios, inversas y residual. No modificar el circuito para
mejorar una cota. La medida escalar de 25 coordenadas puede perder
cancelaciones y propagar el máximo inicial hacia direcciones inexistentes.

## Experimento que debe congelarse antes de medir

1. Separar seis grupos físicos: audio 0..16; C10 17; C2 18; C4 19;
   C7 20; junturas 21..24. Mantener diagonales firmadas y acoplamientos
   dirigidos en una comparación positiva por bloques.
2. Propagar el vector de cotas iniciales por bloque desde las 25 cajas
   reales, en lugar de asignar el máximo a todas las coordenadas.
3. Declarar candidatos de métrica común para las cuatro junturas,
   constantes durante todo el intervalo, con redondeo exterior, incertidumbre
   del descriptor medio y conversiones completas. Congelar banco y orden
   de selección antes de consultas numéricas.
4. Incluir mapas nodales, forcing L1 y directo, picos dentro de cada celda
   y conversiones de norma. Conservar resultados brutos y comparación
   escalar previa; evitar comparar medidas de normas diferentes sin puente.
5. Aceptar únicamente si la cota nodal completa y el error inicial están
   estrictamente dentro del radio. La continuación implícita necesita
   todos los recintos, dominio válido y tasas/cargas acotadas. Un descriptor
   invertible por sí solo no cierra el tubo.

Validar con una ecuación no lineal de solución conocida, un caso de
cancelación firmada y tubos suficientes/insuficientes. Reproducir cada
celda y preservar rechazos y todos los intentos. Ninguna mejora local
cierra automáticamente el gate global de 1 mV o admite audio.
