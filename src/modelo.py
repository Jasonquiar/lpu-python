"""MI BRIEF · Let's Play Ultimate (LPU) · Encuentro 2

Actor: el planillero (scorekeeper) del partido.

Operación: registrar cada gol en el momento en que ocurre (modificar el marcador)
y consultar el marcador y si el partido ya terminó.

Recursos: un Partido con equipo_a y equipo_b (texto, ej. "Equipo Rojo"), el marcador
de cada equipo y goles_maximos (15 por defecto). En LPU, goles_maximos lo define el
líder de torneo al crear el torneo; como Torneo todavía no existe en este modelo,
el valor llega al crear el Partido.

Regla: el marcador solo avanza por la vía válida (registrar_gol). No se registra un gol:
  - si el partido ya terminó (un equipo llegó a goles_maximos), ni
  - a un equipo que no juega este partido.
  Ambos casos → GolRechazado (regla de negocio).
  Datos inválidos → ValueError: nombre vacío, equipo_a igual a equipo_b, goles_maximos <= 0.
  Los nombres se comparan sin espacios al borde y sin distinguir mayúsculas.
  El marcador es de solo lectura y solo cambia por registrar_gol.
  goles_maximos no se puede cambiar después de crear el partido.

Exclusiones: torneo, categoría, jugadores, asistencias, bloqueos, Callahan, tiempos,
espíritu y W.O.

Primer flujo verificable: con el partido 14-10, registrar_gol("Equipo Rojo") → queda 15-10
y terminado es True. Un gol más → GolRechazado. Un gol de "Equipo Verde" → GolRechazado.

¿Clase o función? Clase. Hay un estado que cambia (el marcador) y una regla que lo
protege. Con una función y un diccionario, cualquiera podría modificar el marcador por
fuera; con la clase, el marcador es de solo lectura y solo avanza por registrar_gol.
No uso herencia: hay una sola entidad y nada que especializar.

Límite conocido: el guion bajo es una convención, no una cerradura. Quien escriba
partido._goles a propósito se salta la protección; la clase protege contra errores,
no contra quien la rompe a propósito.

Pendiente:
  - Tildes en los nombres ("Bogotá" vs "Bogota").
  - Confirmar si hay regla de diferencia de 2 goles o tope (cap). Hoy el partido
    termina cuando un equipo llega a goles_maximos, sin importar la diferencia.
  - Retomar un partido ya empezado (marcador inicial): hoy todo partido empieza 0-0.
  - Torneo: el líder de torneo define goles_maximos para todos los partidos (otra entidad).
  - El planillero no puede jugar en el torneo donde planilla (otra entidad).
  - Ayudas de tiempo: inicio, pull de 75 s, tiempos fuera, medio tiempo (8 goles o 45 min)
    y límite de tiempo (85 min).
  - Goles por W.O.: 1 gol cada 3 min si el rival no llega (mínimo 5 jugadores en línea).
  - Estadísticas por jugador (G, A, B, Callahan), caídos y espíritu.
  - Modo sin conexión: guardar en el dispositivo y sincronizar después.
"""


class GolRechazado(Exception):
    """Rechazo de negocio: el gol no se puede registrar en este partido."""


def normalizar(nombre):
    # 📝 Clave para COMPARAR nombres: sin espacios al borde y en minúsculas.
    #    " Equipo Rojo " → "equipo rojo". Solo se usa para comparar, no para mostrar.
    return nombre.strip().lower()


def validar_nombre(nombre):
    # 📝 DATO inválido → ValueError: algo que no es texto, o texto vacío ("", "   ").
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError(f"Nombre de equipo inválido: {nombre!r}")
    return nombre.strip()


