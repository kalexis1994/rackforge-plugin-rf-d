# ON/C27 y cadena nativa de 66 nodos: protocolo previo

Extender el puerto ON/C27 admitido al sistema nativo `circuit66`, sin
reescribir sus dispositivos, capacitor histories, constantes o controles.
Fuentes: SVC-9 Figs.9-17/9-11/9-8 pp.19/13/10 y las hipótesis de laboratorio
de la cadena existente. Mantener ambos candidatos de R61, 200 Ω/200 kΩ,
con Is/beta/temperatura y cargas documentadas del laboratorio nativo.
Fuentes OSC1/2/3, NOISE y EXT impuestas; no es un VCO nativo conectado.

## Red y método

BUS sólo entra en C27, entre pin4 y BASE_Q29 (nodo6). Eliminar BUS mediante
el puerto dinámico y sustituir exclusivamente la corriente/tangente de
C27 en la fila6. Los otros 65 nodos y las otras memorias conservan su ley.
Al adaptar el Jacobiano anterior, restar el stamp C27 fijo y añadir el
reducido. Limitar este primer adaptador a dt=0,5 µs..1 ms: la resta de
conductancias no autoriza pasos arbitrariamente pequeños. Contrastar
su Jacobiano y residuales frente al sistema nodal sin reducción.

Newton global conserva histories originales durante todos los trials,
predictor y fallback; budgets 1..16 iteraciones y 1..16 halvings. Admisión
simultánea: todas las KCL <1e−11 A, constraint de R21 <1e−11 V y corrección
Newton completa <1e−8 V. Sólo publicar la solución final, incluidas C27,
C10 y las 17 memorias; fallo conserva el estado del llamador bit a bit.
No interpolar fuentes o avanzar estados en una búsqueda numérica.

## Oráculo reservado y gates

Python monta los 66 nodos anteriores más BUS y cursores interiores de
la red resistiva original. No usa la reducción Rust para resolver; Euler
con historia explícita en C27 y todas las demás cargas. DC propio y 16
pasos por escena a 48 kHz: ambos R61 × dos redes (sólo OSC1 / cinco ON),
con α=0,5 y fuentes bipolares impuestas. Se conserva cada error del solve.
Presupuesto independiente 40 iteraciones/32 halvings, Jacobiano FD.

Comparar las 66 tensiones, BUS y 18 memorias: <1e−6 V; seis corrientes
de puerto: <1e−9 A. Comprobar KCL, carga C27 y salidas J4/J5/J7 en cada
paso; Jacobiano de todas las columnas en un estado no trivial por FD:
1e−8 S+2e−5·|Y_fd|. Test de fallo atómico y rechazo de dt fuera del dominio.
No emplear salidas nativas como semillas del oráculo independiente.

Conservar snapshots exactos de fuentes, toolchain, commands y binarios.
Durante la campaña SPICE larga, compilar una raíz de laboratorio que
referencie los módulos de producción por rutas explícitas, con identidad
de sus fuentes; export público al núcleo sólo después de pasar los gates.
No alterar fuentes o helpers congelados de la campaña SPICE activa.
No audio nuevo, contorno nativo integrado, VCO nativo, RT o fidelidad física
por este banco; el destino J7 sólo identifica una ruta eléctrica nominal.
