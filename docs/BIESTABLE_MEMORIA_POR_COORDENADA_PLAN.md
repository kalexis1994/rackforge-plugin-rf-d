# Próximo bloque: conservar dirección de memoria por coordenada

El [segundo intervalo rechazado](BIESTABLE_PREFIJO_CERTIFICADO_RESULTADOS.md)
está dominado por su anclaje propagado. El puente de 1 µV es identidad,
la memoria reconstruida es continua y el residual nuevo es menor.
Investigar pérdida de dirección al reemplazar 17 cargas por su máximo.
No interpretar la cota excesiva como crecimiento del error real.

## Protocolo que debe congelarse antes de medir

1. Reutilizar el primer certificado, sus estados, recintos, inversas,
   anclajes iniciales y perfiles de pico por celda. Refinar la memoria
   saliente por coordenada utilizando ese certificado como cubierta
   ya probada; no resolver nuevamente el circuito ni reiniciar DC.
2. Para cada coordenada lineal, encerrar su diagonal firmada y
   acoplamientos desde la inversa media. Propagar su error inicial
   individual y forcing L1; para los demás términos usar los picos
   de grupo realmente certificados en la celda. Incluir todos los
   acoplamientos y las conversiones duales de junturas.
3. Guardar la cota original y la refinada. Intersectar únicamente
   cotas del mismo error y norma; una cota por coordenada puede
   acotar la memoria aunque su refinamiento no mejore ese componente.
4. Congelar una partición de 22 grupos: las 21 coordenadas lineales
   individuales y un bloque cuadrático de cuatro junturas. Conservar
   la métrica certificada del primer intervalo y pagar todas las
   conversiones, forcing y mapas nodales de la nueva partición.
5. Comparar con el intento de seis grupos sobre los mismos radios,
   residual y soporte. Verificar picos interiores, forcing tardío,
   anclaje anisótropo y una red pequeña con solución conocida.
6. Cerrar el segundo tubo sólo por inclusión nodal estricta, dominio,
   descriptor medio y memoria entrante probada. Registrar rechazo
   si la partición fina tampoco basta; no reducir artificialmente
   cotas ni calibrar constantes para satisfacer la desigualdad.

El prefijo real sólo se prolonga tras ese cierre. Congelar fuentes y
protocolo antes de medir y conservar cada intento. 1 mV global, hardware,
voz completa y tiempo real siguen requiriendo sus propias verificaciones.
