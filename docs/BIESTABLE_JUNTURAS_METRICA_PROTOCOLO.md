# Protocolo: métrica cuadrática común por intervalo

Congelar helper, productor y este protocolo antes de medir. Mantener
CA3046, parámetros sintéticos, pesos, 64 celdas y ocho intervalos no contiguos.
No cambiar circuito, audio, gates o datos previos. Evaluar los ocho casos;
no elegir norma por resultado ni intersectar variantes de normas distintas.

## Candidato único

Para cada intervalo formar el hull de sus ocho recintos firmados B_JJ.
Elegir rho, potencia de dos >=max(1,||hull||infinito), con unidades 1/s.
Redondear el centro de hull/rho a 40 bits diádicos, nearest-even exacto.
Resolver CᵀP+PC=-I en las diez incógnitas simétricas por eliminación racional.
Registrar singularidad o pivote no positivo de LDLᵀ, sin regularizar ni
buscar otra métrica. Si P es positiva definida, normalizar traza a cuatro
y redondear de nuevo a 40 bits. Exigir LDLᵀ estrictamente positivo del
P final; éste, no la solución sin redondear, se usa en toda la prueba.
Estas ocho resoluciones son sistemas de métrica numérica, no del circuito.

La [teoría cuadrática de Lyapunov, Stanford EE363](https://web.stanford.edu/class/ee363/notes/lq-lyap-notes.pdf),
consultada 2026-10-03, motiva el candidato. Estabilidad de su centro no
constituye el certificado de la familia. P permanece constante en las
ocho celdas: no hay término P'(t), cambio de coordenadas ni transición
de métrica dentro del intervalo. No es una métrica común a los ocho
intervalos seleccionados; cualquier unión futura requiere sus conversiones.

## Tasa uniforme con incertidumbre

Para cada B/rho calcular S=(PB/rho+(B/rho)ᵀP)/2 mediante intervalos firmados.
Centro C_S y radio simétrico R dan S<=C_S+delta*I, delta=max_i sum_j Rij.
Un LDLᵀ exacto positivo de alpha*P-C_S-delta*I certifica
S<alpha*P para toda la celda. Luego mu_P(B)<=rho*alpha.
Seed estricto superior: (||C_S||infinito+delta)*||P^-1||infinito+1;
inferior negativo de ese seed. Hacer 32 bisecciones racionales, conservando
probes, pivotes y prueba superior. El inferior corresponde al problema
auxiliar C_S+delta*I; **no es cota inferior de la mu_P real**.
Una tasa superior negativa certifica contracción del bloque interno variable,
en esta métrica fija, con sus entradas externas tratadas por separado.

## Conversiones completas

z=W_J e_J; a>=sqrt(max_{s en {+-1}^4} sᵀP s)/2 mediante raíz racional
exterior de 256 bits. Fijar u_J=sqrt(zᵀPz)/(2a) para conservar el anclaje
común ponderado infinito <=1. Usar el máximo de los 16 vértices; el centro
o la traza no bastan. P^-1 exacta determina la norma dual.

En cada vector intervalar, acotar vᵀP v con cuadrados de intervalos y
términos cruzados firmados antes de tomar la raíz. Junturas→otro bloque:
2a*max_fila ||fila||_{P^-1}. Otro bloque→junturas: suma de normas P de
sus columnas dividida por 2a. Forzamiento: suma de normas P de columnas
ponderadas por sus presupuestos L1, dividida por 2a. Salida nodal:
2a*norma dual de cada fila H_inverse[node,J]/W_J. Conservar otros cinco
grupos, forzamientos, ganancias y términos nodales directos idénticos.

Reconstruir las mismas inversas Neumann certificadas, no nuevas resoluciones.
Propagar seis normas con los núcleos exteriores anteriores, anclaje inicial
de unos y forzamiento tardío. Guardar todas las cotas y conversiones incluso
si empeoran; rechazos de candidato permanecen explícitos, sin nueva
propagación para ese caso. Comparar sólo después con la variante RMS/espectro.

## Regresiones y alcance

Verificar ecuación racional del candidato, redondeo, pivotes singulares,
indefinidos, norma y dual, vértices, cuadrados que cruzan cero, tasa para
matrices conocidas y familias estables sin métrica común contractiva.
Reconstruir todos los candidatos, tasas, conversiones y propagaciones;
contrastar productos cuadráticos por método independiente y conservar SHA
antes/después, datos, fuentes y todo intento fallido.

Contracción del bloque interno no certifica el circuito completo, ni
restos no lineales, anclaje, recorrido, error global de 1 mV, física, audio
o deadline. Esta métrica es una herramienta numérica, no parámetro audible.
