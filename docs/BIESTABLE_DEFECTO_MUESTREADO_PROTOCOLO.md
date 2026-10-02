# Defecto aproximado sobre referencias propias: protocolo

Declarado el 2 de octubre de 2026, después de fijar los
[testigos de carga](BIESTABLE_DEFECTO_CARGA_RESULTADOS.md). No se ejecuta
integración nueva ni se cambia controlador. Se usan las dos referencias
propias de 2/4 subpasos de las cuatro ventanas de forzamiento.

## Cobertura y reconstrucción

Se estudian índices gruesos **2..63**, 62 por referencia: **496 puntos**.
Los dos predecesores gruesos son extremos de esa misma continuación fina.
Los cuatro puntos de la derivada fina son sus últimos cuatro publicados,
con sus tiempos exactos binary64 levantados. No se inventa un timestamp
del historial anterior al anclaje ni se usa la base como reseed.

Q tiene 25 coordenadas en C: C*voltaje compensado del capacitor para las
21 ramas, incluidos los voltajes autoritativos de C10 serie, y las cuatro
QBE/QBC almacenadas. Preparación y evaluación explícitas Decimal80/100.
No se recalcula Q desde potenciales redondeados para sustituir la memoria.

Se reconstruye Q' mediante derivada del interpolante cúbico de los cuatro
puntos finos, con pesos cardinales de Lagrange racionales exactos.
La derivada cuadrática de los últimos tres sirve como contraste adicional.
Ambas son aproximaciones sobre estados numéricos; su diferencia no es
una cota ni un estimador del error absoluto de Q'.

## Tres operadores separados

- Dclock: interpolante cuadrático de los tres tiempos gruesos guardados.
- Dcommand: BDF2 ideal con h/k de los intervalos comandados archivados.
- Dbinary: `[a0*(Qn-Qn-1)-a2*(Qn-1-Qn-2)]/h`, levantando exactamente
  a0/a2/h binary64 del paso base. Conserva anulación del origen de Q.

Se guardan todos los vectores y la descomposición:

`Dbinary Q - Q'_cubico = (Dclock Q - Q'_cubico)
 + (Dcommand-Dclock)Q + (Dbinary-Dcommand)Q`.

El primer término es un defecto aproximado; los otros separan reloj y
coeficientes. La razón de intervalos de timestamps puede exceder apenas
2, aunque los intervalos comandados cumplan el dominio: aquí Dclock es
un interpolante matemático, no un solve aceptado con esa razón.

El mapeo diagnosticado de tau_binary aproximado a KCL/publicación usa
las incidencias de las 21 ramas y cuatro junturas. Para C10 aplica
r=beta*tau y z=R*beta*tau; las otras ramas tienen R=0. beta se deriva
del dt_eff racional h/a0 y parámetros binary64 levantados. Se conservan
también dt_eff del kernel y la diferencia respecto a esta fracción;
no se afirma igualdad de bits con el kernel original. La suma de KCL
incluye explícitamente la contribución de los terminales fijos omitidos.

## Gates y alcance

Todas las derivadas, componentes, KCL/publicación y descomposición se
contrastan Decimal80/100 con 1e-30 absoluto +1e-8 relativo por componente.
Se conservan los 496 puntos, pesos racionales, metadatos de reloj y
todos los fallos. Se verifica identidad del origen de Q y conservación,
sin clipping de componentes pequeñas. Se guardan diferencias 4 menos 2
entre aproximaciones en los mismos extremos; no se promueven a cotas.

Este productor sólo diagnostica el operador de diferenciación sobre
referencias conocidas. No compara su salida con el forzamiento relativo
anterior como si ambos midieran lo mismo, no utiliza este proxy para
modificar pasos, ni admite defecto exacto, estimador independiente,
convergencia global desde DC, física, audio o deadline. Antes de usarlo
en una recurrencia de error necesita un contraste propio de la derivada
y cobertura desde el arranque/discontinuidades.
