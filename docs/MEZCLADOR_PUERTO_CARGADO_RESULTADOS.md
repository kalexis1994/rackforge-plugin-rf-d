# Puerto nativo de generadores con la cadena cargada

El [puerto](../crates/rf-d-circuit/src/mixer_chain_port.rs) devuelve cinco
corrientes hacia la red y su matriz 5×5, con filtro/VCAs/salida ya cerrados.
También devuelve los gradientes de los 66 nodos y BUS y el estado candidato.
El estado anterior es inmutable: confirmar la memoria pertenece al solver
que cierre los generadores. Las filas/columnas siguen OSC1/OSC2/OSC3/NOISE/EXT.
El [protocolo previo](MEZCLADOR_PUERTO_CARGADO_PROTOCOLO.md) deriva los cinco
RHS en BASE_Q29 y la composición de la carga; la matriz activa posterior
no se presupone simétrica ni pasiva.

## Resultado

El [oráculo](../evidence/voice_mixer_chain_port_vectors01.json) vuelve a
resolver los sistemas completos con BUS y cursores: cuatro estados, ambos
R61 y una/cinco rutas ON, fuente ±1 mV por cada columna. Sus semillas y
histories proceden de la trayectoria Python independiente, sin raíces ni
Jacobiano Rust. El [ensayo nativo](../evidence/voice_mixer_chain_port_native01.json)
compila la raíz de producción y pasa dos regresiones más una de heap.

| Comparación de tangente | Máximo medido | Gate |
|---|---:|---:|
| Corrientes 5×5 | 2,097672577072084×10⁻¹³ S | 10⁻⁸ S + 10⁻³·\|Y_fd\| |
| 66 nodos | 2,861514866924972×10⁻⁷ V/V | 10⁻⁶ + 10⁻³·\|dx_fd\| |
| Heap | 0 en 16 solves/tangentes completos | 0 |

También pasan BUS, candidato y corrientes centrales con los gates de la
cadena, repetición exacta de calls, fuentes omitidas y rechazo sin confirmar
estado. La [QA](../evidence/voice_mixer_chain_port_tests01.json) cubre
**185**: tres tests nuevos ejecutados y 182 heredados; no se suman las
cinco columnas de cada caso como tests adicionales.

## Uso siguiente y límites

Este puerto aporta la carga necesaria para cerrar un generador con
impedancia real. La tensión de cada fuente sigue impuesta en este banco;
no hay todavía VCO nativo, contorno completo, OFF o taper integrado.
Los nominales y parámetros activos conservan las hipótesis previas.
No hay audio nuevo, fidelidad física o plazo de RT admitidos. La campaña
SPICE monolítica mantiene sus fuentes y continúa independiente.