class Partido:
    def __init__(self, equipo_a, equipo_b, goles_maximos=15):
        # 📝 Primero se validan los DATOS. Si algo falla, el partido ni siquiera se crea.
        self._equipo_a = validar_nombre(equipo_a)
        self._equipo_b = validar_nombre(equipo_b)
        if normalizar(self._equipo_a) == normalizar(self._equipo_b):
            # 📝 ❌ "Equipo Rojo" vs " equipo rojo " → es el mismo equipo.
            raise ValueError(f"Un equipo no puede jugar contra sí mismo: {self._equipo_a}")
        if not isinstance(goles_maximos, int) or goles_maximos <= 0:
            raise ValueError(f"goles_maximos inválido: {goles_maximos!r}. Debe ser un entero positivo")
        self._goles_maximos = goles_maximos
        # 📝 El marcador: un diccionario con la clave NORMALIZADA de cada equipo.
        #    Siempre empieza 0-0; solo registrar_gol lo cambia.
        self._goles = {normalizar(self._equipo_a): 0, normalizar(self._equipo_b): 0}

    # 📝 Todas las properties son SOLO LECTURA (no tienen setter).
    #    partido.marcador = (0, 0) → AttributeError. Así no hay hueco como en
    #    inventario_hueco.py: no existe otra forma "normal" de cambiar el marcador.
    @property
    def equipo_a(self):
        return self._equipo_a

    @property
    def equipo_b(self):
        return self._equipo_b

    @property
    def goles_maximos(self):
        return self._goles_maximos

    @property
    def marcador(self):
        # 📝 Devuelve una TUPLA (goles_a, goles_b). Una tupla no se puede modificar,
        #    así que quien la recibe no puede cambiar el marcador por esa vía.
        return (self._goles[normalizar(self._equipo_a)], self._goles[normalizar(self._equipo_b)])

    @property
    def terminado(self):
        # 📝 Se CALCULA cada vez a partir del marcador, no se guarda.
        #    Así nunca puede quedar "15-10 pero terminado = False".
        return max(self.marcador) >= self._goles_maximos

    def registrar_gol(self, equipo):
        # 📝 👮 Aquí vive la regla. Es la ÚNICA forma de cambiar el marcador.
        #    Orden: 1) el DATO, 2) ¿el equipo juega?, 3) ¿el partido sigue abierto?
        nombre = validar_nombre(equipo)  # ❌ "" → ValueError (dato inválido)
        clave = normalizar(nombre)
        if clave not in self._goles:
            # ❌ "Equipo Verde" en Rojo vs Azul → regla de negocio
            raise GolRechazado(f"{nombre} no juega este partido ({self._equipo_a} vs {self._equipo_b})")
        if self.terminado:
            # ❌ 15-10 con goles_maximos 15 → regla de negocio
            raise GolRechazado(f"El partido ya terminó: {self}")
        self._goles[clave] += 1  # ✅ pasó todos los controles: suma 1
        return self.marcador

    def __repr__(self):
        a, b = self.marcador
        return (
            f"Partido({self._equipo_a!r} {a}-{b} {self._equipo_b!r}, "
            f"goles_maximos={self._goles_maximos}, terminado={self.terminado})"
        )

    def __str__(self):
        a, b = self.marcador
        estado = "terminado" if self.terminado else "en juego"
        return f"{self._equipo_a} {a} - {b} {self._equipo_b} ({estado})"


if __name__ == "__main__":
    partido = Partido("Equipo Rojo", "Equipo Azul")  # goles_maximos = 15 por defecto

    # 📝 Para llegar a 14-10 se usa la vía válida: 24 goles con registrar_gol.
    for _ in range(14):
        partido.registrar_gol("Equipo Rojo")
    for _ in range(10):
        partido.registrar_gol("Equipo Azul")
    print("Antes:", partido)
    # Espero: Antes: Equipo Rojo 14 - 10 Equipo Azul (en juego)

    # Casos de registrar_gol. Escribí ANTES qué espero de cada uno.
    # Espero:
    #   ACEPTADO  Equipo Rojo -> Equipo Rojo 15 - 10 Equipo Azul (terminado)
    #   RECHAZADO Equipo Azul -> El partido ya terminó: Equipo Rojo 15 - 10 Equipo Azul (terminado)
    #   RECHAZADO Equipo Verde -> Equipo Verde no juega este partido (Equipo Rojo vs Equipo Azul)
    for equipo in ["Equipo Rojo", "Equipo Azul", "Equipo Verde"]:
        try:
            partido.registrar_gol(equipo)
            print("ACEPTADO ", equipo, "->", partido)
        except GolRechazado as error:
            print("RECHAZADO", equipo, "->", error)

    # Caso de dato inválido: el mismo equipo con otras mayúsculas y espacios.
    # Espero: DATO INVÁLIDO -> Un equipo no puede jugar contra sí mismo: Equipo Rojo
    try:
        Partido("Equipo Rojo", " equipo rojo ")
    except ValueError as error:
        print("DATO INVÁLIDO ->", error)

    # Simulacro de la revisión: "intenta saltarte la regla asignando el atributo".
    # Espero: un AttributeError, porque marcador no tiene setter.
    try:
        partido.marcador = (0, 0)
    except AttributeError as error:
        print("NO SE PUEDE ->", error)

    print(repr(partido))
    # Espero: Partido('Equipo Rojo' 15-10 'Equipo Azul', goles_maximos=15, terminado=True)
