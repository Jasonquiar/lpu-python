"""MI BRIEF · Let's Play Ultimate (LPU) · Encuentro 2

Actor: el planillero (scorekeeper). El control de tiempo lleva el reloj y le avisa,
para que el planillero esté pendiente de las jugadas y no del tiempo.

Operación: registrar cada jugada en el momento en que ocurre (el pull, el inicio desde
el brick y cada gol) y consultar el marcador, quién ataca, quién defiende y si el
partido terminó y cómo.

Recursos:
  - Reglamento: lo define el líder de torneo al crear el torneo: goles máximos (15),
    duración del partido (85 min), tiempo de pull (75 s), medio tiempo (45 min o la
    mitad de los goles máximos) y cuántos minutos antes del final se avisa la última
    jugada (5). Como Torneo todavía no existe, el reglamento llega al crear el Partido.
  - Partido: equipo_a y equipo_b, quién ataca primero (se sortea en la cancha), el
    marcador y el estado de la jugada (tiempo de pull o jugada activa).
  - ControlDeTiempo: el tiempo del partido y el tiempo de pull de cada jugada.

Cómo funciona una jugada:
  tiempo de pull (la defensa organiza su estrategia) → pull → jugada activa → gol.
  La jugada está activa hasta que alguien anota: el ataque o la defensa.
  Quien anota sigue atacando; a quien le anotaron pasa a defender.
  Si la defensa se pasa del tiempo de pull, el ataque puede iniciar desde el brick.

Regla: el marcador solo avanza por la vía válida, y el partido termina:
  - por goles: un equipo llega a goles_maximos, aunque quede tiempo, o
  - por tiempo: se cumplió el tiempo, no hay jugada activa y no hay empate.
    Con la jugada activa, se sigue hasta el próximo gol; con empate, se juega una
    jugada más. Un partido nunca termina empatado.
  GolRechazado: gol de un equipo que no juega, gol sin jugada activa (falta el pull)
    o gol con el partido terminado.
  JugadaRechazada: pull con una jugada ya activa, brick sin pull vencido, cualquier
    jugada con el partido terminado o marcar dos veces el tiempo cumplido.
  Datos inválidos → ValueError: nombre vacío, un equipo contra sí mismo (sin espacios
    ni mayúsculas), ataca primero un equipo que no juega, o valores del reglamento que
    no son enteros positivos o que no caben en la duración del partido.
  El marcador, el reglamento y el estado son de solo lectura: solo cambian por las
  operaciones. terminado se calcula; no se guarda.

Exclusiones: torneo, categoría, jugadores, asistencias, bloqueos, Callahan, espíritu,
tiempos fuera, partido no jugado y W.O.

Primer flujo verificable: Rojo y Azul van 14-10 y faltan 5 minutos → aviso. Se lanza el
pull y se cumple el tiempo con la jugada activa → el partido sigue. Gol de Azul → 14-11,
terminado por tiempo. Un gol más → GolRechazado.

¿Clase o función? Clases. Hay estado que cambia (marcador, jugada, tiempo) y reglas que
lo protegen. Con funciones y diccionarios, cualquiera podría cambiar el marcador o
reabrir un partido por fuera.
Composición, sin herencia: el Partido TIENE un Reglamento y el ControlDeTiempo TIENE un
Partido. El Partido no sabe nada del reloj: el control le avisa por medio de sus
operaciones (marcar_pull_vencido, marcar_tiempo_cumplido). Así las reglas viven en un
solo lugar y se pueden probar sin esperar 85 minutos, porque el reloj se puede cambiar
por uno de mentira. GolRechazado y JugadaRechazada son dos excepciones separadas.

Límite conocido: el guion bajo es una convención, no una cerradura. Quien escriba
partido._goles a propósito se salta la protección; las clases protegen contra errores,
no contra quien las rompe a propósito.

Pendiente:
  - Torneo: el líder de torneo crea el reglamento una vez para todos los partidos.
  - Sorteo de quién ataca primero dentro de la app (hoy llega como dato).
  - Confirmar si el aviso de pull (hoy fijo: 15 s antes del límite) lo define el líder.
  - Tiempos fuera y duración del descanso de medio tiempo.
  - Partido no jugado (no se presenta ningún equipo) y W.O. (1 gol cada 3 min si el
    rival no llega, mínimo 5 jugadores en línea).
  - Estadísticas por jugador (G, A, B, Callahan), caídos y espíritu.
  - Tildes en los nombres ("Bogotá" vs "Bogota").
  - Retomar un partido ya empezado (hoy todo partido empieza 0-0).
  - El reloj de verdad corriendo cada segundo llega con la app o la API: hoy el control
    revisa el tiempo cada vez que se llama revisar().
  - Modo sin conexión: guardar en el dispositivo y sincronizar después.
"""

