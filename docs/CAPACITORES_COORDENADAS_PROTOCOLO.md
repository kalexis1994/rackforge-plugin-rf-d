# Capacitores: coordenadas sin cambiar el puerto eléctrico

El primer banco KLU de voz rechaza cutoff bajo y cierre de los VCA,
aunque completa nominales, cutoff alto, formas y carga. Se conserva
íntegro, incluyendo su validación global rechazada.

Se prueba una transformación algebraica para C9/C24/C15/C4/C27/C10/C2
de placa 4. Para sus terminales a/b:

```
u = Va - Vb - offset_constante
Iab = C * du/dt = C * d(Va - Vb)/dt
```

Una VCVS forma Va−Vb; una fuente constante resta el offset; el capacitor
interno va a masa y una CCCS refleja su corriente entre a/b con ganancia 1.
La fuente constante no es ESR ni una nueva polarización externa. El puerto
queda abierto en DC y conserva su ley ideal. El DC inicial resuelve u
consistentemente; la carga física se reconstruye como C*(u+offset).
La energía del capacitor interno sola no equivale a la energía física:
incluye el término de referencia al reconstruirla. No se usa UIC.

Offsets fijos en V: C9=10, C24=2, C15=6, C4=-1, C27=-1, C10=6, C2=3.
Son coordenadas para reducir DC almacenada en el estado y separar la
conductancia grande de los nodos físicos; no constantes de sonido ni
parámetros calibrados. Valores, conexiones externas, rieles, tarjetas,
trims y tolerancias físicas permanecen iguales.

Antes de admitir esta representación se declara un contraste de puerto:
220 microfarad, Va=2+0.1*sin(2*pi*440*t), Vb=1 V, offset=1 V;
10 ms, Euler implícito máximo 500 ns. Corrientes directa/transformada
y ley discreta C*delta(Va−Vb)/delta(t) dentro de 10 nA absolutos.
Después: unión nominal, cutoff 0.2 y ambos mutes, 10 ms Gear2/500 ns,
KLU. Que completen no admite aún 40 ms ni sus controles; deben pasar
el [banco de voz](VOZ_KLU_PROTOCOLO.md) y contrastar la trayectoria
nominal directa completa contra la transformada con los mismos gates.
