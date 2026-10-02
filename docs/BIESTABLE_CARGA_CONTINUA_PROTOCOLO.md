# Tasas de carga y ecuaciones continuas: protocolo

Declarado el 2 de octubre de 2026. Se mantienen el modelo condicional,
sus parámetros sintéticos y los informes anteriores. No hay solves nuevos.
Fuentes eléctricas, topología y restricciones siguen los productores
identificados por SHA del [diagnóstico anterior](BIESTABLE_DEFECTO_MUESTREADO_PROTOCOLO.md).
No se introduce una constante audible ni se identifica un componente vintage.

## Cobertura y preparación

496 puntos: índices 2..63, cuatro ventanas, referencias propias de 2/4
subpasos. Últimos cuatro tiempos/estados finos publicados, sin reseed.
Todos los high+low, cargas y evaluaciones se preparan dentro de contextos
Decimal80/100. Q conserva las 25 memorias autoritativas, en C.
Los pesos cardinales cúbicos/cuadráticos son fracciones exactas de tiempos
binary64. El BDF fino usa los coeficientes a0/a2/h realmente archivados
del último subpaso, aplicado a los últimos tres estados propios.
Las derivadas se evalúan mediante diferencias que anulan el origen de Q.

## Ecuaciones y signos

Con A como incidencia saliente y f(x) como KCL estática, ambos en A:

`R4 = f(x) + A D4 Q`, `Rb = f(x) + A Db Q`.

Se verifica `R4 = Rb + A(D4-Db)Q`. No se usa beta para sellar
corrientes continuas: beta pertenecía a la eliminación discreta del
defecto en la rama RC serie, no a la incidencia física de Q'.
Se guarda también f evaluada sobre potenciales high redondeados y
su diferencia frente a high+low. Ese contraste no se sustituye por
un cambio de integrador ni por el recibo histórico binary64.

Para las 21 ramas lineales, con voltaje terminal U, capacidad C,
voltaje interno vc=Q/C y resistencia serie R:

`E4 = U - vc - R D4Q`, `Eb = U - vc - R DbQ`.

Se verifica `E4 = Eb - R(D4-Db)Q`. R=0 mantiene la restricción
algebraica independiente de la derivada. C10 usa su memoria interna,
no el voltaje terminal como si fuera el voltaje del capacitor.

Para las cuatro cargas QBE/QBC se contrasta D4Q almacenada con
`Cj(v) * D4v`, donde Cj=dQ/dv de la ley condicional congelada.
Se guarda además Q almacenada menos Q evaluada sobre high+low.
Se registra si los cuatro extremos de soporte ocupan piezas diferentes
del knee; la ausencia de cruce muestreado no garantiza regularidad interior.
Se conserva KCL con ambas tasas no lineales. La regla de la cadena sobre
un interpolante de nodos no es la derivada exacta de la trayectoria física.

## Verificación y alcance

Todos los vectores y las tres identidades se contrastan con los gates
existentes 1e-30 absoluto +1e-8 relativo; sin clipping. Conservación
dinámica incluye contribuciones de terminales fijos. Se archivan los
pesos, coeficientes, recibos del paso fino y diferencias 4 menos 2.
Los umbrales 10 pA KCL y 10 fV de ecuación de rama sólo clasifican
observaciones del diagnóstico; un incumplimiento se conserva completo.
No son criterios de publicación de nuevos pasos, que no se ejecutan.

Las regresiones auditarán todos los puntos a 80/100, 24 replays racionales
de tasas/incidencias/ecuaciones de ramas (índices 2,31,63), un evaluador
estático independiente por corrientes de dispositivos en esos puntos,
FD independiente de capacitancia de juntura, conservación, alcance y bytes.
Se preservará cada intento fallido con fuente completa y hashes.

Este residual es puntual y depende de estados numéricos y reconstrucción.
No certifica una solución de la DAE, un defecto temporal exacto, una cota
entre muestras, error global de 1 mV, física, audio ni tiempo real.
No se cambia controlador, historia, raíz ni informe anterior.
