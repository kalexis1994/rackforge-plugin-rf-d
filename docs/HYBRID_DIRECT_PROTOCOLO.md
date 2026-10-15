# Ensamblado directo de Radau en Schur y CSR

## Cambio y alcance fijados antes de medir

Desde el ensamblado contiguo admitido, eliminar la matriz intermedia de
236×236 f64. Leer por referencia las matrices DC/masa de ambas etapas,
calcular cada coeficiente con la misma fórmula, verificar finitud y
partición, y copiar los no nulos al bloque/borde/cruce correspondiente
y al CSR para el residual compensado. No reutilizar números de otra
etapa, estado o h. Inicializar a cero todos los bloques en cada solve.

La partición sólo indica pertenencia física: contorno, audio o puertos
VCA_BASE/TAIL. Toda celda real se inspecciona, sin máscara de sparsity
aprendida de una escena. Un enlace nuevo dentro del mismo interior debe
aparecer; un enlace inesperado entre interiores debe rechazar. El CSR
mantiene orden ascendente de filas/columnas y el mismo piso de precisión.
Pivoteo, factores, reconstrucción, backward y refinamiento no cambian.

Voz nominal CA3046/SVC-204D, 40–100 ms, KEY OFF 75 ms, semilla HIGH/LOW,
perfil VCO, reloj, cargas y constantes del bloque anterior. Fuentes
físicas heredadas SVC-9 pp.9/13/19 y p.10. Sólo representación numérica,
sin nueva constante audible ni ampliación de dominio físico.

## Gates previos

- 24 matrices: reconstruir el CSR real del inicializador del candidato
  y comparar todos los 1.336.704 coeficientes bit a bit con la fórmula
  anterior. 192 direcciones iguales bit a bit al Schur anterior y dentro
  de 2 nV+1e-7·abs(ref) del monolítico refinado.
- 24 inserciones legales nuevas y retiro posterior sin coeficientes
  residuales. Rechazos y retry válido exacto para no finitos de DC/masa,
  pesos/RHS, enlaces entre interiores, capacidad agotada y matriz singular.
- Dos trayectorias propias, techos full 64/32 µs, 481 observaciones cada
  una, y todos los estados finales frente al contiguo: nodos/estados
  20 µV+2e-6·abs(ref), cargas 2 nA+2e-5·abs(ref), J7 RMS 0,1 %, pico
  0,3 %, media 1 µV. Mantener gates heredados de voz completa/refinamiento.
- Auditoría original de 24 pares/5712 filas con Amount: 20 pA/2 nV;
  candidatos nativos auditados, sin otra trayectoria original independiente.
- Newton 1 pA/2 nV, backward ≤1e-11 y hasta tres refinamientos; estimador
  sin cambios, heap cero en integración, ocho replays y diez rechazos
  atómicos de paso. Etapas/FD eléctricas se heredan por identidad.
- Control contiguo fresco al techo 32 µs, mismo compiler/rlib/flags/equipo,
  sin timers internos. Ratio candidato/control ≤0,90; no se interpreta
  una medición como resultado estadístico o deadline de producción.

Un `tmp/lab-current`, binarios/semilla retirados después de recibos;
fallos con fuente/entrada/replay conservados antes de corregir. Sin WAV,
carpetas de muestras, Cargo o biblioteca nueva. Dominio offline nominal;
arranque, CV general, antialias de producción y fidelidad física abiertos.

## Rechazo de costo y siguiente transformación

El primer candidato conserva matrices, direcciones y trayectorias, pero
cuesta 0,921727 del control: rechazo frente al gate 0,90, con fuentes,
entrada y replay sin cambios en `hybrid_direct_native01.json`.

El siguiente conserva el ensamblado directo y omite dividir candidatos
de pivote exactamente cero. Las escalas de fila ya se comprueban positivas;
abs(0)/escala es cero y nunca supera best, que empieza en cero. Conservar
orden y división de todos los candidatos no nulos, swaps, umbral singular,
eliminación y refinamiento. No hay nuevo ordenamiento, tolerancia o máscara.
La aceleración eventual pertenece al conjunto de ambas transformaciones.
Se repiten los gates completos y un control fresco, sin cambiar 0,90.


El segundo también falla costo: 0,929258, recibo/replay 02. Un perfil
del candidato (`hybrid_direct_profile01.json`) mide ensamblado/inspección
2,6161 s y factores 3,9842 s; incluye replays, sin desglose completo de
line search/rechazos. No prueba que omitir divisiones haya acelerado.

El siguiente comprueba que los cuatro pesos son finitos, e identifica
coeficientes cuyos términos DC/masa reales son ambos cero antes de
multiplicar. Continúa inspeccionando cada entrada, incluyendo enlaces
nuevos y cancelaciones entre términos no nulos. Sólo evita aritmética
para un cero probado desde los inputs; no usa una máscara de soporte.
Calcula el máximo absoluto de cada fila interior al cargar sus valores,
sin recorrer la matriz densa otra vez para las escalas. Excluye bordes de
ese máximo igual que el control, conserva swaps/orden/umbral de pivote y
verifica la finitud completa de los factores calculados. Se añade un
probe de cancelación que conserva el término en la otra etapa. Mismos
gates completos y control fresco. Atribuir el costo al conjunto medido.