import math
import time

AVISO_PULL_SEGUNDOS_ANTES = 15
# 📝 El aviso de "se acaba el tiempo de pull" sale 15 s antes del límite.
#    Con un pull de 60 s → aviso a los 45 s. Con 75 s → aviso a los 60 s.


class GolRechazado(Exception):
    """Rechazo de negocio: el gol no se puede registrar en este partido."""


class JugadaRechazada(Exception):
    """Rechazo de negocio: la jugada (pull, brick o fin de tiempo) no se puede hacer ahora."""


# ---------------------------------------------------------------------------
# Validación de datos (ValueError = la solicitud está mal escrita)
# ---------------------------------------------------------------------------

def normalizar(nombre):
    # 📝 Clave para COMPARAR nombres: sin espacios al borde y en minúsculas.
    #    " Equipo Rojo " → "equipo rojo". Solo se usa para comparar, no para mostrar.
    return nombre.strip().lower()


def validar_nombre(nombre):
    # 📝 ❌ algo que no es texto, o texto vacío ("", "   ") → ValueError.
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError(f"Nombre de equipo inválido: {nombre!r}")
    return nombre.strip()


def validar_entero_positivo(dato, valor):
    # 📝 True y False también son int en Python; por eso se excluyen aparte.
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise ValueError(f"{dato} inválido: {valor!r}. Debe ser un entero positivo")
    return valor


# ---------------------------------------------------------------------------
# Reglamento: lo que decide el líder de torneo
# ---------------------------------------------------------------------------

class Reglamento:
    """Valores que define el líder de torneo al crear el torneo (por defecto, los de LPU)."""

    def __init__(
        self,
        goles_maximos=15,
        duracion_minutos=85,
        tiempo_pull_segundos=75,
        minuto_medio_tiempo=45,
        minutos_aviso_final=5,
    ):
        self._goles_maximos = validar_entero_positivo("goles_maximos", goles_maximos)
        self._duracion_minutos = validar_entero_positivo("duracion_minutos", duracion_minutos)
        self._tiempo_pull_segundos = validar_entero_positivo("tiempo_pull_segundos", tiempo_pull_segundos)
        self._minuto_medio_tiempo = validar_entero_positivo("minuto_medio_tiempo", minuto_medio_tiempo)
        self._minutos_aviso_final = validar_entero_positivo("minutos_aviso_final", minutos_aviso_final)
        # 📝 Además de ser positivos, los valores tienen que tener sentido JUNTOS:
        if tiempo_pull_segundos <= AVISO_PULL_SEGUNDOS_ANTES:
            raise ValueError(
                f"tiempo_pull_segundos debe ser mayor que {AVISO_PULL_SEGUNDOS_ANTES} "
                f"(el aviso de pull se da {AVISO_PULL_SEGUNDOS_ANTES} s antes)"
            )
        if minuto_medio_tiempo >= duracion_minutos:
            raise ValueError("El medio tiempo debe ser antes del final del partido")
        if minutos_aviso_final >= duracion_minutos:
            raise ValueError("El aviso de última jugada debe caber en la duración del partido")

    # 📝 Solo lectura: una vez creado, el reglamento no cambia en medio del partido.
    @property
    def goles_maximos(self):
        return self._goles_maximos

    @property
    def duracion_minutos(self):
        return self._duracion_minutos

    @property
    def tiempo_pull_segundos(self):
        return self._tiempo_pull_segundos

    @property
    def minuto_medio_tiempo(self):
        return self._minuto_medio_tiempo

    @property
    def minutos_aviso_final(self):
        return self._minutos_aviso_final

    @property
    def goles_medio_tiempo(self):
        # 📝 La mitad de los goles máximos, redondeada hacia arriba: 15 → 8.
        return math.ceil(self._goles_maximos / 2)


