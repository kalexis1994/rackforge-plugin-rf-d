# Próximo bloque: prolongar la trayectoria certificada sin reiniciar memoria

Partir del [primer intervalo certificado](BIESTABLE_TUBO_BLOQUES_RESULTADOS.md),
con endpoint a 195,3125 ns, norma cuadrática conocida y presupuesto nodal
≤0,586 µV. No volver a usar la caja DC como error inicial de otro paso.

## Experimento que se debe congelar

1. Fijar un prefijo de endpoints reales de la trayectoria publicada,
   orden de radios/normas y límite de intentos antes de medir. Conservar
   cada rechazo; el prefijo certificado termina en el primer hueco.
2. Generalizar la reconstrucción de dos estados a tiempos positivos:
   historia real, potenciales/21 cargas afines y cuatro Q(v). Verificar
   continuidad exacta de potencial y memoria reconstruida en interfaces.
3. Llevar anclaje y forcing finales al siguiente intervalo. Si cambia P,
   pagar un puente exterior de norma. Una ruta conservadora explícita
   convierte cada coordenada de junturas con 2a*sqrt((P^-1)_ii) desde
   la norma cuadrática anterior y vuelve a encerrar la nueva caja.
   No comparar cotas de métricas distintas sin conversiones.
4. En cada intervalo encerrar el descriptor medio sobre el tubo completo,
   usar una métrica constante en sus ocho celdas y el anclaje entrante
   realmente probado. Cubrir residual, picos, resto y error nodal inicial.
5. Admitir un intervalo únicamente con inclusión nodal estricta. Archivar
   el extremo final certificado, las memorias y cada puente; distinguir
   duración intentada, inversas cubiertas y error real certificado.

Validar una sucesión no lineal conocida, cambios de métrica con conversión
exacta y rechazos que cortan el prefijo. Reconstruir fuentes y datos sin
alterar el corte anterior. Un prefijo continuo mayor sigue sin cerrar por
sí solo 3 ms/global 1 mV, parámetros físicos, audio o tiempo real.
