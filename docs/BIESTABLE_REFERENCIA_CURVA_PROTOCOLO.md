# Protocolo: referencia cuadrática con endpoints publicados conservados

Modelo documental CA3046 nominal y sintético. Fuente aceptada: séptimo
soporte del informe signed_memory, selección [1,1]. Transportar sus 22
errores finales reales restituidos, pico y P del prefijo dirigido por SHA.
Intentar sólo índice 7, ≈12,5→25 µs; ninguna rama rechazada continúa.

## Banco fijado antes de medir

Orden exterior affine, c7_bubble; radios interiores 0,1/1/10 µV. Seleccionar
el primer par con cierre estricto; completar ambas variantes y todos los
radios aunque uno acepte. Ocho celdas y ocho subceldas de acción por celda.
Política explícita sys.set_int_max_str_digits(0), dominio de kernels <=4096,
exponenciales <=45 y gates anteriores intactos. Sin nuevos solves.

## Candidata y unidades

Reconstruir la afín con las historias propias 6 y 7. Evaluar su descriptor
Decimal100 en u=1/2 y obtener X candidata binary64 finita, fija en todo el
soporte. Construir el RHS polinómico completo de las 119 ecuaciones.
f0(u)=-sum_j X[114,j]*R_poly,j(u) en V/s. Fijar A=(f0(0)-f0(1))/2.
p=A*h*u*(1-u) en V. Referencia curva x_i=x_affine,i-X[i,114]*p (94 filas),
y_C7=y_affine,C7+p. Las otras veinte memorias lineales conservan su afín.
Los dos extremos son exactamente los publicados. No usar p como solución
verdadera ni cancelar restos independientes del RHS usado como candidata.

Recalcular q=C*y, las 21 restricciones y-voltage+tau*y'_t (C10 incluida)
y cuatro voltajes de juntura. Q(v_curva) sigue la ley constitutiva por
piezas original; cuatro placeholders cero no son carga física cero.

## Auditoría del grado y recintos

Las operaciones exactas add/multiply/reparameterize/Bernstein conservan
todo el grado. La expansión exponencial de orden seis produce grado doce
para voltaje cuadrático: sin recortar coeficientes. Su resto usa el radio
Bernstein completo. Capacitancias monótonas por piezas y slopes variables
se cubren por intervalos; pagar C(v)*v'_t y los restos completos.

Renovar para cada variante ocho X de celda, residual, covers Hbar con radio,
inversas completas, tasas en P fija y acciones firmadas. Conservar recintos
de toda la curva, no sólo puntos. La P anterior mantiene la norma, no las
tasas ni la validez de inversas futuras. Todos los certificados nuevos y
rechazos quedan archivados. El error se mide respecto a cada referencia;
el integrador y sus endpoints permanecen intactos.

## Validación y alcance

Congelar helper/productor/protocolo antes de medir. Datos, tests y validator
antes de validar. Comprobar solución cuadrática exacta, signo, endpoints,
tiempo físico, restricciones RC y Q, residual completo contra consultas
Decimal100, recintos curvos e inversas/acciones/tasas/cierres reproducidos.
Preservar fallos y ampliar corpus. KCL 10 pA, corrección 10 nV, rama 10 fV,
backward 1e-10 y objetivo 1 mV intactos. No admite hardware, voz completa,
sonido vintage, audio nativo ni deadline.
