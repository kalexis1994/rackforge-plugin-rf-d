# Protocolo congelado: proyección consistente post-KEY

Modelo nominal CA3046 documental, leyes y parámetros sintéticos idénticos
al anclaje DC. Este experimento offline no modifica el motor ni el reloj.

## Datos, incógnitas y conservación

Leer el DC certificado y sus 25 recintos de carga. El centro de cargas es
la memoria publicada previa, no un nuevo ajuste. Fijar KEY=10 V en t=0.
Resolver los 94 potenciales y 25 tasas de coordenada mediante el sistema
del [plan post-KEY](BIESTABLE_ESTADO_POST_KEY_PLAN.md): KCL estática más
incidencia*S*ydot; y-voltage+R*C*ydot para lineales; y-Q(v)/S para junturas.
Conservar C10 con resistencia serie. No imponer continuidad de potenciales.

## Política fijada antes de ejecutar

Dos semillas: todos los potenciales DC anteriores y tasas cero, cambiando
sólo V77 a 9,5 V y 9 V respectivamente. Ejecutar ambas; primera convergente
como candidata primaria. Newton Decimal80, Jacobiano analítico del descriptor,
eliminación con pivot parcial, máximo 64 iteraciones. Line search con 25
candidatos alpha=2^-k (k=0..24), Armijo 1e-4, mérito máximo de residual KCL
dividido por 10 pA y residual de coordenadas dividido por 10 fV. Rechazar y
registrar dominios inválidos, sin clamp. Parar con ambos residuales <=1e-35
en sus unidades y corrección ponderada <=1e-25 V. Estas metas adicionales
de precisión no sustituyen los gates previos de publicación.

Calcular un precondicionador binary64 de H119 en el centro primario.
Registrar separadamente solve(Hbinary,I) con el solver y gate backward
1e-10 anteriores; un rechazo no se oculta ni impide una prueba ideal exterior.
El precondicionador no se admite en audio.

## Recinto y dependencia de las cargas

Pesos D: 1 para potenciales, 1e-6 s para tasas; ||D*delta(v,ydot)||inf tiene
unidades V. Cajas de radios normalizados 1e-9, 1e-8, 1e-7 y 1e-6 V;
ejecutar todas y elegir el primer certificado robusto aceptado.
Usar Banach con I-D*X*H*D^-1 y D*X*residual. Sellar corrientes/exponenciales
compartidas antes de intervalos; conductancias y masa exactas racionales.
Encerrar capacitancias de juntura mediante monotonía y extremos del recinto,
incluyendo la transición con knee binario. Todo exponente <=45.

Probar dos objetivos por radio: cargas publicadas nominales y toda la caja
de cargas compatible con DC. Para la segunda agregar D*X[:,94:119]*delta_y
al residual central, conservando cada intervalo de parámetro. q<1 e imagen
estrictamente interior garantizan una raíz local única para cada carga de
esa caja, con cota posterior eta/(1-q). No afirman continuidad global de
ramas ni unicidad fuera de la caja. Mantener voltajes y tasas con unidades
separadas; convertir tasas dividiendo la cota normalizada por 1e-6 s.

## Publicación, pruebas y alcance

Publicar un evento propio con fuente previa/posterior, reloj cero, cargas,
tasas y potenciales racionales sin pérdida. Restaurar JSON y comprobar
residual Decimal100 con KCL 10 pA y restricciones 10 fV. No fabricar una
historia BDF2 ni llamar DC KEY=0 al evento. Esta publicación de laboratorio
no es todavía el estado binary64 del integrador.

Verificar Jacobiano con diferencias independientes, eliminación con solución
conocida, sello de cargas/corriente, resistencia serie, ambos candidatos,
replay de los ocho certificados, residuales Decimal80/100, incertidumbre de
cargas y dominio completo, serialización, bytes, fuentes y scopes. Congelar
pruebas y validator antes de validar; conservar cada intento fallido.

No avanzar tiempo ni repetir el corpus de trayectorias. Restan publicación
high+low en el integrador, arranque sin historia, reconstrucción contigua,
conversión de norma inicial y resto no lineal. Gates global 1 mV, física,
audio y deadline siguen abiertos. Corpus ampliado separado tras validación.
