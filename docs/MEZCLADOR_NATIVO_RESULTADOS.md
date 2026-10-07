# Mezclador ON nativo: corrientes y tangentes de carga

2026-10-07. Resultado del [protocolo](MEZCLADOR_NATIVO_PROTOCOLO.md).
La red nominal procede de SVC-9 Fig. 9-17 p.19; su destino es pin 4/C27
de Fig. 9-11 p.13. Se conserva la [referencia anterior](MEZCLADOR_PANEL.md).

## Nuevo bloque eléctrico portable

`mixer_on::OnMixer` entrega el stamp de seis terminales OSC1/2/3, NOISE,
EXT y BUS. Calcula corrientes entrando a la red, potencia disipada y,
como control condicionado, bus ante corriente de placa impuesta. Entrega
sus tangentes y las de las cinco corrientes de fuentes después de eliminar
el bus. Así conserva la carga que el mezclador ejerce sobre cada generador.

El cursor se elimina algebraicamente con D=S+Pα(1−α)≥S. Los extremos son
contactos ideales; no hay resistencias epsilon ni divisiones por α o 1−α.
Con cursor en masa, OSC1 sigue viendo su pista de 25 kΩ y BUS sigue cargado
por R45=33 kΩ. Con los cinco arriba, el control reproduce los pesos 1/7
para OSC1/2/3/EXT y 3/7 para NOISE. Es una cuenta eléctrica condicionada,
no una relación de volumen audible.

Constructor, stamp y evaluación usan arrays fijos, sin memoria dinámica.
Rechazan NaN, infinito, fracciones fuera de dominio y overflow; no recortan
valores ni sustituyen errores por silencio. Omitir una ruta excluye su
subgrafo; no reconstruye su contacto OFF. El subgrafo vacío tiene stamp
cero y devuelve `FloatingBus` si se intenta resolver con corriente impuesta.

## Oráculo nodal y ejecución Rust

Los [279 casos](../evidence/voice_mixer_on_vectors01.json) cubren los 31
subconjuntos no vacíos y nueve perfiles eléctricos, extremos y vecindades
10⁻⁹ incluidos. El oráculo monta resistores y nodos de cursor, usa unión
exacta en los extremos y eliminación nodal a 80 dígitos con `Decimal`.
No usa la fórmula reducida de Rust como valor esperado.

La [ejecución](../evidence/voice_mixer_on_native_attempt01.json) con Rust
1.97.0, target Windows GNU, perfil test sin optimización, pasa siete tests
de conformance y un test aislado de asignación. El build y test completo
duraron 6,25 s; no es una medición de deadline de procesamiento.

| Observable | Máximo medido | Gate previo |
| --- | ---: | ---: |
| Vbus frente al oráculo | 2,2204460493×10⁻¹⁶ V | 10⁻¹⁰ V |
| Corriente de puerto con placa cargada | 2,7105054312×10⁻²⁰ A | 10⁻¹⁴ A |
| Matriz de admitancia | 2,7105054312×10⁻²⁰ S | 10⁻¹⁵ S |
| Asignaciones en 10000 evaluaciones | 0 | 0 |

Pasan matriz completa, tangentes reducidas, KCL, potencia, reciprocidad,
contraste FD, contactos, vecindades representables y rechazos. La
[auditoría](../evidence/voice_mixer_on_native_validation01.json) regenera el
oráculo y verifica stdout, gates, fuentes, toolchain y binarios conservados.
En el resto del núcleo sólo se añadió el export del módulo; sus otras
trece fuentes conservan identidad de Git/checkout explícita.

## Diagnóstico de la referencia anterior y adaptación de identidad

Vbus, pesos, corriente del bus y resistencia de carga del Python anterior
pasan sus gates en estos 279 controles. La comparación diagnóstica de su
matriz completa conserva hasta **3,2450275377×10⁻¹² S** de diferencia.
La antigua expresión resta fuente−cursor y divide por el tramo superior
muy pequeño cerca de α=1; el resultado es compatible con pérdida de
precisión por cancelación. El nuevo stamp se contrasta con los nodos
independientes, sin retocar la referencia vieja ni promover equivalencia
bit a bit con su aritmética. Este diagnóstico no explica el rechazo largo
del solver de la voz ni identifica una tolerancia física del potenciómetro.

La primera auditoría de procedencia falló al comparar literalmente cuatro
checkouts Rust CRLF con blobs Git LF. Se preservan el
[snapshot y fallo observado](../evidence/voice_mixer_on_audit_rejection01.json)
y su [replay completo sin cambios](../evidence/voice_mixer_on_audit_rejection02.json).
La corrección declara cuatro pares concretos de SHA Git/checkout y verifica
su reconstrucción exacta. No admite normalización genérica ni cambia código
eléctrico, vectores, tests o gates. Los nuevos archivos Rust tienen LF fijado.

## Publicación y siguiente integración

La [QA](../evidence/voice_mixer_on_native_tests02.json) cubre **173**:
ocho tests nativos ejecutados y 165 heredados por identidad, sin contarlos
como nuevas ejecuciones. Sólo se actualizan las tres portadas y se añaden
reglas de LF para cuatro archivos Rust en `.gitattributes` entre los inputs
anteriores. Los binarios de test se conservan por hash; se retiró únicamente
el cache de compilación nuevo de este intento, con ruta absoluta comprobada
y [recibo de archivo](../evidence/voice_mixer_on_build_archive01.json).

Admisión local: **puerto pasivo ON nominal**. No está conectado todavía a
la voz portable. Faltan fuentes con impedancias reales, C27/ladder cargado,
contactos OFF y taper. Próximo bloque: acoplar el stamp al puerto dinámico
de entrada del filtro con memoria conservada y contrastar ambos lados.
La nota monolítica larga sigue pendiente por recursos. No hubo solves
SPICE ni audio nuevos, y no se admite fidelidad física o tiempo real.
