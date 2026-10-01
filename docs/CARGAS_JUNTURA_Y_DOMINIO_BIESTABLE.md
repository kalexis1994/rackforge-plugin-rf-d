# Carga de juntura y dominio del biestable

## Alcance y evidencia

Continúa la [búsqueda de tres raíces](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) del cierre cargado de 94 incógnitas. El inventario registra las junturas de Q25/Q15 en esas soluciones del paso implícito de 1 ms: **dos R61 × tres raíces × dos transistores = 12 puntos**. Son puntos condicionados del modelo, no mediciones ni una trayectoria física.

- [Inventario de polarización](../evidence/loudness_junction_domain_audit.json), generador `tools/loudness_junction_domain_audit.py`.
- [Primitivas de carga](../tools/junction_charge_reference.py), sin parámetros predeterminados de componentes.
- [300 sondas independientes](../evidence/junction_charge_probes.json), generador `tools/junction_charge_probes.py`.
- Regresión `tests/test_junction_charge.py`; laboratorio Python 3.12.10/NumPy 2.5.2, binary64. Metadatos y hashes de fuentes en cada informe.

No se incorporan estas cargas al paso de 94 nodos ni al motor Rust. Preparan la matemática de una futura hipótesis explícita. La selección causal de rama permanece abierta.

## Polarización que debe cubrir una ley física

Valores para R61=200 Ω; el informe también incluye 200 kΩ. Tensiones en V, corrientes salientes en el colector en mA. `g·1 ns` está expresado en pF: es una **normalización de sensibilidad por unidad de tiempo**, nunca un tiempo de tránsito asignado.

| Raíz | Transistor | VBE | VCB | IC hipotético | gF·1 ns | gR·1 ns |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Inferior | Q25 | 0,693633 | −0,671752 | 2,589332 | 206,545 | 88,137 |
| Inferior | Q15 | 0,047876 | 4,948940 | ≈0 | ≈0 | ≈0 |
| Intermedia | Q25 | 0,671962 | 0,325604 | 2,283052 | 88,860 | ≈0 |
| Intermedia | Q15 | 0,650062 | −0,508105 | 0,968805 | 37,889 | 0,151 |
| Superior | Q25 | 0,658331 | 3,177705 | 1,343056 | 52,274 | ≈0 |
| Superior | Q15 | 0,660786 | −0,627664 | 0,989209 | 57,516 | 15,845 |

Se conserva la hipótesis Ebers–Moll del laboratorio `Is=10⁻¹⁴ A`, `βF=100`, `βR=5`, `T=298,15 K`, no identificada para las piezas vintage. Las derivadas son `gF=Is·exp(VBE/VT)/VT`, `gR=Is·exp(VBC/VT)/VT`; su unidad es S, por lo que `τ·g` tiene unidad F. El inventario publica además IB/IC/IE y las corrientes de las dos junturas.

Q25 tiene ambas junturas directamente polarizadas en la raíz inferior; Q15 en las raíces intermedia y superior. Se usa el signo de las junturas, sin inventar un umbral de encendido de 0,6 V. El rango total VCB es `−0,671752..3,177705 V` para Q25 y `−0,627664..4,948940 V` para Q15. **Cero de doce** puntos coinciden con VCB=10 V de DS-3392-C/F. La temperatura coincide por hipótesis; no hay excitación AC a 1 MHz. Cob a ese sesgo tampoco identifica Cj0 a cero voltios.

Las sensibilidades no permiten trasladar los capacitores constantes de diagnóstico a una ley de difusión física. Falta determinar tiempos de tránsito y su dependencia con sesgo, carga almacenada en saturación, resistencia de base, alta inyección, temperatura, partición entre terminales y dispersión del lote.

## Ley de depleción condicionada

Fuente matemática **NG-46**, manual ngspice 46, página PDF/impresa 138, ecuación 7.4. Se usa sólo el término de depleción inferior; el borde lateral no se modela. El manual es una fuente de formulación, no de parámetros 2N3392. Se descarga/verifica el PDF y se revisan visualmente pp. 138 y 145; sus valores por defecto y ejemplos no se adoptan como piezas Moog.

Para `Vk=FC·Vj` y `v<Vk`:

```text
C(v) = Cj0·(1−v/Vj)^(−m)
Q(v) = Cj0·Vj·[1−(1−v/Vj)^(1−m)]/(1−m)    si m≠1
Q(v) = −Cj0·Vj·ln(1−v/Vj)                  si m=1
```

