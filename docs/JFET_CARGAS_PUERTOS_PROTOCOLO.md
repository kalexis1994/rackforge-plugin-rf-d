# JFET: cargas de juntura como puertos explícitos

Fecha: 2026-10-06. El screening de tolerancia de corriente no completa
base Q21=0 V con ninguno de los tres candidatos. No se amplía la lista.
Se contrasta una representación de memoria equivalente del E402 condicionado.

## Ley, unidades y dominio

Fuentes: `jfetload.c` de ngspice 46, revisión fijada en
[el manifiesto](../evidence/voice_current_tolerance_sources.json), y manual
NG-46 PDF pp. 83–84, sección 3.3.9, sintaxis `C ... Q='expresión'`.
Nivel 1, m=0.5, RD=RS=0, temperatura=TNOM=25 C, tarjeta registrada
[del laboratorio](../evidence/vco1_laboratory_devices.json). No se extrapola
a otras temperaturas, resistencias internas o modelos de dispositivo.

Para cada puerto gate→source y gate→drain, V en voltios, C0 en faradios,
PB en voltios, FC adimensional, q en coulomb:

```text
Vc = FC*PB
V < Vc: q(V) = 2*PB*C0*(1-sqrt(1-V/PB))
V >= Vc:
  d = V-Vc
  q(V) = q(Vc) + C0/sqrt(1-FC)*d + C0/[4*PB*(1-FC)^1.5]*d^2
I(g→x) = dq(Vg-Vx)/dt
```

q y dq/dV son continuas en Vc. Se conservan referencia q(0)=0,
orientación, valores CGS/CGD y las cuatro memorias de las dos mitades.
El NJF original mantiene canal, conducción de diodos y gmin con CGS=CGD=0;
los puertos explícitos reciben esas cargas, sin duplicarlas o eliminarlas.
No hay epsilon, capacitor lineal sustituto, ESR ni ley ajustada a oído.
La expresión protege la raíz de su rama inactiva; en la rama seleccionada
es exactamente la ley indicada. El solver e inicialización de la memoria
cambian, y requieren contraste: equivalencia de ecuaciones no prueba
convergencia ni equivalencia de trayectorias a precisión finita.

## Banco predeclarado

Primero comparar NJF original y NJF con cargas separadas bajo los mismos
voltajes de terminal, en un único solve de 20 microsegundos, máximo 5 ns,
Gear2/KLU. Gate PWL: -1, -0.1, +0.65, -1, -3, +0.65, -1 V en
0, 2, 4, 6, 10, 14, 20 microsegundos; source=0 V y drain senoide
0.2 + 1.5*sin(2*pi*100 kHz*t) V. Cruza región inversa y continuación
de carga forward. Comparar las tres corrientes de fuentes de terminal:
<=1 nA + 1e-6 relativo, y diferencia integrada acumulada <=10 fC.
Este gate pertenece al puerto de laboratorio; no identifica un E402 real.
Si falla, conservar el ensayo y no ejecutar escenas de voz.

Si pasa: base Q21=0 V, contorno=0 V, cutoff=0.2 y nominal125, en ese
orden. Cada escena conserva 40 ms, observación desde 20 ms, máximo 125 ns,
Gear2, KLU y tolerancias originales (abstol=1e-13 A incluida).
Se reportan todas, aunque una rechace. No se modifica el generador nominal.
El intento es diagnóstico y no admite un nuevo oráculo por sí solo.

Una posterior admisión exige el banco de once escenas, más 250 ns y
Trap2/125 ns en los tres controles, y contraste nominal con la referencia
anterior. Los gates de frecuencia 1 cent, extremos 5 mV, RMS 1% + 10
microvolt y balance C2 0.1 nC permanecen. Toda fuente/deck/log/trace queda
identificada antes/después; los rechazos históricos permanecen visibles.
