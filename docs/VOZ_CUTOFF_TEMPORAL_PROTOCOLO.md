# Cutoff temporal con VCO y carga conjunta

2026-10-12, previo a ejecución. Model D CA3046 nominal, misma escena del
[candidato adaptativo](VOZ_CANDIDATO_CICLOS_RESULTADOS.md). OSC1 ON por
SW6/alpha=0,5; otras entradas OFF, R61=200 Ω, RANGE=0,1, VCAs=2 V.
Sólo cutoff eléctrico cambia: 0,5 (control nominal) o1 (apertura). Fuente:
SVC-9 Fig.9-11 p.13 y Fig.9-17 p.19, reducción del panel Q26/Q28
[ya contrastada](CUTOFF_NATIVO_Q26_Q28.md). No nuevo componente o trim.

Se reutilizan por bytes los dos checkpoints iniciales del candidato a=1.
El cambio de fuente se aplica en t=0 sin resolver otra raíz ni reescribir
las cargas. Los nodos algebraicos se resuelven junto al resto en cada
paso aceptado. No se declara que el estado inicial sea DC del panel nuevo.
Los parámetros del checkpoint se reconstruyen con la receta explícita
de cutoff; el codec sólo transporta estado/reloj/propuesta/settings.

Cuatro perfiles propios, hasta250 µs, máximo medio paso125/62,5 ns.
Relojes comunes: 2/16/64/125/250 µs. Coarse/mid/end seleccionados en el
primer intervalo y en cada reloj: seis selecciones, 18 candidatos por
perfil, total72/28800 ecuaciones independientes, 48 observaciones de
corrientes VCO y24 LTE. Auditor VCO Decimal100 heredado; cadena Python
con KCL propias y FD1 µV, cambiando sólo el panel. No modificar globals
del auditor anterior ni sus gates. No búsqueda independiente de raíces.

Gates heredados: residual2e−11 A/2e−10 V, corrección1 µV/1 nA;
LTE y estados al mismo reloj2 µV/2 nA. KCL C1/BUS/C18≤1e−12 A,
balance C1≤0,002, C18/C27≤1e−12 A·duración; identidades de media
del panel≤1e−9 V. Restore en0 y64 µs de cada perfil, estados e
incrementos por bits, ratios/relojes/h/intentos. Nominal: estado a2 µs
por bits contra el banco anterior, y250 µs al mismo reloj con gates.

C18=100 pF en nodo62 de la cadena (joint195): integrar la KCL estática
de sus dos etapas con pesos Radau3/4,1/4 y verificar ΔQ+∫I_DC=0.
Corriente de cola=(VTAIL−VQ28C)/680 Ω. Conservar estas observaciones,
estados completos en relojes, traza J7/BUS y ledger C27. Efecto del
control: C18 final cambia≥1 mV y cola final aumenta≥1 % frente al nominal
en ambos perfiles. Publicar cambios/offset/extremos muestreados de J7;
no exigir54× ni interpretar250 µs como un ciclo, nota o asentamiento.

Biblioteca/compilador anteriores; cuatro procesos seriales con stack32 MiB.
Compile≤120 s, perfil≤900 s/12000 intervalos, total≤3800 s,
administrativo4200 s; auditor≤300 s. Reserva disco1 GiB, estimación32 MiB.
Vigilancia250 ms; conservar stderr/stdout, final y datos parciales.
Rechazo eléctrico: repetir el advance exacto con el mismo cutoff y
checkpoint, comprobando rollback. Fallo de auditor: conservar fuente,
excepción y repetición idéntica antes de reparar. No nueva biblioteca,
audio, SPICE, fidelidad física o RT.
