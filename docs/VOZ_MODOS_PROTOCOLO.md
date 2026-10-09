# Excitación y observación de los modos de carga

2026-10-09. Diagnóstico previo; revisión CA3046 nominal, misma raíz conjunta
condicionada y matrices del banco de inicialización. No modificar el circuito,
la historia anterior ni los gates. No requiere una nueva simulación temporal.

## Pregunta y frontera

Los 18 tiempos locales anteriores no indican por sí solos cuánto aparece cada
modo en J7. Cuantificar la excitación desde BUS y la observación en J7, además
de la distribución de energía entre capacitores. BUS es una frontera de tensión
ideal en este diagnóstico; sus polos no son los de VCO1 conectado dinámicamente.
Las 50 coordenadas algebraicas no se cuentan como polos finitos.

## Reducción y reconstrucción

Usar G con fila BUS=1, C con fila BUS nula, E de incidencia de las 18 cargas,
E' con fila BUS nula y Z=diag(sqrt(C_k)). Definir L=G^-1 E' Z,
T=Z Eᵀ L, f=G^-1 e_BUS y d=Z Eᵀ f. Con T=V diag(τ) V^-1,
o=L V y a=V^-1 d, la respuesta nodal se reconstruye como

`x(s)=f-s Σ o_k a_k/(1+s τ_k)`.

Para J7, `K_k=o[J7,k] a_k/τ_k` es el peso de un término pasa bajos;
el residuo en la variable s es K_k/τ_k. Guardar ambos, incluyendo signo y
partes complejas. El término algebraico directo es `f[J7]-Σ K_k`.
No descartar términos pequeños ni sumar sus magnitudes como ganancia AC.
Conservar todos los 18 modos. Guardar condición de V y residuo de inversión.

La fracción de energía del capacitor i en el modo k es
`|V[i,k]|²/Σ_i |V[i,k]|²`: son coordenadas sqrt(C)·V, no voltajes nodales.
Es una distribución por modo local (también para pares complejos), no una
atribución causal exclusiva a un componente ni una medición física.

## Gates declarados

- Incidencia: error máximo C<=1e-15 F. Residuos de autovectores <=1e-8,
  misma norma que el banco anterior. Inversa V: residuo relativo <=1e-10.
- Reconstrucción nodal: comparar con solución directa en 27 frecuencias
  (25 logarítmicas de 0,01 Hz a 1 MHz, DC y 410,80175922051075 Hz).
  Gate `1e-10 V/V+1e-8 |directa|`; no usar comparación de magnitudes solamente.
- Contraste independiente: FD central 1 µV del oráculo anterior y C de su
  incidencia; gate nodal `1e-6 V/V+1e-4 |referencia|`, heredado del banco AC.
- Escalón formal normalizado: comprobar `G x+C x'=e_BUS` a 0+, 1 µs,
  1 ms, 5,25 ms, 20 ms, 100 ms, 265 ms y 1,3 s; residuo físico<=1e-10 A,
  frontera<=1e-12 V, parte imaginaria nodal<=1e-10 V.
  A 0+ todas las cargas incrementales deben ser nulas dentro de 1e-10 sqrt(F)·V.
- Reconstrucción de transferencia también con la forma de pesos K; guardar
  la cancelación DC y el límite algebraico. No afirmar asentamiento global.

El escalón de valor 1 es normalización de un sistema lineal local; no representa
un salto físico de 1 V validado en el circuito no lineal. Para ilustrar la
envolvente, escalar formalmente a 1 mV y buscar el tiempo en que
`Σ |K_k| exp(Re(-1/τ_k)t)` sea <=0,001 V/V (1 µV referido a ese escalón).
Solo calcularlo si todos los polos tienen parte real negativa. Guardar la
envolvente y el error firmado: la cancelación entre modos puede ser grande.
Ese tiempo no será una duración de calentamiento obligatoria para RF-D.

## Recursos y evidencia

Reusar matrices exportadas, sin compilación, SPICE, audio ni nuevo trace.
Registrar espacio libre antes y después y duración; no relajar la reserva
de 1 GiB para lanzar bancos temporales. Conservar recibos fallidos y replay
antes de corregir. Verificar identidad de fuentes y matrices antes/después.
La falta de espacio bloquea el banco largo, no este análisis en memoria.
