# Condición inicial conjunta y asentamiento local

2026-10-09. Perfil CA3046 nominal anterior, SVC-9 pp.5/19/13/10.
VCO1→BUS→cadena hasta J7, OSC1 solo, R61=200 Ω, controles nominales
constantes del builder previo. Mantener todas las leyes y el motor temporal.

## Inicialización condicionada

Resolver200 coordenadas DC con capacitores abiertos y una sola fila
sustituida: RAMP_C1=0 V en fila43. Registrar la corriente necesaria de
esa restricción; no llamarlo DC libre del oscilador o arranque desde
semilla analítica propia de toda la voz. La semilla sigue siendo el lift
histórico; el resultado debe resolver conjuntamente las cargas estáticas.
No copiar ese estado a una trayectoria ya iniciada ni resetear capacitores.

Newton64/24, residuo1e-13 A/1e-11 V y corrección2e-9 V/2e-12 A,
iguales a los contratos anteriores. Memoria e incrementos high/low.
Dos semillas (lift histórico y perturbación+1 mV de coordenadas de cadena
excepto BUS) deben alcanzar la misma raíz local a1e-6 V/1e-9 A.
Esto no prueba unicidad global. Oráculo VCO Decimal100 y cadena Python/FD:
200 residuos y corrección por raíz, puertas2e-11 A/2e-10 V y1e-6 V/1e-9 A.

Publicar raíces y matrices DC/carga completas. Comparar cadena DC con
el oráculo Python y matriz de carga con las18 incidencias explícitas.
Usar una pequeña señal impuesta en BUS para diagnóstico de cadena:
resolver(G+jωC)x=b, fila BUS=1, en10 Hz,100 Hz, frecuencia410,80175922051075
Hz del ciclo conservado,1000 Hz y10000 Hz. Comparar con el oráculo
FD independiente: error complejo<=1e-6 V+1e-4|referencia|; residuo complejo
<=1e-10 A para1 V de estímulo, BUS<=1e-12 V. La ganancia es una
linealización de cadena en DC condicionado, no respuesta no lineal de voz.

Estimar polos locales a través de G^-1 C con BUS fijado: comprobar
residuo de autovectores<=1e-8 relativo, conservar modos algebraicos y
conjugados, informar modos activos/inestables sin asumir pasividad.
No promover su escala temporal como cota global de asentamiento. No
ampliar la trayectoria ni producir escucha solo por este diagnóstico.

## Liberación y recursos

Dos continuaciones desde la raíz condicionada, máximos125/62,5 ns,
hasta2 µs exactos. Mantener LTE2 µV/2 nA, balances C1/BUS1e-12 A,
comparación al mismo reloj2 µV/2 nA. Contrastar full/mid/end del primer
y último intervalo: candidatos nativos declarados. La corriente de
restricción no permanece en el motor dinámico. No acredita reset/ciclo
de esta nueva inicialización; el banco anterior conserva su propia semilla.

Compilador fijado, O2 y stack32 MiB. Reserva1 GiB, estimación12 MiB
adicionales, ejecutables con strip=symbols. Tiempo180 s por proceso,
600 s total; no borrar evidencia protegida. Guardar fallo y replay sin
cambios antes de reparar. No audio/SPICE nuevos, fidelidad o RT.