# ---------------------------------------------------------------------------
# Partido: las reglas (no sabe nada del reloj)
# ---------------------------------------------------------------------------

class Partido:
    def __init__(self, equipo_a, equipo_b, ataca_primero, reglamento=None):
        # 📝 Primero los DATOS. Si algo falla, el partido ni siquiera se crea.
        self._equipo_a = validar_nombre(equipo_a)
        self._equipo_b = validar_nombre(equipo_b)
        clave_a, clave_b = normalizar(self._equipo_a), normalizar(self._equipo_b)
        if clave_a == clave_b:
            raise ValueError(f"Un equipo no puede jugar contra sí mismo: {self._equipo_a}")
        primero = validar_nombre(ataca_primero)
        if normalizar(primero) not in (clave_a, clave_b):
            raise ValueError(f"El equipo que ataca primero no juega este partido: {primero}")
        if reglamento is None:
            reglamento = Reglamento()
        if not isinstance(reglamento, Reglamento):
            raise ValueError("reglamento debe ser un Reglamento")

        self._reglamento = reglamento  # 📝 COMPOSICIÓN: el partido TIENE un reglamento.
        self._nombres = {clave_a: self._equipo_a, clave_b: self._equipo_b}
        self._goles = {clave_a: 0, clave_b: 0}  # 📝 Siempre empieza 0-0.
        self._atacante = normalizar(primero)
        self._jugada_activa = False  # 📝 Empieza en "tiempo de pull": la defensa planea.
        self._pull_vencido = False
        self._tiempo_cumplido = False

    # 📝 Todas las properties son SOLO LECTURA (no tienen setter).
    #    partido.marcador = (0, 0) → AttributeError. No hay otra forma "normal"
    #    de cambiar el estado que las operaciones de abajo.
    @property
    def equipo_a(self):
        return self._equipo_a

    @property
    def equipo_b(self):
        return self._equipo_b

    @property
    def reglamento(self):
        return self._reglamento

    @property
    def goles_maximos(self):
        return self._reglamento.goles_maximos

    @property
    def marcador(self):
        # 📝 Una TUPLA (goles_a, goles_b): quien la recibe no la puede modificar.
        return (self._goles[normalizar(self._equipo_a)], self._goles[normalizar(self._equipo_b)])

    @property
    def atacante(self):
        return self._nombres[self._atacante]

    @property
    def defensor(self):
        # 📝 El defensor no se guarda: es "el otro equipo". Así nunca se contradicen.
        clave = next(c for c in self._goles if c != self._atacante)
        return self._nombres[clave]

    @property
    def jugada_activa(self):
        return self._jugada_activa

    @property
    def pull_vencido(self):
        return self._pull_vencido

    @property
    def tiempo_cumplido(self):
        return self._tiempo_cumplido

    @property
    def como_termino(self):
        # 📝 Se CALCULA cada vez a partir del estado; nunca se guarda.
        #    Devuelve "por goles", "por tiempo" o None (sigue en juego).
        goles_a, goles_b = self.marcador
        if max(goles_a, goles_b) >= self.goles_maximos:
            return "por goles"  # ✅ 15-10, aunque quede tiempo
        if self._tiempo_cumplido and not self._jugada_activa and goles_a != goles_b:
            return "por tiempo"  # ✅ tiempo cumplido + sin jugada activa + sin empate
        return None  # ⏳ incluye: tiempo cumplido con jugada activa, o con empate

    @property
    def terminado(self):
        return self.como_termino is not None

    # --- Operaciones: la ÚNICA forma de cambiar el estado ------------------

    def registrar_pull(self):
        # 📝 La defensa lanza el disco: empieza la jugada activa.
        if self.terminado:
            raise JugadaRechazada(f"El partido ya terminó: {self}")
        if self._jugada_activa:
            raise JugadaRechazada("Ya hay una jugada activa: el pull ya se lanzó")
        self._jugada_activa = True
        self._pull_vencido = False

    def marcar_pull_vencido(self):
        # 📝 La llama el ControlDeTiempo cuando la defensa se pasa del tiempo de pull.
        if self.terminado:
            raise JugadaRechazada(f"El partido ya terminó: {self}")
        if self._jugada_activa:
            raise JugadaRechazada("No hay tiempo de pull corriendo: la jugada está activa")
        self._pull_vencido = True

    def iniciar_desde_brick(self):
        # 📝 El ataque inicia sin pull, desde el brick. Solo si el pull se venció.
        if self.terminado:
            raise JugadaRechazada(f"El partido ya terminó: {self}")
        if self._jugada_activa:
            raise JugadaRechazada("Ya hay una jugada activa: el pull ya se lanzó")
        if not self._pull_vencido:
            raise JugadaRechazada(
                f"No se puede iniciar desde el brick: {self.defensor} todavía tiene tiempo de pull"
            )
        self._jugada_activa = True
        self._pull_vencido = False

    def registrar_gol(self, equipo):
        # 📝 👮 Aquí vive la regla del marcador. Orden: 1) el DATO, 2) ¿el equipo
        #    juega?, 3) ¿el partido sigue abierto?, 4) ¿hay jugada activa?
        nombre = validar_nombre(equipo)  # ❌ "" → ValueError (dato inválido)
        clave = normalizar(nombre)
        if clave not in self._goles:
            raise GolRechazado(f"{nombre} no juega este partido ({self._equipo_a} vs {self._equipo_b})")
        if self.terminado:
            raise GolRechazado(f"El partido ya terminó: {self}")
        if not self._jugada_activa:
            raise GolRechazado(f"No hay jugada activa: falta el pull de {self.defensor}")
        self._goles[clave] += 1  # ✅ pasó todos los controles: suma 1
        self._jugada_activa = False  # 📝 Termina la jugada: empieza un nuevo tiempo de pull.
        self._atacante = clave  # 📝 Regla de LPU: quien anota sigue atacando.
        return self.marcador

    def marcar_tiempo_cumplido(self):
        # 📝 La llama el ControlDeTiempo. No cierra el partido por sí sola:
        #    como_termino decide si ya terminó o si falta la última jugada.
        if self._tiempo_cumplido:
            raise JugadaRechazada("El tiempo del partido ya se había cumplido")
        if self.terminado:
            raise JugadaRechazada(f"El partido ya terminó: {self}")
        self._tiempo_cumplido = True

    def __repr__(self):
        goles_a, goles_b = self.marcador
        return (
            f"Partido({self._equipo_a!r} {goles_a}-{goles_b} {self._equipo_b!r}, "
            f"ataca={self.atacante!r}, terminado={self.como_termino!r})"
        )

    def __str__(self):
        goles_a, goles_b = self.marcador
        estado = f"terminado {self.como_termino}" if self.terminado else "en juego"
        return f"{self._equipo_a} {goles_a} - {goles_b} {self._equipo_b} ({estado})"


