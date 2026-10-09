# Prefijo conjunto desde DC condicionado

2026-10-09. Extender la liberación desde 2 µs hasta 500 µs, exactamente
262.144.000 ticks (125 ns/65536 por tick), en dos perfiles de media etapa
máxima 65536/32768. Misma escena CA3046, misma semilla importada y misma
raíz condicionada del banco anterior. Retirar la restricción al liberar.
No sustituir cargas en una trayectoria ya iniciada.

El caller se deriva del banco de ciclos antiguo con tres cambios declarados:
duración, condición conjunta antes de construir el Engine y gate final de
un replay de restore (a 250 µs), sin exigir dos resets en un prefijo de
500 µs. No cambiar física, algoritmos, tolerancias ni observer de C1/BUS.
La copia anterior sigue congelada. Biblioteca compilada del banco de
inicialización identificada por SHA256; compilar únicamente el caller.

## Gates previos

- Checkpoint inicial: las 400 componentes high/low idénticas a raíz0 del
  recibo de inicialización. No comparar solo sumas ni contenedores JSON.
- Ambos perfiles completos hasta el reloj declarado, checkpoints comunes
  en 0, 250 y 500 µs; 200 coordenadas a 2 µV/2 nA y precisión Decimal100.
- Cada intervalo publica solo ambas medias etapas admitidas, metadata y
  clocks exactos. Gates nativos heredados residual/corrección/LTE<=1,
  BUS y C1 instantáneos<=1e-12 A. Cuadratura Radau conserva Qa/Q10/Q7,
  suma compensada y balance relativo integrado de C1<=0,002.
- Selecciones primera y última por perfil: full/mid/end, dos etapas cada
  par; contraste independiente de 4800 ecuaciones y 24 corrientes de
  terminales (tres corrientes en ocho endpoints), gate 2e-11 A heredado.
  LTE seleccionado<=1 con historias encadenadas y referencia Decimal100.
- Restore a 250 µs: replay bit a bit del próximo intervalo, excluido
  de contadores e integrales. Final.ckp idéntico al último checkpoint.
- Exports compactos sin pérdida, hashes antes/después y codec heredado.
  Este prefijo no admite frecuencia de ciclo, periodicidad ni nota asentada.

## Recursos

Presupuesto por perfil 10.000 intervalos/300 s; total 700 s, caller compile
120 s. Estimar 16 MiB de outputs antes de lanzar, reserva mínima 1 GiB.
Muestrear disco cada 250 ms; stop cooperativo con checkpoint ante incumplir
reserva o presupuesto, terminación solo tras 20 s de gracia. Conservar
recibo parcial, sources, trace y checkpoint si falla; replay inmediato
de rechazo eléctrico desde ese checkpoint. No aumentar presupuestos en
silencio ni reinterpretar un stop administrativo como fallo eléctrico.
Stack de laboratorio 32 MiB; heap y deadline de audio no medidos aquí.

Los modos locales anteriores orientan la investigación; no proporcionan
un certificado de este prefijo no lineal. No generar audio en este banco.
