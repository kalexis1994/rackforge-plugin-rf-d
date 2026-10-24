# Familia H128 conectada a la entrada real del filtro

Protocolo previo, 2026-10-24. Usar la cadena nativa de carga de 68 nodos
ya contrastada, SVC-9 Fig.9-11 p.13, Fig.9-8 p.10 y Fig.9-17 p.19.
BASE_Q29 (nodo6) deja de ser fuente ideal: tiene Q29, R54 y C27, con
filtro ladder, recuperación, dos VCA y salida/J7 conectados. No modificar
componentes, tarjetas, polaridades, controles o datos H128 anteriores.

## Fronteras y memoria

Trims/calibración/25 C y selector3/10/R6=.5 de FAMILIA_MIXER. CV fijos
-2.6/-1.6/-.6 V, otras entradas -2.1 V. L0: OSC1+EXT ON; L1: cinco
ramas ON, fuentes restantes a cero y potenciómetros .5. Desactivar OSC1
en OnMixer: su puerto R6/R45 lo aporta la familia una sola vez. BUS es
incógnita. R61=200 y200000 ohm son perfiles documentales separados.

Controles de mixer_chain_lab/control_boundary(0,true): cutoff=.5,
range=.1, R14=25k, loudness1/2=2 V, balances12.5/50 ohm, salida R21
interior2000 ohm y cargas originales. Son fronteras de laboratorio; no
contornos KEY activos, interpretación de perillas o un ejemplar vintage.
Conservar los 17 capacitores de chain_charge más C10 explícito, incluidos
C27 entre BASE_Q29/BUS y las cuatro celdas68 nF del ladder.

## Sistema acoplado y arranque

Estado HIGH/LOW de68 nodos y fase; solve conjunto69 incógnitas. Retener
el stamp analítico completo y sus cargas. Añadir sólo Ipanel_BUS y sus
derivadas BUS/fase, además de dphase/dt=f(CV,BUS). Fuentes de otros canales
cero. Trapezoidal implícito sobre carga, sin cancelar dos historias grandes:
DCnuevo+DCanterior+2*DeltaQ/h=0. La fase cumple el mismo orden. Newton
64 iteraciones/24 mitades, residual <=1e-13 A y fase<=1e-11 ciclos,
corrección <=2e-9 V y fase<=1e-11 ciclos. Publicación atómica tras aceptar.

DC propio de la cadena con fuente OSC1 media del ciclo (coeficiente0),
capacitores abiertos; BUS y BASE se resuelven. El generador de onda es
estacionario, no VCO físico con arranque propio. Iniciar fase0 desde ese
DC y conservar todas las diferencias de tensión de capacitor. No llamar
a esa condición un ciclo ya asentado o el arranque de la voz anterior.

## Contraste previo

Doce DC: dos R61, dos cargas, tres CV. Contrastar con ecuaciones Python
independientes de66 nodos, red del panel sin condensar y cargas originales.
Raíces de paso compartiendo la historia fija, sin sembrar con la solución
nativa: cuatro escenas seleccionadas (-1.6 V, ambos R61/cargas), fases
0/.37 y h=.5/2 us. Dieciséis raíces de69 incógnitas, Newton FD independiente.
Ese contraste usa la misma familia H128: no otro VCO independiente.

Comparación nodal <=1e-6 V; BUS/BASE <=1e-6 V, corriente terminal<=2 nA.
Oráculo FD: KCL<=1e-11 A, corrección<=1e-8 V, fase<=1e-11 ciclos.
Native conserva sus gates más estrictos. Derivadas del acoplamiento y
carga devuelta frente a FD relativas1e-5 más1e-10 absoluto. MNA del panel,
balance de C27 y corrientes por rama con signos explícitos.

Recorridos completos de un ciclo desde DC para R61=200/L1, CV=-2.6/-.6,
h=.5/.25 us, sin CV/KEY temporal. Refinamiento: BUS/BASE DC y norma
armónica1..8 <=10 uV; corrientes panel/C27<=2 nA; J7 DC<=.5 mV,
norma armónica relativa<=2% (o absoluta<=1e-6 V cerca de cero).
Frecuencia<=1 cent. Conservar DC y mismo reloj/estado de arranque;
integrar hasta la primera vuelta real de la fase del reducido.
Esto califica esos ciclos completos, no asentamiento periódico o RT.

Rechazos de dominio o presupuesto deben conservar estado; retry válido
por bits. Medir cero heap en pasos y resolver controles negativos de BASE
impuesta y R45 duplicada. No generar otra escucha en este bloque.

## Recursos

Un tmp/lab-current vacío al inicio/final, sin Cargo, rlib/cache nueva o WAV.
Usar compiler y biblioteca congelados por QA, h≥MIN_DT de chain_charge.
Cada proceso<=240 s, compile<=120 s, export<=256 MiB, reserva1 GiB;
evidencia nueva<=32 MiB sin QA. Conservar HIGH/LOW de raíces seleccionadas,
ventanas completas de estos ciclos y digests. Fallos/replays con fuente
antes de corregir. Heredar tests anteriores por identidad, no reejecutarlos
o contarlos como pruebas nuevas. No cambiar la voz activa o su escucha.
