# Radau directo a interiores, frontera y residual

## Transformación admitida

El [generador](../tools/prepare_hybrid_direct.py) deriva el candidato desde
el ensamblado contiguo y el Schur admitidos. Recibe por referencia DC/masa
de ambas etapas y construye interiores 108/124, bordes/cruces de cuatro
puertos y CSR del residual. Evita materializar el objeto intermedio
236×236 f64, de 445.568 bytes; no se midió reducción de pico de stack.
El export denso de diagnóstico sólo se compila con `cfg(laboratory)`.

Se inspeccionan los términos reales de cada celda. Con pesos finitos,
dos términos cero permiten evitar la multiplicación; términos no nulos
se calculan con la fórmula anterior, incluidas sus cancelaciones. No hay
máscara de enlaces aprendida. Los máximos absolutos de fila interior se
acumulan al cargar coeficientes, excluyendo bordes igual que el control.
Se reinicializan todos los bloques y escalas en cada solve. El CSR sigue
ordenado por fila/columna y mantiene piso y residual compensado originales.

La [refinación](../tools/refine_hybrid_direct.py) también omite dividir
candidatos de pivote exactamente cero; conserva división/orden de todos
los no nulos. Escalas positivas, swaps, umbral, eliminación, comprobación
de finitud de factores y refinamiento siguen vigentes. Los números de un
solve anterior no se reutilizan como factores o escalas de otro estado/h.

Misma voz nominal CA3046/SVC-204D, 40–100 ms y KEY OFF 75 ms, perfil VCO,
historia HIGH/LOW, 118 estados, puertos y cargas. Sin constantes audibles
nuevas; leyes/fuentes físicas heredadas de SVC-9 pp.9/13/19 y p.10. El
dominio físico no se amplía a arranque, CV general u otra configuración.

## Contrastes ejecutados

[Protocolo previo](HYBRID_DIRECT_PROTOCOLO.md),
[recibo nativo](../evidence/hybrid_direct_native03.json) y
[auditoría original](../evidence/hybrid_direct_audit01.json):

- Reconstrucción del CSR real: 24 matrices/1.336.704 coeficientes iguales
  bit a bit al ensamblado anterior. No es otra copia de la fórmula como
  sustituto del inicializador ejecutado.
- 192 direcciones iguales bit a bit al Schur anterior y dentro del gate
  frente a monolítico refinado: máximo 0,972279 de 2 nV+1e-7·abs(ref).
  Es un contraste condicionado, cercano al gate para una dirección.
- 33 rechazos y retries válidos exactos: no finitos de DC/masa, pesos y
  RHS, enlaces entre interiores, capacidad CSR y singularidad. Capacidad
  devuelve InvalidInput; la matriz nula devuelve SingularJacobian.
- 24 enlaces legales nuevos se incorporan y después se retiran sin
  contaminación. Un probe de cancelación conserva el término no nulo de
  la otra etapa y restaura después el solve válido exacto.
- Dos trayectorias propias a techo full 64/32 µs, 962 observaciones y
  estados finales iguales al contiguo. Líneas ROOT/GRID/SOLVER serializadas
  idénticas antes del FINAL cronometrado; 99.922 solves/499 refinamientos.
- Backward ≤9,9852e-12; Newton ≤0,999722 pA/1,87210 nV; estimador ≤0,950788.
  Heap cero en integración; ocho replays de paso y diez rechazos atómicos.
- 5712 filas originales con Amount retenido: ≤0,719007 pA/0,325050 nV.
  Auditoría de candidatos nativos, sin otra trayectoria original independiente.
- Frente a voz completa, J7 RMS ≤1,067158 %, pico ≤2,607925 % y media
  ≤0,088947 µV. C2/C5, BUS, R59/R60 y refinamiento temporal pasan. Las
  48 etapas/472 columnas FD/26 guardas eléctricas previas se heredan por
  identidad de fuentes sin reejecutarlas; las ecuaciones no cambiaron.

## Rechazos, perfil y costo

El primer ensamblado directo pasó los gates numéricos pero falló costo:
ratio 0,921727. Omitir divisiones por cero tampoco pasó: 0,929258.
Ambos [recibos](../evidence/hybrid_direct_native01.json) y
[replays](../evidence/hybrid_direct_native02.json) conservan fuentes e
entrada sin cambios. No se redondearon ni se modificó el gate 0,90.

El [perfil del segundo](../evidence/hybrid_direct_profile01.json) midió
2,6161 s de ensamblado/inspección, 3,9842 s de factores, 0,8665 s de
sustitución, 0,1474 s de backward, 0,0048 s de refinamiento y 6,9568 s
de evaluación completa de Newton. Incluye cuatro replays y no atribuye
todo el line search/solves fallidos. Identifica el costo restante; no
prueba una aceleración aislada de omitir divisiones. El siguiente cambio
evita aritmética de ceros probados y el segundo recorrido para escalas.

| Ejecución sin timers internos | Tiempo por 60 ms simulados |
|---|---:|
| Contiguo fresco, techo 32 µs | 18,4483898 s |
| Directo final, techo 64 µs | 16,2331166 s |
| Directo final, techo 32 µs | 16,5512289 s |

Ratio **0,897164**, ahorro **10,28 % en este ensayo**. Pasa por margen
pequeño respecto de 0,90; una medición secuencial no acredita estabilidad
estadística, otra escena/host o deadline RT. El ahorro corresponde al
conjunto de ensamblado, ceros, escalas y pivotes, sin atribución aislada.
La cadena detallada sigue offline.

## Conservación y continuación

Compiler/rlib congelados; sin Cargo, biblioteca, WAV o inputs privados
nuevos. Recibos de ~6,40 MB antes de QA con observaciones/etapas
seleccionadas, fuentes fallidas y replays comprimidos; sin otras muestras.
Un `tmp/lab-current`, vacío después de retirar ejecutables y semilla.
Las 4031 fuentes y 8769 inputs privados anteriores quedan protegidos.
[QA](../evidence/hybrid_direct_tests01.json).

Continuar sobre la unión funcional: perfilar la evaluación eléctrica y
los factores restantes antes de elegir otra reducción. Conservar puertos,
cargas e historia; arranque, controles generales, antialias de producción,
fidelidad física y tiempo real siguen pendientes.
