# Diferenciación de carga: protocolo y derivación

Declarado el 2 de octubre de 2026. Se mantienen circuito, integrador,
controlador, umbrales y todos los informes anteriores. El primer bloque
usa soluciones manufacturadas conocidas; no identifica parámetros vintage.

## Operador ideal y signo

Destino t=0, historiales en -h y -(h+k), h/k en (0,2]. Los pesos ideales
del interpolante cuadrático son:

`w0=(2h+k)/(h(h+k)); w1=-(h+k)/(hk); w2=h/(k(h+k))`.

El defecto de corriente es `tau = sum(w_i Q(t_i)) - Q'(0)`, en A.
Para Q con tercera derivada continua en el intervalo:

`tau = integral K(u) Q'''(u) du`, de -(h+k) a 0, donde

`K(u)=-h*(u+h+k)^2/[2k(h+k)]` entre -(h+k) y -h;

`K(u)=u+(2h+k)*u^2/[2h(h+k)]` entre -h y 0.

K es no positivo y su masa es `-h(h+k)/6`, en s². Por tanto
`abs(tau) <= h(h+k)/6 * sup(abs(Q'''))` sólo si esa cota se conoce
sobre todo el intervalo. No se sustituye por un máximo de muestras.
Para arranque BE: kernel `-(u+h)/h`, masa `-h/2`, aplicado a Q''.
El límite puede ser integral bajo regularidad suficiente; aquí los
testigos no atraviesan discontinuidades de fuente o ramas de carga.

Con delta = exacto menos numérico, el residual de la referencia exacta
es +tau; ése es el signo del forzamiento del mapa de diferencias. El
error numérico menos exacto utiliza el signo contrario. Las memorias
entrantes numéricas propagan su propio error además del defecto nuevo.

## Carga RC serie y publicación

Para la rama lineal C/R, terminal = vc + R*Q', Q=C*vc. Sea
dt_eff=1/w0 y beta=dt_eff/(dt_eff+C*R). Al evaluar el paso discreto
en los estados exactos, su corriente difiere de Q' en **beta*tau**.
La diferencia vc_exacta menos vc_publicada es **R*beta*tau**.
En consecuencia la rama aporta r=beta*tau a KCL y z=R*beta*tau a
su memoria de voltaje. R=0 deja r=tau y z=0. Las cargas de juntura
directas aportan tau con sus incidencias terminales; su publicación
ideal Q(V) no introduce ese término RC adicional.

## Testigos declarados

- Polinomios racionales de grado 0..8, cuatro razones (1/4,1/2,1,2)
  y h=1 o 1/1000. Pesos de Lagrange independientes, kernel integrado
  exactamente, anulación de grado <=2, signo, origen y cotas polinómicas.
- Arranque BE sobre los mismos grados y ambas escalas.
- RC serie con C=10 uF y R=25500 ohm, más R=0 como control algebraico.
  Son constantes del ejemplo de rama C10, sin calibrar su excitación.
  Voltaje conocido vc(t)=1/5+t+100*t²+100000*t³ (V, t en s).
  Se publican 64 pasos propios sobre dos relojes: uniforme y patrón
  (1/2,3/4,1,3/2,1,1/2,1/4,1/2)*10 us. Se ensayan arranque BE y
  historial doble inicialmente exacto. Se verifica error forzado exacto,
  y se conserva error que quedaría oculto al omitir z.
- QBE/QBC sintéticos existentes, dos sesgos (.12/.55 V), cuatro
  razones y dos h (100/50 us): 32 perfiles. Voltaje conocido
  v(t)=v0+100*t+20000*t²+10000000*t³. Se deriva
  Q'''(t)=Q_v'''*v'^3+3*Q_v''*v'*v''+Q_v'*v'''.
  Se rechaza cruce de knee o dominio exponencial inválido.
  Cuadratura Simpson separada en -h con 32/64/128/256 particiones por
  tramo; se conserva cada nivel. Contraste con defecto calculado desde
  Q y Q' analíticos. Gate 1e-30 A + 1e-8*abs(tau), sin escoger nivel
  posterior. Las dos mallas finales son el gate de cuadratura declarado.
  Se registra Decimal80/100 de todos los defectos y de la malla final.

Los polinomios se calculan con fracciones exactas; cargas no lineales
con preparación y evaluación explícitas a 80/100 dígitos. Los sesgos,
coeficientes de trayectoria y escalas temporales son testigos manufacturados.
No se transfieren como constantes de sonido o límites universales RF-D.
Se guardan fuentes/SHA antes/después, fallos y recibos. No hay nuevos
solves no lineales, admisión de 1 mV desde DC, audio o deadline.
