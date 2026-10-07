# BJT nominal nativo del VCO: transporte y cargas

2026-10-07. Pasó el [protocolo previo](VCO_BJT_NOMINAL_PROTOCOLO.md).
NPN/PNP condicionados, TEMP=TNOM=25 °C, cuatro terminales [C,B,E,S],
GMIN operativo y escala térmica ngspice46. Las constantes y el subset
siguen las [tarjetas de laboratorio](../evidence/vco1_laboratory_devices.json).
No son semiconductores físicos identificados.

## Núcleo y memoria

Corrientes de transporte, depleción y difusión, con Jacobianos completos.
Se reutiliza la primitiva de depleción sin cambios. La difusión TF/TR usa
incrementos estables de corriente, incluidos cruces del empalme −3VT.
No hay clamps o limiting inventados. Historia fija durante Newton;
el stamp entrega un candidato sin publicar el estado del circuito.

El sustrato omitido del BJT de tres pines vuelve a masa en ngspice46.
La rama GMIN se conecta a C en NPN vertical y B en PNP lateral por los
defaults del modelo. Se hizo explícita como cuarto terminal; su corriente
se conserva, sin atribuir carga a CJS=0 ni tratarla como transporte.
El futuro grafo debe conectar S a masa como en el oráculo actual.

## Contrastes ejecutados

[Decimal100](../evidence/voice_vco_bjt_vectors01.json): 1536 vectores con
polaridades, dos bases, ocho biases por juntura, tres historias y dt125/500 ns;
20 vecinos adicionales con gate relativo sin piso absoluto. Inputs binary64
exactos, reference por ramas e incidencias, ajena al código Rust.

| Valor | Diferencia máxima contra Decimal100 |
|---|---:|
| Corriente DC/Euler | 7,9936057773×10⁻¹⁵ A |
| Carga terminal | 2,3161057151×10⁻²³ C |
| Jacobiano DC/Euler | 2,8421709430×10⁻¹³ S |
| Derivada de carga | 8,4703294725×10⁻²² F |
| ΔQ de juntura | 1,7370792864×10⁻²³ C |

Gates absolutos más relativos aplicados a cada valor. También pasaron
FD de las 16 entradas, gauge y conservación de cuatro terminales, historia
igual/fija, retornos de sustrato y rechazos. La [producción nativa](../evidence/voice_vco_bjt_native01.json)
compila la raíz y ejecuta tres tests eléctricos y uno aislado de heap:
10.000 stamps completos, cero asignaciones. No acredita deadline.

[Ngspice46 independiente](../evidence/voice_vco_bjt_spice02.json): doce
escenas, DC, Q/capacidad y excitación AC separada de los cuatro terminales.
Todos los gates previos pasaron. La diferencia máxima nativo/AC es
1,0000004297×10⁻¹² S. **AC no coincide exactamente con la derivada DC**:
bjtacld.c omite gdsub real, mientras bjtload.c lo incluye en DC/transitorio.
La [auditoría](../evidence/voice_vco_bjt_ac_audit01.json) conserva esa diferencia;
al agregar sólo esa rama como diagnóstico a AC, el máximo frente al oráculo
Decimal baja a 6,9388939047×10⁻¹⁷ S. No se alteró el kernel, dato o gate.

El [primer intento SPICE](../evidence/voice_vco_bjt_spice01.json) fue rechazado
por export incompleto: wrdata interpretó las corrientes DC como una sola
expresión. Se preservaron fuentes y exports originales y se reprodujo
el mismo comando sin cambios. Un exportador nuevo usa expresiones real()
separadas; no se corrigió física o tolerancias. 14 procesos SPICE en total:
uno fallido, su replay y doce escenas admitidas. No hay audio nuevo.

## Admisión y siguiente bloque

La [QA de publicación](../evidence/voice_vco_bjt_tests02.json) conserva
algoritmos, gates y datos anteriores, verifica las identidades de producción,
reconstruye Decimal y coteja los exports privados. 201 controles: cuatro
nuevos ejecutados y 197 heredados por identidad, sin doble conteo de SPICE.
El [snapshot](../evidence/voice_vco_bjt_documentation01.json) guarda las tres
portadas previas por bytes exactos; se conservan fallos y binarios.

BJT nominal con transporte/cargas admitido para su dominio; JFET, estados
741, VCO autónomo y unión cargada permanecen pendientes. No extiende
fidelidad física, producto, tiempo real o la campaña larga rechazada.