# ---------------------------------------------------------------------------
# ControlDeTiempo: lleva el reloj y avisa al planillero
# ---------------------------------------------------------------------------

class ControlDeTiempo:
    # 📝 COMPOSICIÓN: el control TIENE un partido. Lleva el tiempo y le avisa al
    #    planillero, pero las reglas siguen viviendo en Partido.
    #    reloj = una función que devuelve "los segundos de ahora". Por defecto es el
    #    reloj real (time.monotonic); en la demo y en las pruebas se cambia por uno
    #    de mentira para no esperar 85 minutos.

    def __init__(self, partido, reloj=time.monotonic):
        if not isinstance(partido, Partido):
            raise ValueError("partido debe ser un Partido")
        self._partido = partido
        self._reloj = reloj
        self._inicio = None
        self._avisos_dados = set()  # 📝 Cada aviso del partido sale UNA sola vez.
        self._jugada_del_pull = None  # 📝 Qué jugada tiene su tiempo de pull corriendo.
        self._inicio_pull = None
        self._avisos_pull = set()

    def iniciar(self):
        if self._inicio is not None:
            raise JugadaRechazada("El control de tiempo ya se había iniciado")
        self._inicio = self._reloj()
        return self.revisar()

    def revisar(self):
        # 📝 Se llama seguido (en una app, cada segundo). Devuelve la lista de
        #    avisos NUEVOS para el planillero. Si no hay nada que avisar → [].
        if self._inicio is None:
            raise JugadaRechazada("Primero hay que iniciar el control de tiempo")
        partido = self._partido
        if partido.terminado:
            return []
        reglas = partido.reglamento
        ahora = self._reloj()
        segundos = ahora - self._inicio
        avisos = []

        if "medio tiempo" not in self._avisos_dados and (
            segundos >= reglas.minuto_medio_tiempo * 60
            or max(partido.marcador) >= reglas.goles_medio_tiempo
        ):
            self._avisos_dados.add("medio tiempo")
            avisos.append(f"Medio tiempo: {partido}")

        minuto_aviso_final = reglas.duracion_minutos - reglas.minutos_aviso_final
        if "aviso final" not in self._avisos_dados and segundos >= minuto_aviso_final * 60:
            self._avisos_dados.add("aviso final")
            avisos.append(f"Faltan {reglas.minutos_aviso_final} minutos: se acerca la última jugada")

        if "tiempo cumplido" not in self._avisos_dados and segundos >= reglas.duracion_minutos * 60:
            self._avisos_dados.add("tiempo cumplido")
            partido.marcar_tiempo_cumplido()  # 📝 El control avisa; el Partido decide.
            if partido.terminado:
                avisos.append(f"Tiempo cumplido: el partido terminó. {partido}")
                return avisos
            if partido.jugada_activa:
                avisos.append("Tiempo cumplido con la jugada activa: el partido termina con el próximo gol")
            else:
                avisos.append("Tiempo cumplido con empate: se juega una jugada más")

        # 📝 Tiempo de pull: corre mientras NO hay jugada activa. Cada jugada nueva
        #    (después de cada gol) tiene su propio tiempo de pull desde cero.
        if partido.jugada_activa:
            self._jugada_del_pull = None
        else:
            jugada = sum(partido.marcador)  # 📝 0-0 → jugada 0; tras 1 gol → jugada 1…
            if self._jugada_del_pull != jugada:
                self._jugada_del_pull = jugada
                self._inicio_pull = ahora
                self._avisos_pull = set()
            segundos_pull = ahora - self._inicio_pull
            limite = reglas.tiempo_pull_segundos
            if "aviso" not in self._avisos_pull and segundos_pull >= limite - AVISO_PULL_SEGUNDOS_ANTES:
                self._avisos_pull.add("aviso")
                avisos.append(f"Se acaba el tiempo de pull: avisa a {partido.defensor} (defensa)")
            if "vencido" not in self._avisos_pull and segundos_pull >= limite:
                self._avisos_pull.add("vencido")
                partido.marcar_pull_vencido()
                avisos.append(f"Pull vencido: avisa a {partido.atacante} (ataque) que puede iniciar desde el brick")

        return avisos


