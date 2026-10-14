# Puerto del contorno de filtro con carga Q26/Q28

2026-10-14, base `50d88846fedaf7e374493a6820b09fba10571f34`, QA `cutoff_ab_tests01.json`. Perfil documental CA3046 vintage; sin hardware. Primer cierre funcional del seguidor de filtro, Amount of Contour y control Q26/Q28. No sustituye aún el gatillo, biestable o C5 por un generador completo.

## Topología revisada antes de implementar

SVC-9 PDF p9, Fig9-7 (página impresa9-5), p19 Fig9-17 y p13 Fig9-11; copia completa SVC-204D p65 para verificar pines. Q22 NPN: base por R48=10 kΩ desde C5, colector a base Q21, emisor a salida11B. Q21 PNP: emisor a alimentación por R50=560 Ω, colector a salida11B. Es un par complementario con realimentación, distinto del Darlington NPN/NPN de volumen. Salida→R33=5,6 kΩ→feedback; feedback→R29=16,9 kΩ→−10 V; CR3 1N34A ánodo feedback/cátodo base Q4. C11 opcional47 pF une colector Q22/base Q21 con emisor Q21. C12 opcional500 pF involucra el temporizador: queda omitido y declarado para el siguiente cierre.

Salida11B llega al extremo de R17 Amount of Contour, 50 kΩ; otro extremo a masa, cursor→pin16placa4→R74=47 kΩ→base Q26. Es una carga sobre el seguidor, no una fuente ideal multiplicada por amount. Q26 PNP/Q28 NPN, C18=100 pF, R45=330 Ω, R60=680 Ω y panel restante conservan [derivación y fuentes](CUTOFF_NATIVO_Q26_Q28.md). Retirar exactamente una rama R74 desde la fuente impuesta al cerrar la red nueva.

Reducción exacta del cursor: ru=(1−a)R17, rl=aR17, D=R74·R17+ru·rl; go=(R74+rl)/D, gx=−rl/D, gp=R17/D. Corrientes OUT/Q26=G·[Vout,Vq26] respecto de masa, G=[[go,gx],[gx,gp]]. Vcursor=(R74·rl·Vout+ru·rl·Vq26)/D. Topes0/1 exactos, sin epsilon; R17 siempre carga OUT y R74 siempre conecta el cursor. a es fracción eléctrica desde masa, sin curva angular calibrada.

## Modelo y fronteras

Nueve nodos: base Q22; Q22C/Q21B; Q21E; salida; feedback; Q26B; Q26E/Q28B; Q26C; Q28C. Ocho puertos explícitos TIMING_C5/RESET_Q4/TAIL/SUPPLY9,3/MINUS10/CUTOFF_TH/RANGE_TH/GROUND. C5, reset, alimentación y TAIL se imponen; sus corrientes/tangentes permiten el cierre futuro. R11 de panel reduce a Vth=−10+20α V y R=200k+5000α(1−α) Ω; RANGE a Vth=10b V y R=68k+10000b(1−b) Ω. Ground debe conservar su retorno. Contorno/gatillo completos y voz229 no se promueven por este puerto.

BJTs Ebers–Moll Is10⁻¹⁴ A/βF100/βR5/298,15 K y CR3 Shockley Is10⁻⁸ A/n1,5: hipótesis nominales heredadas sin identificación vintage. Sin Early/ruptura/carga de junturas del nuevo seguidor. C11=0/47 pF son escenarios separados; C18 siempre100 pF. Companion Euler implícito con historial fijo para todos los trials. Respuesta provisional; sólo `step` convergido publica nodos/cargas, fallo atómico.

## Gates fijados

Banco DC: amount0/0,5/1, C5 en[0;0,85;3;6;9,3] V, reset[0,01;0,7] V, cutoff[0,5;1], TAIL1,4 V:60 casos, con C11 abierto en DC. Oracle independiente con ramas originales y cursor sin reducir en casos interiores, topes unidos exactamente; Jacobiano FD. Contrastar raíces nativas≤1 µV, puertos≤1 nA, todas las columnas de stamp y todas las tangentes de puertos≤2 nS+2e−5·|referencia|. KCL nativo≤10 pA y corrección≤10 nV; oráculo≤1 pA/10 nV. No imponer reciprocidad al bloque activo.

Trayectorias: dos variantes C11 y dos máximos de paso8/4 µs durante128 µs, C5 de0,85→3 V en32 µs y de3→0,85 V en96 µs, reset0,01 V, cutoff0,5/amount0,5/TAIL1,4 V. Comparar los nueve nodos a relojes comunes≤2 µV y cada corriente de puerto≤2 nA. Verificar ΔQ de C11/C18 y suma de KCL/retornos≤20 pA, replay completo por bits, llamadas provisionales sin publicar y rechazos de parámetros/historial/budget/overflow. Estas duraciones son estímulos de laboratorio, no ADSR ni audio nuevo.

Compilar llamador con biblioteca congelada, sin Cargo/cache/SPICE; no modificar fuentes anteriores. Límites privados32 MiB, reserva1 GiB, procesos≤300 s; preservar fallo/fuente/replay sin cambios antes de reparar. Publicar sólo el puerto que pase, con fronteras documentadas. Sin voz completa, calibración, fidelidad física, heap/deadline o RT nuevos.

## Admisión local posterior al estrés rechazado

El intento native02 conserva el estrés 0,85→3 V y su replay sin cambios: ecuaciones originales y tangentes pasan, pero 8/4 µs discrepan 668,677 µV y 622,610 nA. Ese recorrido grande sigue rechazado. No ampliar tolerancias ni sustituir su resultado por otro estímulo.

El siguiente banco mantiene los 60 DC y declara por separado una excitación local de 1 mV: C5 0,85→0,851→0,85 V, con iguales relojes, pasos, variantes C11, historia y gates. Comprueba el puerto y su pequeña señal dinámica; no acredita el salto grande, ataque de una nota, contorno completo ni integración a la voz. El comportamiento a gran señal de C5 requiere su temporizador continuo y un método/paso con refinamiento admitido. El banco conserva el estrés como modo predeterminado; `--local` selecciona esta cobertura reducida y explícita.

El banco ampliado emite las 289 entradas del Jacobiano completo de nueve nodos y ocho puertos en cada paso local, ademas de DC, manteniendo la historia fija. Mismos gates FD; las 64 tangentes cargadas se contrastan tambien en cada paso.

La variante C11 queda vinculada al estado publicado. Rechazar cambios 0↔47 pF durante una trayectoria sin publicar nada; una nueva variante comienza con su propio DC. Amount/cutoff pueden cambiar, conservando la historia capacitiva. Se suman cuatro rechazos de receta a los veinte casos inválidos originales. `linearize/solve` siguen siendo operaciones matemáticas condicionadas a la receta suministrada; `provisional/step` comprueban el binding del estado.
