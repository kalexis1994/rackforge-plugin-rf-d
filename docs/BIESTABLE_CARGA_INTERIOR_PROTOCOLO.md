# Reconstrucción interior y cambios de pieza: protocolo

Declarado el 2 de octubre de 2026, tras el
[contraste continuo en extremos](BIESTABLE_CARGA_CONTINUA_RESULTADOS.md).
No hay integración nueva ni parámetros audibles nuevos. Se conserva
el modelo condicional/sintético, la revisión documental y todos los gates.
Las constantes/topología siguen sus fuentes SHA identificadas anteriormente.

## Reconstrucción y consultas

496 soportes de cuatro estados finos propios, índices 2..63 de las cuatro
ventanas y referencias 2/4. Para el último intervalo se normaliza
u=(t-t_anterior)/(t_actual-t_anterior). Tiempos, high+low, cargas y pesos
se levantan como fracciones exactas. Se construyen polinomios cúbicos
de los 94 potenciales y 25 cargas almacenadas, sin sustituir sus memorias.

Se consultan u=1/4,1/2,3/4: **1.488 puntos interiores**. Las fracciones
son cobertura de laboratorio, no constantes físicas ni control del paso.
En cada punto se evalúan a Decimal80/100 f(x)+A*Q', las 21 ecuaciones
U-Q/C-R*Q', QBE/QBC almacenada/interpolada menos Q(v), y Q' frente a
Cj(v)*v'. Otra KCL usa la regla de la cadena de las cuatro junturas;
se verifica su diferencia por incidencia conservativa. R=0 sigue siendo
restricción algebraica y C10 conserva su voltaje interno.

El extremo u=1 se contrasta con los 496 resultados anteriores. El residual
interior no es una trayectoria resuelta. Cargas y nodos interpolados por
separado pueden apartarse de la variedad constitutiva Q=Q(v).
Todos los errores de dominio se conservan por consulta, sin clipping o reseed.

## Certificados del polinomio, no de la trayectoria física

Para cada ecuación de rama lineal se obtiene su polinomio racional exacto
en u, incluidos derivada y factor 1/h. Se convierte a Bernstein sobre [0,1].
El mínimo/máximo de coeficientes encierra todo ese polinomio por la propiedad
de envolvente convexa; se registra la cota absoluta y observación <10 fV.
No se usa una rejilla para sustituir este certificado de la restricción.

Para cada una de las cuatro junturas se certifica el polinomio v-knee en
el último intervalo y en el soporte completo de cuatro tiempos. Si todos
los coeficientes Bernstein son estrictamente positivos o negativos, ese
polinomio permanece en una pieza. Los restantes se subdividen exactamente
por de Casteljau, hasta profundidad 40, conservando todo intervalo que
pueda contener un cero. Se registran puntos cero exactos, coincidencia
idéntica y brackets con/sin signos opuestos. Sólo signos opuestos prueban
un cruce por continuidad; un bracket sin ellos es inconcluso, no un cruce
inventado. Los intervalos excluidos tienen coeficientes de un solo signo.
La anchura final es (ancho inicial)/2^40; no es incertidumbre de la raíz física.

Los certificados sólo cubren los polinomios reconstruidos. No establecen
regularidad ni ausencia de cruces de la solución desconocida del circuito.
Los puntos de KCL no dan una cota de KCL entre consultas. No se integran
derivadas suaves a través de los brackets del knee ni se modifica esa ley.

## Gates y regresiones

Precisión, identidades y extremo: 1e-30 absoluto +1e-8 relativo, sin cambios.
10 pA y 10 fV clasifican observaciones; no aceptan pasos nuevos. Fuentes
SHA antes/después, pesos, tiempos, soportes y todos los resultados quedan
archivados. Pruebas: identidades polinómicas y Bernstein exactas, cruces
manufacturados con extremos del mismo signo, tangencias/coincidencias,
los 496 certificados y 1.488 consultas, replays racionales seleccionados,
FD de la regla de la cadena en piezas locales y bytes/alcance. Se preserva
cada intento fallido con fuente completa y recibo.

No se admite cota temporal global de 1 mV, defecto exacto, estimador
independiente, física, audio ni deadline mediante esta reconstrucción.
