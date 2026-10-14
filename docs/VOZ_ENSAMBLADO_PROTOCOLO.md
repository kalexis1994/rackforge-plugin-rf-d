# Ensamblado directo de la voz cargada

Base `8e3dbb40c52591f05a82864d718eab256ea24b0b`, QA `voice_zero_tests01.json`, modelo documental vintage CA3046. El perfil actual localiza initialize≈55 % y parts≈42 % incluido; se prueba eliminar el contenedor intermedio de 200 nodos y su copia a 229. No cambian dispositivos, parámetros, constantes audibles, puertos, cargas, pivotes, Schur, Newton ni controlador.

## Transformación fijada

Conservar el constructor `joint_voice::Parameters::new`, incluida validación y reconstrucción del mezclador, antes de las leyes físicas. Proyectar directamente HIGH/LOW a los mismos 134 índices de VCO y 68 de cadena. Usar los mismos `joint_vco_fine`, stamp DC y `chain_charge`, en el mismo orden. Ensamblar sus incidencias en un solo Parts229, manteniendo cada `+=`, resta, suma compensada, coordenada compartida BUS12 y orden de contribuciones. Comprobar finitud del bloque200 antes de agregar contorno, igual que la versión anterior. Las ramas del contorno y cargas de juntura quedan idénticas.

Banco congelado de168 pares. Comparar dos Parts completos por par (DC, carga/h, Jacobianos, masa/h y candidatos), stamp completo y los1834 f64/counters de cada solve. Casos inválidos deben conservar errores y rechazo sin publicar estado. Ceros con signo siguen operando; no se introduce poda de coeficientes. Medir workspace fijo y costo agregado.

Puerta de utilidad previa: cinco rondas alternadas, ratio de medianas ≤0,95 y peor ronda ≤1,05. Laboratorio y biblioteca pública se miden separadamente antes de promover. Un rechazo conserva fuentes, binario y replay si es un fallo numérico/de compilación; no se relaja gate. El origen documental y el banco anterior no equivalen a una auditoría original nueva del circuito.

Si pasa, familia pública `assembly_decay_voice/engine` conserva las anteriores. Recorrido pareado público de4 ms por resolución en68,442→72,442 ms, desde el checkpoint propio de esa rejilla en `extended-release01`. Comparar cada Accepted, observables, reloj, propuesta, estado e integrales orientadas; verificar todo STEP/OBS/GRID con el segmento admitido y ΔQ Decimal100 entre extremos. Heredar solo las ecuaciones seleccionadas presentes en ese segmento. No sumar duración ni atribuirse el WAV68 ms entero.

## Recursos y alcance

Reserva1 GiB y productos privados nuevos≤96 MiB. Compilación≤120 s, banco≤300 s, perfil pareado≤850 s/proceso≤900 s/campaña≤1900 s. Stack de laboratorio32 MiB. Sin Cargo/cache o SPICE nuevos. Sin identificación física, heap/deadline nuevos medidos ni RT. Prioridad siguiente: usar la mejora admitida para una duración de escucha útil.
