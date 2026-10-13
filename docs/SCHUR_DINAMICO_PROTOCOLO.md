# Condensación dinámica de los dos LM741

Antes de medición, 2026-10-13. Base48543a7, voz229 CA3046 condicionada.
Partición documental: OPAMPS en vco1_stamp_data.rs; SVC-9 p.5/p.19,
tarjeta TI nominal y [contrato previo](VCO1_741_CONDENSACION_PROTOCOLO.md).
La tarjeta es un macromodelo nominal, no identificación del integrado vintage.

## Contrato de memoria y puertos

Dos interiores de32 incógnitas por etapa; cada bloque une ambas etapas
Radau,64×64. Dos bloques independientes a través de sus terminales:
eliminar128 correcciones y resolver330 exteriores. Conservar cinco
terminales de cada integrado (IN+/IN−/V+/V−/OUT); V+ de IC1 vuelve a
suelo físico y no se convierte en otra incógnita. Validar que no aparecen
acoplamientos interiores fuera de esos puertos ni entre ambos interiores.

Para J·d=b: factorizar A=Jii una vez, resolver u=A⁻¹bi y W=A⁻¹Jip;
S=Jee−JeiW, q=be−Jeiu. Resolver S·de=q y reconstruir di=u−Wde.
Se parte del Jacobiano Radau completo, incluidos G y B·M/h de ambas
etapas. El RHS conserva la historia HIGH/LOW original. Sin cambiar
dispositivos, GMIN, h, fuentes, Newton o tolerancias; sin inversa explícita.
Se reponen458 correcciones antes de probar convergencia. Ninguna carga
sale del estado aceptado: C4/C3/C5 y L2/L3 de cada 741 conservan sus
tensiones/corrientes, además del resto de la voz. Los puertos se evalúan
con las funciones originales sobre estados reconstruidos.

## Gates previos

Banco84 pares congelados del ciclo con contorno. Cambia el orden de
eliminación: no exigir bits como identidad algebraica de binary64.
Comparar correcciones de un mismo J/b a2 nV/2 pA y backward error
normalizado≤1e-11 (denominador |b|+Σ|Jd|, fila cero exige residuo cero).
Comparar candidatos/incrementos completos a2 µV/2 nA; residual y
corrección de Newton mantienen gates originales. Medir reconstrucción,
puertos de ambas etapas y cinco memorias por integrado. Verificar raíces
nuevas con el grafo/FD/Q Decimal100 original antes de admitir trayectorias.

Singularidad interior/exterior se rechaza explícitamente; no regularizar
ni ocultar el fallo con un solve completo. Conservar salida/fuentes y
replay antes de reparar. Sólo si pasa el banco, ejecutar los cuatro
recorridos propios de3.004 ms y contrastar229 coordenadas al mismo reloj,
2 µV/2 nA, tiempos de reset10 ns y balances1 pA×duración. Comparar también
con la referencia anterior en esos relojes; no heredar ecuaciones nuevas
por identidad si los estados difieren. Restores/rollbacks originales.

Cinco rondas alternadas de costo en el banco, warmup separado, mediana>1
para admitir utilidad. Compilación120 s, banco600 s, perfil900 s,
campaña4000 s, auditor600 s;64 MiB privados nuevos/reserva1 GiB,
stack32 MiB. Biblioteca congelada;248 tests heredados, no reejecutados.
Sin audio nuevo, nueva duración, ajuste físico o admisión RT.