Se deriva Q integrando C y fijando Q(0)=0. La implementación usa `log1p`/`expm1` para conservar precisión cerca de cero y del límite m=1. Dominio declarado del helper: `Cj0≥0 F`, `Vj>0 V`, `m∈[0,1]`, `FC∈[0,1)`, parámetros finitos.

Para `v≥Vk`, con `u=v−Vk`, `Ck=C(Vk)` y `sk=Ck·m/[Vj·(1−FC)]`:

```text
C(v) = Ck + sk·u
Q(v) = Qk + Ck·u + ½·sk·u²
```

Esta continuación coincide con la extrapolación lineal de C del manual; conserva Q, C y dC/dv en la unión. La extrapolación evita una singularidad matemática; su existencia no valida la carga real bajo conducción directa.

## Difusión limitada y contrato temporal

NG-46 p. 138 distingue difusión/depleción y expresa `Cdiff=TT·∂Ieff/∂v`. El helper implementa su **límite de baja inyección** con Is y escala `s=n·kT/q` explícitas:

```text
Qdiff(v) = τ·Is·expm1(v/s)     [C, referencia Qdiff(0)=0]
Cdiff(v) = τ·Is·exp(v/s)/s     [F]
```

No implementa la corrección de alta inyección de la ecuación 7.3, recuperación con estado de la p. 139, ni el modelo Gummel–Poon completo. `τ≥0 s`, `Is>0 A`, `s>0 V`; `v/s≤45` es una guardia **numérica** heredada del laboratorio, no un umbral físico. No hay extrapolación silenciosa ni clipping para hacer converger.

Una juntura de dos terminales usa `v=Vpositivo−Vnegativo`. Su compañero de Euler hacia atrás recibe historial inmutable **en coulombs**:

```text
Ipositivo = [Q(vnuevo)−Qanterior]/dt
Inegativo = −Ipositivo
J = [ +C(vnuevo)/dt  −C(vnuevo)/dt ]
    [ −C(vnuevo)/dt  +C(vnuevo)/dt ]
```

El candidato de historial se publica sólo si el circuito completo acepta el paso. Evaluación inválida o rechazo conservan el historial anterior. Q negativa bajo sesgo inverso es válida: la referencia Q(0)=0 es un origen, no una restricción de signo. Cambiar parámetros durante un historial requiere una política de conservación/repreparación aún no implementada.

Este contrato es para una rama genérica. **Dos ramas BE/BC independientes no constituyen automáticamente un BJT dinámico conservativo**: falta derivar partición de carga, terminales internos, acoplamiento de transporte, saturación e inicialización coherente. No se admite un biestable por haber completado estas funciones.

## Verificación

Valores sintéticos, sin ajuste vintage: Cj0=7 pF, Vj=0,75 V, m=0/0,33/0,5/0,999999999/1, FC=0/0,4/0,8, τ=0/3 ns, Is=10⁻¹⁴ A, escala=0,026 V. Se cubren 30 modelos y diez voltajes por modelo, incluidos ±1 pV, la unión de extrapolación y sesgos −10..0,82 V.

La comparación independiente integra C con Gauss–Legendre de 64 puntos, separando la unión. Puertas fijadas en el generador: carga `1e−20 C + 2e−8·|Q|`; derivada `1e−19 F + 1e−6·|C|`. Los 300 casos pasan: error máximo de carga **2,18×10⁻²³ C**, error máximo absoluto dQ/dv **1,58×10⁻¹⁷ F**. La puerta de derivada es relativa además de absoluta.

Las siete pruebas verifican cuadratura regenerada, derivadas regeneradas, continuidad de Q/C/pendiente con extrapolación de Richardson, límite logarítmico y señal pequeña, Jacobiano de ambos terminales con FD, KCL, inmutabilidad ante fallo, carga integrada en un recorrido cerrado y rechazo de parámetros/tiempos no válidos. El inventario de polarización se regenera durante la prueba.

En un incremento sintético 0,2→0,68 V, usar `C(vnuevo)·Δv/dt` da una diferencia relativa **10,1751** frente a `ΔQ/dt`. Es un contraejemplo matemático reproducible, sin adjudicarle esa magnitud a la conmutación vintage.

## Próximo cierre

Identificar o acotar explícitamente parámetros y transporte para la revisión objetivo; implementar una hipótesis BJT de carga conservativa; contrastarla con una formulación independiente; estudiar la transición con memoria fija y resolución de sus modos rápidos. Refinamiento y rechazo deben preceder a cualquier reducción para audio. Las tres raíces y el modo creciente del diagnóstico anterior siguen siendo resultados locales condicionados.