# ---------------------------------------------------------------------------
# Demo: casos que se aceptan y que se rechazan. Escribí ANTES qué espero.
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    class RelojDeMentira:
        # 📝 Reemplaza al reloj real: el tiempo solo avanza cuando yo lo digo.
        def __init__(self):
            self.segundos = 0

        def ahora(self):
            return self.segundos

        def avanzar(self, minutos=0, segundos=0):
            self.segundos += minutos * 60 + segundos

    def jugar(partido, equipo, veces=1):
        # 📝 Atajo de la demo: una jugada completa (pull + gol), repetida.
        for _ in range(veces):
            partido.registrar_pull()
            partido.registrar_gol(equipo)

    def intentar(partido, descripcion, accion):
        try:
            accion()
            print(f"  ACEPTADO  {descripcion} -> {partido}")
        except (GolRechazado, JugadaRechazada) as error:
            print(f"  RECHAZADO {descripcion} -> {type(error).__name__}: {error}")

    def mostrar(reloj, avisos):
        minutos, segundos = divmod(reloj.ahora(), 60)
        if not avisos:
            print(f"  [{minutos:02d}:{segundos:02d}] (sin avisos)")
        for aviso in avisos:
            print(f"  [{minutos:02d}:{segundos:02d}] AVISO: {aviso}")

    print("== 1 · Jugadas y fin por goles")
    partido = Partido("Equipo Rojo", "Equipo Azul", ataca_primero="Equipo Rojo")
    print("  Inicio:", partido, "| ataca:", partido.atacante, "| defiende:", partido.defensor)
    # Espero:   Inicio: Equipo Rojo 0 - 0 Equipo Azul (en juego) | ataca: Equipo Rojo | defiende: Equipo Azul
    intentar(partido, "gol sin pull", lambda: partido.registrar_gol("Equipo Rojo"))
    # Espero:   RECHAZADO gol sin pull -> GolRechazado: No hay jugada activa: falta el pull de Equipo Azul
    partido.registrar_pull()
    intentar(partido, "gol de la defensa (Azul)", lambda: partido.registrar_gol("Equipo Azul"))
    # Espero:   ACEPTADO  gol de la defensa (Azul) -> Equipo Rojo 0 - 1 Equipo Azul (en juego)
    print("  Ahora ataca:", partido.atacante, "| defiende:", partido.defensor)
    # Espero:   Ahora ataca: Equipo Azul | defiende: Equipo Rojo
    jugar(partido, "Equipo Rojo", veces=14)
    jugar(partido, "Equipo Azul", veces=9)
    partido.registrar_pull()
    intentar(partido, "gol de Rojo con 14-10", lambda: partido.registrar_gol("Equipo Rojo"))
    # Espero:   ACEPTADO  gol de Rojo con 14-10 -> Equipo Rojo 15 - 10 Equipo Azul (terminado por goles)
    intentar(partido, "otro pull", partido.registrar_pull)
    # Espero:   RECHAZADO otro pull -> JugadaRechazada: El partido ya terminó: Equipo Rojo 15 - 10 Equipo Azul (terminado por goles)
    intentar(partido, "gol de Equipo Verde", lambda: partido.registrar_gol("Equipo Verde"))
    # Espero:   RECHAZADO gol de Equipo Verde -> GolRechazado: Equipo Verde no juega este partido (Equipo Rojo vs Equipo Azul)
    try:
        partido.marcador = (0, 0)  # 📝 Simulacro de la revisión: saltarse la regla.
    except AttributeError as error:
        print("  NO SE PUEDE ->", error)
    # Espero:   NO SE PUEDE -> property 'marcador' of 'Partido' object has no setter

    print("== 2 · Datos inválidos")
    for descripcion, crear in [
        ("mismo equipo", lambda: Partido("Equipo Rojo", " equipo rojo ", "Equipo Rojo")),
        ("ataca un equipo ajeno", lambda: Partido("Equipo Rojo", "Equipo Azul", "Equipo Verde")),
        ("pull de 10 s", lambda: Reglamento(tiempo_pull_segundos=10)),
    ]:
        try:
            crear()
        except ValueError as error:
            print(f"  DATO INVÁLIDO {descripcion} -> {error}")
    # Espero:   DATO INVÁLIDO mismo equipo -> Un equipo no puede jugar contra sí mismo: Equipo Rojo
    #           DATO INVÁLIDO ataca un equipo ajeno -> El equipo que ataca primero no juega este partido: Equipo Verde
    #           DATO INVÁLIDO pull de 10 s -> tiempo_pull_segundos debe ser mayor que 15 (el aviso de pull se da 15 s antes)

    print("== 3 · Tiempo de pull y brick (pull de 75 s)")
    reloj = RelojDeMentira()
    partido = Partido("Equipo Rojo", "Equipo Azul", ataca_primero="Equipo Azul")
    control = ControlDeTiempo(partido, reloj=reloj.ahora)
    mostrar(reloj, control.iniciar())
    # Espero:   [00:00] (sin avisos)
    reloj.avanzar(segundos=60)
    mostrar(reloj, control.revisar())
    # Espero:   [01:00] AVISO: Se acaba el tiempo de pull: avisa a Equipo Rojo (defensa)
    reloj.avanzar(segundos=15)
    mostrar(reloj, control.revisar())
    # Espero:   [01:15] AVISO: Pull vencido: avisa a Equipo Azul (ataque) que puede iniciar desde el brick
    intentar(partido, "iniciar desde el brick", partido.iniciar_desde_brick)
    # Espero:   ACEPTADO  iniciar desde el brick -> Equipo Rojo 0 - 0 Equipo Azul (en juego)
    reloj.avanzar(segundos=30)
    partido.registrar_gol("Equipo Azul")
    mostrar(reloj, control.revisar())  # 📝 Empieza un nuevo tiempo de pull desde cero.
    # Espero:   [01:45] (sin avisos)
    intentar(partido, "brick sin pull vencido", partido.iniciar_desde_brick)
    # Espero:   RECHAZADO brick sin pull vencido -> JugadaRechazada: No se puede iniciar desde el brick: Equipo Rojo todavía tiene tiempo de pull

    print("== 4 · Fin por tiempo con la jugada activa (85 min)")
    reloj = RelojDeMentira()
    partido = Partido("Equipo Rojo", "Equipo Azul", ataca_primero="Equipo Rojo")
    control = ControlDeTiempo(partido, reloj=reloj.ahora)
    control.iniciar()
    jugar(partido, "Equipo Rojo", veces=8)
    jugar(partido, "Equipo Azul", veces=6)
    reloj.avanzar(minutos=40)
    mostrar(reloj, control.revisar())  # 📝 Medio tiempo por goles: Rojo llegó a 8.
    # Espero:   [40:00] AVISO: Medio tiempo: Equipo Rojo 8 - 6 Equipo Azul (en juego)
    jugar(partido, "Equipo Rojo", veces=6)
    jugar(partido, "Equipo Azul", veces=4)
    reloj.avanzar(minutos=40)
    mostrar(reloj, control.revisar())
    # Espero:   [80:00] AVISO: Faltan 5 minutos: se acerca la última jugada
    partido.registrar_pull()
    reloj.avanzar(minutos=5)
    mostrar(reloj, control.revisar())
    # Espero:   [85:00] AVISO: Tiempo cumplido con la jugada activa: el partido termina con el próximo gol
    intentar(partido, "gol de Azul en la última jugada", lambda: partido.registrar_gol("Equipo Azul"))
    # Espero:   ACEPTADO  gol de Azul en la última jugada -> Equipo Rojo 14 - 11 Equipo Azul (terminado por tiempo)
    intentar(partido, "gol de Rojo después del final", lambda: partido.registrar_gol("Equipo Rojo"))
    # Espero:   RECHAZADO gol de Rojo después del final -> GolRechazado: El partido ya terminó: Equipo Rojo 14 - 11 Equipo Azul (terminado por tiempo)

    print("== 5 · Fin por tiempo con empate: se juega una jugada más")
    reloj = RelojDeMentira()
    partido = Partido("Equipo Rojo", "Equipo Azul", ataca_primero="Equipo Rojo")
    control = ControlDeTiempo(partido, reloj=reloj.ahora)
    control.iniciar()
    for _ in range(10):
        jugar(partido, "Equipo Rojo")
        jugar(partido, "Equipo Azul")
    reloj.avanzar(minutos=85)
    mostrar(reloj, control.revisar())  # 📝 Saltamos 85 min de golpe: llegan 3 avisos juntos.
    # Espero:   [85:00] AVISO: Medio tiempo: Equipo Rojo 10 - 10 Equipo Azul (en juego)
    #           [85:00] AVISO: Faltan 5 minutos: se acerca la última jugada
    #           [85:00] AVISO: Tiempo cumplido con empate: se juega una jugada más
    partido.registrar_pull()
    intentar(partido, "gol de Rojo en la jugada extra", lambda: partido.registrar_gol("Equipo Rojo"))
    # Espero:   ACEPTADO  gol de Rojo en la jugada extra -> Equipo Rojo 11 - 10 Equipo Azul (terminado por tiempo)

    print("== 6 · Fin por tiempo sin jugada activa y sin empate")
    reloj = RelojDeMentira()
    partido = Partido("Equipo Rojo", "Equipo Azul", ataca_primero="Equipo Rojo")
    control = ControlDeTiempo(partido, reloj=reloj.ahora)
    control.iniciar()
    jugar(partido, "Equipo Rojo", veces=12)
    jugar(partido, "Equipo Azul", veces=9)
    reloj.avanzar(minutos=85)
    mostrar(reloj, control.revisar())
    # Espero:   [85:00] AVISO: Medio tiempo: Equipo Rojo 12 - 9 Equipo Azul (en juego)
    #           [85:00] AVISO: Faltan 5 minutos: se acerca la última jugada
    #           [85:00] AVISO: Tiempo cumplido: el partido terminó. Equipo Rojo 12 - 9 Equipo Azul (terminado por tiempo)
    print(" ", repr(partido))
    # Espero:   Partido('Equipo Rojo' 12-9 'Equipo Azul', ataca='Equipo Azul', terminado='por tiempo')
