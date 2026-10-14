# VCO nominal de fase con puerto cargado

Base `c6b6f91`, SVC-9 CA3046 pp.5/19, SW6 sierra, R8=.5, R11=500 Ω,
C4=10 pF, seis CV de placa −2.1 V, 25 °C, rieles nominales. Perfil
experimental de régimen periódico; no sustituye todavía el VCO de la voz.

## Reducción y fuentes

Usar los 53 coeficientes complejos (DC y 52 armónicos) del ciclo nativo
de 30 ms admitido en `voice_vco1_radau_listening01.json`, conservando DC.
Son integrales del interpolante eléctrico del último ciclo, no una onda
ideal. Recuperar el drive48 desde sierra46/tri54 por KCL resistiva con
BUS=0. La red de salida lleva 4.7 kΩ a masa, 4.3 kΩ a drive48, 47+10 kΩ
a tri54 y el puerto R6/R45. No atribuir exactitud al generador periódico:
se aproxima su estado interno y su reacción dinámica a la carga.

Eliminar sierra46/tap47/cursor39 de esa red resistiva. Conservar las cuatro
corrientes de drive/tri/masa/BUS, Jacobiano completo, contacto α y potencia.
La sierra se resuelve con BUS libre: no es una fuente de voltaje ideal.
R45 sigue presente una sola vez; no duplicar R6/R45 al conectar la cadena.

La fase de reset del ciclo aislado se relaciona con su cruce descendente
C1=−2 V. Ajustar período/época exclusivamente con cruces descendentes
de la voz cargada entre 8 y 40 ms. Reservar 40–100 ms para contraste,
con ambas resoluciones y sin alineación o cambio de ganancia posterior.
Importar el ciclo viejo por streaming, sin nueva copia de muestras.

## Gates previos

- Cruces reservados: fase ≤1e−4 ciclos y frecuencia ≤0.01 cent respecto
  de la recta ajustada. Comparar también con la frecuencia aislada.
- Red resistiva original de tres nodos internos: corrientes ≤2 fA +
  2e−12|I|; tensiones ≤2 pV + 2e−12|V|; Jacobiano FD ≤2e−12 S + 2e−7|Y|.
- Forma nominal: comparar DC y armónicos 1–8 con integración sobre fase
  de observaciones reservadas; error vectorial AC ≤2 %, DC ≤5 mV.
  Registrar hueco máximo de fase; observaciones de 8 kHz no acreditan
  armónicos altos ni el reset continuo. Error crudo RMS/máximo es diagnóstico,
  sin presentarlo como error de banda audible.
- Reacción local al BUS: tangentes Radau del VCO completo con historia
  fija, 24 estados reservados, h=1/8/32 µs, BUS de ambas etapas perturbado
  por igual. Diferencia de admitancia final ≤2 %; residual lineal ≤1e−10.
  Es un contraste diferencial local; no una trayectoria con carga nueva.
- Motor: estado de fase publicado sólo tras entrada válida; NaN/rate/BUS
  fuera de dominio se rechazan atómicamente. Rates 48–192 kHz, BUS ±2 V,
  panel α=.5. 52 armónicos ≤0.45 Fs. Medir heap y costo de un millón de
  muestras, sin atribuir deadline a toda la voz.

El perfil guarda DC, formas y frecuencia nominales derivados. No admite
CV general, otros rangos/selectores, noise, deriva, modulación, encendido,
memorias descartadas del VCO ni fidelidad al hardware. La cadena con ambos
contornos sigue pendiente de unión con este generador. No generar WAV.
Usar `tmp/lab-current`, guardar recibos y retirar binarios/exports al acabar;
si falla, preservar fixture y replay acotados antes de reparar.
