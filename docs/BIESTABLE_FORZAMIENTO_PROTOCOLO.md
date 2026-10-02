# Forzamiento relativo a una continuación refinada: protocolo

Declarado el 2 de octubre de 2026. No modifica integrador ni controlador.
Se usan las cuatro ventanas congeladas de 64 pasos de memoria larga,
con el mismo circuito, parámetros sintéticos, KEY=10 V y R61=200 ohm.

## Referencias condicionadas

Desde cada historial doble base se ejecutan continuaciones propias con
dos y cuatro subpasos por intervalo base. No se vuelven a sembrar estados.
Los destinos intermedios se calculan desde inicio + j*h/N; el último es
el tiempo base archivado. Cada intervalo resuelto es destino - tiempo
actual; se conservan diferencia respecto a h/N, razón, fuente, estados,
publicación y fallos. Mínimo 1 ps, razón BDF2 <=2, KCL 10 pA, corrección
10 nV, rama 1e-14 V y roundtrip exacto mantienen sus gates.
No hay arranque desde DC ni gate adaptativo. Se cuentan todos los intentos.

Se muestrean los extremos finos sobre el reloj base, conservando aparte sus
historiales finos reales. Las dos memorias iniciales son las del anclaje
común. El historial muestreado no se presenta como trayectoria BDF2 gruesa
aceptada. No se presupone convergencia al aumentar N.

## Mapa levantado y forzamiento

Para evitar restar corrientes binary64 casi iguales se usa el grafo de
curvatura de 94 nodos, con las mismas leyes, en Decimal80/100. Los nodos
levantados son high + low; no se afirma identidad con la evaluación
binary64 original de potenciales redondeados. Pasivos dinámicos conservan
g=1/(dt/C+R), P y D binary64 levantados. Q se evalúa analíticamente.

Sean delta_n y delta_m las diferencias referencia menos base. Con
virtual=(1+gamma)*delta_m_actual - gamma*delta_m_previa (los mismos
coeficientes binary64 levantados), se calcula independientemente:

- r = F_lift(n_ref, virtual_ref) - F_lift(n_base, virtual_base), en A.
- z = delta_m_publicada - [G_lift(ref) - G_lift(base)], en V de coordenada.

F incluye estática, cargas terminales/dt y ramas lineales; su dependencia
en memoria es -B*virtual. G conserva P/D para las 21 memorias lineales,
incluida C10 serie, y QBE/QBC dividido por 1 pF para las cuatro restantes.
La escala 1 pF sigue siendo exclusivamente numérica.

La recurrencia forzada de primera variación es:

`J n1 = B virtual1 + r; m1 = P n1 + D virtual1 + z`.

Con r/z considerados constantes en la familia epsilon*r/epsilon*z y
historias iniciales cero, la segunda es:

`J n2 = B virtual2 - H_F[n1,n1]`

`m2 = P n2 + D virtual2 + H_G[n1,n1]`.

La predicción a epsilon=1 es primera + segunda/2. El forzamiento r/z se
extrae de la referencia finita; no es un estimador independiente disponible
en ejecución ni se ajusta una constante al error. La recurrencia homogénea
con ambos historiales cero permanece cero; no representa esos defectos.

## Contrastes congelados

Se conservan ambas referencias y todos los errores lineales/cuadráticos
contra sus diferencias nodales/memoria. Gate por componente:
10 nV + 1e-3*abs(predicción). Un fallo no cambia niveles ni cobertura.
Se guarda diferencia 2/4 sin elevarla a cota de solución exacta.

Todos los pasos contrastan r/z y H Decimal80/100: máximo cociente
abs(diferencia)/(1e-30 + 1e-8*abs(valor80)) <1. Ambos errores hacia atrás
de cada solve deben ser <1e-10; si falla, se guarda y se detiene esa
recurrencia, manteniendo la continuación fina separada. En índices
0/31/63 se auditan ambos RHS con eliminación racional exacta de los
coeficientes binary64; gate de mapa normalizado 1e-8.

Se comprueban identidades con un testigo escalar racional independiente
y una carga RC serie. Se registran SHA antes/después, serialización
canónica, todos los recibos e intentos fallidos. No hay parámetros vintage
nuevos, cierre temporal global de 1 mV, solución DAE exacta, audio o deadline.
