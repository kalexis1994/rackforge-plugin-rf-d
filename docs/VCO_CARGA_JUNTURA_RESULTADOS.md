# Carga de juntura nativa: resultado condicionado

2026-10-07. Se cumplió el [contrato previo](VCO_CARGA_JUNTURA_PROTOCOLO.md)
para la primitiva de depleción BE/BC y GS/GD de las tarjetas nominales.
No incluye transporte, carga de difusión, correcciones térmicas o el VCO completo.

## Contraste y estado

La [referencia Decimal de 100 cifras](../evidence/voice_junction_charge_vectors01.json)
usa los floats de entrada exactos y resta Q a esa precisión, sin usar la
integral estable del Rust. Cuatro tarjetas, 1280 casos a 125/500 ns,
polaridades, cero, historias iguales, vecinos de un ULP y cruces del splice.

| Valor | Diferencia absoluta máxima |
|---|---:|
| Q | 1,6543612251×10⁻²⁴ C |
| C | 5,1698788285×10⁻²⁶ F |
| ΔQ | 1,6543612251×10⁻²⁴ C |
| I | 2,7755575616×10⁻¹⁷ A |
| G | 4,3368086899×10⁻¹⁹ S |

Cada vector pasó sus gates absolutos más relativos. Los vecinos no nulos
se comprueban además con error relativo ≤2×10⁻¹², sin piso absoluto.
Las derivadas centrales de Q/I coinciden con C/G; continuidad de Q/C y
reversibilidad de ΔQ comprobadas. La historia entrante queda fija durante
las evaluaciones; el helper entrega un candidato sin confirmar memoria.

La [producción](../evidence/voice_junction_charge_native01.json) compila la
raíz de la biblioteca y ejecuta tres tests eléctricos y uno de heap aislado.
10.000 companions, cero asignaciones; no acredita deadline. Se comprobaron
capacitancia cero, historia igual, dominio, inputs no finitos y overflow.
Fuentes, compiler, comandos y tres binarios conservados; ningún intento
falló. No se ejecutó SPICE ni generó audio.

## Herencia y próximo cierre

La [QA de publicación](../evidence/voice_junction_charge_tests01.json)
reconstruye los 1280 vectores, comprueba los parámetros contra las tarjetas
existentes y conserva algoritmos, datos y gates anteriores. Sólo se añaden
el export, la política de bytes de los nuevos archivos y este bloque;
las tres portadas previas están en su [snapshot exacto](../evidence/voice_junction_charge_documentation01.json).
197 controles: cuatro ejecutados y 193 heredados por identidad.

Siguiente: integrar las corrientes y cargas de transporte/difusión BJT/JFET,
los estados internos de IC1/IC3 y la carga conjunta del mezclador. No hay
oscilación nativa completa admitida, voz instalable o equivalencia física.
El rechazo de la campaña larga permanece vigente.
