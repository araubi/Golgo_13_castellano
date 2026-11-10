# Golgo 13: La Guarida del Lobo (MSX) en castellano

Traducción no oficial al castellano de **Golgo 13 – Okami no Su** (ゴルゴ13 狼の巣, Pony Canyon), la aventura conversacional de MSX. Pensada para MSX europeos: usa tildes, ñ y los signos de apertura ¿ ¡ de su juego de caracteres.

Además de la traducción, el parche **corrige dos fallos que hacen imposible terminar el juego** en la ROM original, y el repositorio incluye una solución completa comprobada de principio a fin.

Aquí **no hay ninguna ROM**: ni la original ni la traducida. Solo un parche IPS que aplicas a tu propia copia.

## La ROM necesaria

El parche se aplica a esta ROM japonesa de 32 KB (sin mapeador):

| | |
|---|---|
| tamaño | 32.768 bytes |
| SHA-1 | `031a611ba1f75b7d5fe3ed088a61c24598b4b314` |
| SHA-256 | `87ecf3e0fb911b740f1271c09d745ae9365d32036f953684cd82d784a3517c7d` |
| CRC32 | `40d3889f` |

## Cómo aplicarlo

Con cualquier herramienta de IPS (Lunar IPS, Floating IPS, etc.), o con el script incluido, que comprueba las sumas antes y después:

    python3 tools/apply_patch.py golgo13_jp.rom patch/golgo13_es.ips golgo13_es.rom

El resultado debe tener SHA-1 `71bf403b9d2afeb303281da045ec375d0791b3f2` (SHA-256 `49d8f89463e82a0beca80c169695d0d06f3e8f7f6c647a5ee4581c3d8c3c60fd`, CRC32 `4b3d3916`). En openMSX, con una máquina europea: `openmsx -cart golgo13_es.rom`.

## Qué cambia

### Traducción
- Todos los mensajes, la barra de estado, los avisos y los finales, en castellano.
- Los textos van comprimidos (pares de letras frecuentes en un solo byte) para que quepan en los 32 KB.
- La ventana de mensajes solo tiene 12 columnas: se ha añadido **corte de línea por palabras**.
- Se han dibujado **Á, Í, Ó y Ú**, que no existen en la fuente del MSX.
- Barra de estado: Estado (VERDE / AMBAR / ROJO), Hora, Planta (P.B, S-1, S-2) y Rumbo.

### Órdenes
- Se escribe **verbo + nombre**, en el orden del castellano: `ABRIR PUERTA`, `COGER LA LLAVE`. El juego toma la primera y la última palabra, así que los artículos sobran.
- Da igual escribir en minúsculas o con tildes.
- Las flechas del cursor siguen sirviendo para moverse, y `C` es abreviatura de `CORRER`.
- Las preguntas de sí o no se contestan con **S** o **N**.
- El vocabulario está solo en castellano: en un teclado europeo no se puede escribir en katakana.

### Fallos corregidos
El juego salió en cinta y se ejecutaba en RAM. La ROM que circula es una conversión que conserva **código que se modifica a sí mismo**: en un cartucho esas escrituras se pierden. Por eso, en la ROM sin parchear:

- **no se puede bajar por las escaleras** (la orden de bajar reescribía una instrucción en 4E61h), y
- **no se pueden abrir los cajones con llave** de las salas del sótano 2 (reescritura en 505Bh).

Es decir, el juego no se puede terminar. El parche guarda esos datos en RAM y reproduce el comportamiento de la cinta original, que se ha comprobado sobre una copia verificada de la cinta.

## Solución

La solución completa, con un plano por tramo y la ruta tecla a tecla, está en [docs/solucion.pdf](docs/solucion.pdf). Lo esencial:

- Para el final bueno hay que **matar a Bormann y a Wessel, leer el testamento de Hitler y salir vivo por la puerta del museo**.
- `CORRER` avanza hasta la pared, y **las trampas solo actúan en la casilla donde te paras**: así se cruzan.
- Si entras en una sala con un enemigo vivo, tu siguiente orden tiene que ser `DISPARAR`.
- La única granada de gas es para el Último Batallón, en la sala 8.

## Pruebas

La ROM traducida se ha jugado entera, de principio a fin, en un emulador Z80 propio con la BIOS simulada (`src/emu/`), siguiendo la ruta de la solución: final bueno, con 4 impactos recibidos de los 5 que se pueden aguantar.

**Sin comprobar todavía:** openMSX con una máquina europea completa y máquinas reales. Tampoco se ha probado grabar y cargar partida en cinta.

## Contenido

- `patch/golgo13_es.ips`: el parche, de la ROM japonesa a la traducida.
- `tools/apply_patch.py`: aplica el parche comprobando las sumas.
- `src/build.py`: genera la ROM traducida a partir de la original (`python3 src/build.py golgo13_jp.rom golgo13_es.rom`). Solo necesita Python 3.
- `src/es_text.py`: todos los textos en castellano y el vocabulario.
- `src/asm.py`, `src/z80.py`: ensamblador y desensamblador Z80 mínimos usados para el parche.
- `src/mkips.py`: genera el IPS.
- `src/emu/`, `src/full_walk.py` y el resto de `src/`: el emulador, el mapa y el buscador de rutas con los que se calculó y se comprobó la solución. Necesitan Python 3 y Pillow, y la ROM original en la variable de entorno `G13_ORIG`.
- `docs/solucion.pdf`: la solución completa.
- `docs/notas_tecnicas.md`: estructura interna del juego y detalles del parche.

## Créditos

- **Juego original:** Pony Canyon. Basado en el manga *Golgo 13* de Takao Saito.
- **Traducción, correcciones y solución:** araubi, con la ayuda de Claude (Anthropic).

## Licencia y avisos

- **Código y herramientas** (`patch/`, `src/`, `tools/`): [MIT](LICENSE).
- **Documentación** (este README y `docs/`): [CC BY-NC-SA 4.0](LICENSE-DOCS).
- **Juego original:** *Golgo 13 – Okami no Su* es obra de Pony Canyon, y *Golgo 13* de Takao Saito / Saito Production; sus derechos pertenecen a sus titulares. Este proyecto no distribuye el juego, ni original ni modificado, y no reclama ningún derecho sobre él. Es un homenaje sin ánimo de lucro, sin relación con los titulares, y se retirará si ellos lo piden.
