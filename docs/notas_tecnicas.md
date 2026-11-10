# Notas técnicas

## La ROM

- 32 KB en 4000h–BFFFh, sin mapeador. Arranque en 4010h.
- Es una conversión a ROM de una versión en cinta. Al arrancar copia 9200h–987Fh a C000h (mapa y variables de partida) y 6A00h–6BFFh a CB00h (rutina de líneas).

## Estructura del juego

- **Llamadas de sistema:** `CALL 4300h` seguido de un byte con el número de función. La tabla de funciones está en 54F5h. Las más usadas:
  - 13h: imprime la cadena que va detrás de la llamada.
  - 11h: imprime la cadena apuntada por DE.
  - 15h: imprime el mensaje número A.
  - 0Eh, 0Fh y 10h: separan las dos palabras de la orden, las buscan en el diccionario y buscan la frase.
- **Texto:** 57A3h escribe un carácter con la fuente de la BIOS (puntero en F920h). Filas 0–3 de 25 columnas: barra de estado. Filas 4–10 de 12 columnas: ventana de mensajes; al llenarse espera una tecla y se borra. Búfer de texto en ED00h.
- **Datos:**
  - Mapa: 3 plantas de 16×16 casillas. Bits de pared E=1, S=2, O=4, N=8; las puertas usan los mismos bits desplazados 4 a la izquierda. Al avanzar solo se mira la pared de entrada de la casilla de destino.
  - Tablas de salas, trampas, interruptores, llaves, personajes y temporizadores, a continuación del mapa.
  - 990Bh: diccionario (id, palabra, 0). 9C29h: frases (resultado, id1, id2). 9D46h: mensajes (id, texto, 0).
  - A7FDh en adelante: gráficos vectoriales, referenciados por dirección fija.

## El parche

- **Textos:** compresión DTE con los códigos B0h–FEh (79 pares). Una rutina nueva sustituye a las de impresión (11h y 13h) y hace el corte de línea por palabras en la ventana de mensajes. Las cadenas incrustadas en el código se sustituyen por llamadas a cadenas nuevas.
- **Caracteres:** juego internacional del MSX (á A0h, é 82h, í A1h, ó A2h, ú A3h, ñ A4h, ¿ A8h, ¡ ADh, « AEh, » AFh). Glifos propios para Á Í Ó Ú en 83h–86h.
- **Intérprete:** toma la primera y la última palabra; si la frase no existe, la reintenta con las palabras intercambiadas. La entrada pasa a mayúsculas y quita las tildes. Se añaden frases nuevas (por ejemplo, `USAR LLAVE`, `DISPARAR` solo o `HABLAR` solo).
- **Auto-modificaciones:** la escalera (4E61h, `dec a` / `inc a`) y el desbloqueo de cajones (505Bh, `ld c,c` / `ld c,e`) se resuelven con variables en F2F0h–F2F3h.
- **Espacio usado:** 4117h–42FFh, 6550h–69FFh, 6C00h–6C7Fh, 9880h–98FFh, BF77h–BFFFh y la zona antigua de diccionario, frases y mensajes.

## La cinta original

Se comparó con un TSX verificado de la versión en cinta (1984): un BASIC de presentación y el juego en código máquina en 8400h–DBFFh, con arranque en A000h.

- Las dos auto-modificaciones están igual en la cinta (92A8h y 9623h), donde funcionan porque el juego corre en RAM.
- La ROM es una revisión posterior: el mapa cambia en 19 casillas de la planta baja y 13 del sótano 2, los temporizadores son más cortos (130 y 350 turnos frente a 150 y 400), la interfaz se rehízo para 12 columnas y se añadieron un mensaje y las órdenes de depuración TRACE y ESCAPE.
- La clave secreta del final («HAKENKREUZ») no la usa ningún código, ni en la ROM ni en la cinta.

## Mecánica relevante para la solución

- Las trampas se comprueban después de cada orden, en la casilla donde estás. `CORRER` mueve hasta la pared y solo comprueba la casilla final.
- Las trampas de disparo suman daño; se muere al pasar de 3000h (sexto impacto). Las demás matan si su interruptor está encendido.
- Al entrar en la sala 3 empieza una cuenta de 130 turnos, que se detiene al entrar en la sala 5. Al entrar en la sala de Bormann se reactivan todos los interruptores, se abren nuevas compuertas y empieza una cuenta de 350 turnos.
- Las trampas del Último Batallón dejan de actuar solo si se le gasea en la sala 8.
- Final bueno: Bormann y Wessel muertos, testamento leído y Golgo vivo al salir.
