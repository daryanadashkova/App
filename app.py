import random
import time
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

# ====================== CONFIGURACIÓN DE COLORES ======================

class Colors:
    """Colores para la interfaz de consola"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'

# ====================== CLASES PRINCIPALES ======================

class Activo(ABC):
    """Clase base abstracta para todos los activos financieros"""
    
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float):
        self.simbolo = simbolo
        self.nombre = nombre
        self._precio_actual = precio_inicial
        self.precio_anterior = precio_inicial
        self.historial_precios = [precio_inicial]
        self._observers = []
        
    @abstractmethod
    def actualizar_precio(self):
        """Método abstracto para actualizar el precio del activo"""
        pass
    
    @property
    def precio_actual(self):
        return self._precio_actual
    
    @precio_actual.setter
    def precio_actual(self, nuevo_precio):
        """Setter con notificación automática a observadores"""
        if nuevo_precio != self._precio_actual:
            self.precio_anterior = self._precio_actual
            self._precio_actual = nuevo_precio
            self.historial_precios.append(nuevo_precio)
            self._notificar_observadores()
    
    def agregar_observador(self, observer):
        """Agrega un observador (como un portafolio) para cambios de precio"""
        self._observers.append(observer)
    
    def _notificar_observadores(self):
        """Notifica a todos los observadores del cambio de precio"""
        for observer in self._observers:
            observer.actualizar(self)
    
    def get_cambio_porcentual(self) -> float:
        """Retorna el cambio porcentual respecto al precio anterior"""
        if self.precio_anterior == 0:
            return 0
        return ((self.precio_actual - self.precio_anterior) / self.precio_anterior) * 100
    
    def __str__(self):
        cambio = self.get_cambio_porcentual()
        if cambio >= 0:
            cambio_str = f"{Colors.GREEN}▲{cambio:.2f}%{Colors.ENDC}"
        else:
            cambio_str = f"{Colors.RED}▼{abs(cambio):.2f}%{Colors.ENDC}"
        return f"{Colors.BOLD}{self.simbolo}{Colors.ENDC} - {self.nombre}: ${self.precio_actual:.2f} {cambio_str}"


class Accion(Activo):
    """Clase para acciones de empresas"""
    
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float, sector: str):
        super().__init__(simbolo, nombre, precio_inicial)
        self.sector = sector
        self.volatilidad = 0.02  # 2% de volatilidad base
        
    def actualizar_precio(self):
        """Actualiza el precio de la acción con movimiento aleatorio y tendencia"""
        # Cambio porcentual aleatorio
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        
        # Eventos de mercado (noticias)
        evento = random.random()
        if evento < 0.05:  # 5% de probabilidad de noticia importante
            if random.random() < 0.5:
                cambio_pct += 0.03  # Noticia positiva +3%
                self._mostrar_noticia(f"📈 NOTICIA POSITIVA: {self.nombre} sube por buenos resultados")
            else:
                cambio_pct -= 0.03  # Noticia negativa -3%
                self._mostrar_noticia(f"📉 NOTICIA NEGATIVA: {self.nombre} cae por malas expectativas")
        
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        # Limitar cambios extremos
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.85)  # Máximo -15%
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.15)  # Máximo +15%
        
        self.precio_actual = nuevo_precio
    
    def _mostrar_noticia(self, mensaje: str):
        """Muestra noticias en la interfaz"""
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.ENDC}")
        print(f"{Colors.CYAN}{mensaje}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.ENDC}\n")


class Criptomoneda(Activo):
    """Clase para criptomonedas (más volátiles)"""
    
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float):
        super().__init__(simbolo, nombre, precio_inicial)
        self.volatilidad = 0.05  # 5% de volatilidad (las criptos son más volátiles)
        
    def actualizar_precio(self):
        """Actualiza el precio de la criptomoneda con alta volatilidad"""
        # Las criptomonedas tienen mayor volatilidad
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        
        # Eventos extremos de criptomonedas
        evento = random.random()
        if evento < 0.03:  # 3% de probabilidad de evento extremo
            if random.random() < 0.5:
                cambio_pct += 0.15  # "Luna" +15%
                self._mostrar_evento(f"🚀 ¡{self.nombre} se va a la LUNA! +15% 🚀")
            else:
                cambio_pct -= 0.15  # "Crash" -15%
                self._mostrar_evento(f"💥 ¡CRASH de {self.nombre}! -15% 💥")
        
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        # Las criptos pueden tener movimientos más extremos
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.6)  # Máximo -40%
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.4)  # Máximo +40%
        
        self.precio_actual = nuevo_precio
    
    def _mostrar_evento(self, mensaje: str):
        """Muestra eventos de criptomonedas"""
        print(f"\n{Colors.MAGENTA}{'='*60}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{mensaje}{Colors.ENDC}")
        print(f"{Colors.MAGENTA}{'='*60}{Colors.ENDC}\n")


class Portafolio:
    """Clase que gestiona las inversiones y actualiza su valor automáticamente"""
    
    def __init__(self, inversor_nombre: str, capital_inicial: float = 10000):
        self.inversor_nombre = inversor_nombre
        self.activos: Dict[Activo, float] = {}  # activo -> cantidad
        self.valor_total = capital_inicial
        self.efectivo = capital_inicial
        self.historial_valor = [capital_inicial]
        self.historial_tiempos = [datetime.now()]
        
    def agregar_activo(self, activo: Activo, cantidad: float) -> tuple:
        """Agrega un activo al portafolio y se suscribe a sus cambios"""
        costo = cantidad * activo.precio_actual
        
        if costo > self.efectivo:
            return False, f"❌ Saldo insuficiente. Necesitas ${costo:.2f}"
        
        if activo in self.activos:
            self.activos[activo] += cantidad
        else:
            self.activos[activo] = cantidad
            activo.agregar_observador(self)
        
        self.efectivo -= costo
        self.actualizar_valor_total()
        return True, f"✅ Comprados {cantidad:.4f} {activo.simbolo} por ${costo:.2f}"
    
    def vender_activo(self, activo: Activo, cantidad: Optional[float] = None) -> tuple:
        """Vende parcial o totalmente un activo"""
        if activo not in self.activos:
            return False, f"❌ No tienes {activo.simbolo} en tu portafolio"
        
        cantidad_actual = self.activos[activo]
        if cantidad is None or cantidad >= cantidad_actual:
            cantidad = cantidad_actual
            del self.activos[activo]
        else:
            self.activos[activo] -= cantidad
        
        ingreso = cantidad * activo.precio_actual
        self.efectivo += ingreso
        self.actualizar_valor_total()
        return True, f"✅ Vendidos {cantidad:.4f} {activo.simbolo} por ${ingreso:.2f}"
    
    def actualizar(self, activo: Activo):
        """Método observer - se llama cuando un activo cambia de precio"""
        self.actualizar_valor_total()
    
    def actualizar_valor_total(self):
        """Actualiza el valor total del portafolio"""
        valor_inversiones = sum(cantidad * activo.precio_actual for activo, cantidad in self.activos.items())
        nuevo_valor_total = valor_inversiones + self.efectivo
        self.valor_total = nuevo_valor_total
        self.historial_valor.append(nuevo_valor_total)
        self.historial_tiempos.append(datetime.now())
    
    def get_rendimiento(self) -> float:
        """Calcula el rendimiento porcentual desde el inicio"""
        capital_inicial = self.historial_valor[0]
        return ((self.valor_total - capital_inicial) / capital_inicial) * 100
    
    def mostrar_resumen(self):
        """Muestra un resumen detallado del portafolio"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📊 PORTAFOLIO DE {self.inversor_nombre}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}💰 EFECTIVO DISPONIBLE:{Colors.ENDC} ${self.efectivo:.2f}")
        
        rendimiento = self.get_rendimiento()
        if rendimiento >= 0:
            rendimiento_color = Colors.GREEN
        else:
            rendimiento_color = Colors.RED
        print(f"{Colors.BOLD}📈 RENDIMIENTO TOTAL:{Colors.ENDC} {rendimiento_color}{rendimiento:+.2f}%{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}📦 ACTIVOS EN PORTAFOLIO:{Colors.ENDC}")
        
        if not self.activos:
            print(f"  {Colors.YELLOW}No tienes activos. ¡Comienza a invertir!{Colors.ENDC}")
        else:
            for activo, cantidad in self.activos.items():
                valor = cantidad * activo.precio_actual
                cambio = activo.get_cambio_porcentual()
                if cambio >= 0:
                    cambio_str = f"{Colors.GREEN}+{cambio:.2f}%{Colors.ENDC}"
                else:
                    cambio_str = f"{Colors.RED}{cambio:.2f}%{Colors.ENDC}"
                print(f"  {activo.simbolo} ({activo.nombre})")
                print(f"    Cantidad: {cantidad:.4f} | Valor: ${valor:.2f} | Cambio: {cambio_str}")
        
        print(f"\n{Colors.BOLD}💎 VALOR TOTAL DEL PORTAFOLIO: ${self.valor_total:.2f}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}\n")


class Mercado:
    """Clase que maneja el mercado y la simulación"""
    
    def __init__(self):
        self.activos: List[Activo] = []
        self.simulando = False
        self.velocidad_simulacion = 1  # Segundos entre actualizaciones
        
    def agregar_activo(self, activo: Activo):
        """Agrega un activo al mercado"""
        self.activos.append(activo)
        print(f"✓ {activo.simbolo} agregado al mercado")
    
    def actualizar_mercado(self):
        """Actualiza todos los activos del mercado"""
        for activo in self.activos:
            activo.actualizar_precio()
    
    def mostrar_mercado(self):
        """Muestra el estado actual del mercado"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📈 MERCADO DE VALORES - TIEMPO REAL{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        
        # Separar acciones y criptomonedas
        acciones = [a for a in self.activos if isinstance(a, Accion)]
        criptos = [a for a in self.activos if isinstance(a, Criptomoneda)]
        
        if acciones:
            print(f"\n{Colors.BOLD}{Colors.GREEN}🏢 ACCIONES:{Colors.ENDC}")
            for accion in acciones:
                print(f"  {accion}")
        
        if criptos:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}🪙 CRIPTOMONEDAS:{Colors.ENDC}")
            for cripto in criptos:
                print(f"  {cripto}")
        
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
    
    def iniciar_simulacion(self, portafolio: Portafolio, pasos: int = 0):
        """Inicia la simulación del mercado"""
        self.simulando = True
        contador = 0
        
        print(f"\n{Colors.GREEN}🎬 INICIANDO SIMULACIÓN DE MERCADO...{Colors.ENDC}")
        print(f"Presiona Ctrl+C para detener la simulación\n")
        
        try:
            while self.simulando and (pasos == 0 or contador < pasos):
                # Limpiar pantalla en Windows o Linux/Mac
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Actualizar mercado
                self.actualizar_mercado()
                
                # Mostrar estado actual
                self.mostrar_mercado()
                portafolio.mostrar_resumen()
                
                # Mostrar rendimiento del día
                print(f"{Colors.BOLD}⏰ Actualización {contador + 1}{Colors.ENDC}")
                
                contador += 1
                if pasos > 0 and contador >= pasos:
                    break
                
                # Esperar para la próxima actualización
                time.sleep(self.velocidad_simulacion)
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⏸️ Simulación detenida por el usuario{Colors.ENDC}")
        
        print(f"\n{Colors.GREEN}🏁 SIMULACIÓN FINALIZADA{Colors.ENDC}")


# ====================== INTERFAZ DE USUARIO ======================

class SimuladorMercado:
    """Clase principal del simulador con interfaz de usuario"""
    
    def __init__(self):
        self.mercado = Mercado()
        self.portafolio = None
        self.usuario_actual = None
        
    def inicializar_mercado(self):
        """Inicializa el mercado con activos predefinidos"""
        print(f"{Colors.CYAN}Inicializando mercado...{Colors.ENDC}")
        
        # Agregar acciones
        acciones = [
            Accion("AAPL", "Apple Inc.", 150.00, "Tecnología"),
            Accion("GOOGL", "Alphabet Inc.", 2800.00, "Tecnología"),
            Accion("AMZN", "Amazon.com Inc.", 3300.00, "Comercio Electrónico"),
            Accion("TSLA", "Tesla Inc.", 250.00, "Automotriz"),
            Accion("MSFT", "Microsoft Corp.", 330.00, "Tecnología"),
            Accion("NFLX", "Netflix Inc.", 450.00, "Entretenimiento"),
        ]
        
        # Agregar criptomonedas
        criptos = [
            Criptomoneda("BTC", "Bitcoin", 45000.00),
            Criptomoneda("ETH", "Ethereum", 3000.00),
            Criptomoneda("ADA", "Cardano", 0.50),
            Criptomoneda("SOL", "Solana", 100.00),
            Criptomoneda("DOGE", "Dogecoin", 0.08),
        ]
        
        for accion in acciones:
            self.mercado.agregar_activo(accion)
        
        for cripto in criptos:
            self.mercado.agregar_activo(cripto)
        
        print(f"{Colors.GREEN}✓ Mercado inicializado con {len(self.mercado.activos)} activos{Colors.ENDC}\n")
    
    def crear_usuario(self):
        """Crea un nuevo usuario/inversor"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}🎯 BIENVENIDO AL SIMULADOR DE MERCADO DE VALORES{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        nombre = input(f"\n{Colors.BOLD}Ingresa tu nombre: {Colors.ENDC}").strip()
        if not nombre:
            nombre = "Inversor"
        
        capital_input = input(f"{Colors.BOLD}Capital inicial (default: $10,000, 0 para default): {Colors.ENDC}").strip()
        try:
            capital = float(capital_input) if capital_input and float(capital_input) > 0 else 10000
        except:
            capital = 10000
        
        self.usuario_actual = nombre
        self.portafolio = Portafolio(nombre, capital)
        
        print(f"\n{Colors.GREEN}✅ ¡Bienvenido {nombre}!{Colors.ENDC}")
        print(f"💰 Capital inicial: ${capital:.2f}")
        print(f"📈 ¡Comienza a invertir y haz crecer tu fortuna!\n")
    
    def mostrar_menu(self):
        """Muestra el menú principal"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📋 MENÚ PRINCIPAL{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"1. {Colors.GREEN}📊 Ver Mercado{Colors.ENDC}")
        print(f"2. {Colors.BLUE}💰 Ver Mi Portafolio{Colors.ENDC}")
        print(f"3. {Colors.GREEN}🛒 Comprar Activo{Colors.ENDC}")
        print(f"4. {Colors.RED}💸 Vender Activo{Colors.ENDC}")
        print(f"5. {Colors.YELLOW}🚀 Iniciar Simulación Automática{Colors.ENDC}")
        print(f"6. {Colors.MAGENTA}📈 Ver Historial de Rendimiento{Colors.ENDC}")
        print(f"0. {Colors.RED}❌ Salir{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    
    def ver_mercado(self):
        """Muestra el estado actual del mercado"""
        self.mercado.mostrar_mercado()
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ver_portafolio(self):
        """Muestra el estado actual del portafolio"""
        self.portafolio.mostrar_resumen()
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def comprar_activo(self):
        """Compra un activo del mercado"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}🛒 COMPRAR ACTIVO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        # Mostrar activos disponibles
        for i, activo in enumerate(self.mercado.activos, 1):
            print(f"{i}. {activo}")
        
        try:
            opcion = int(input(f"\n{Colors.BOLD}Selecciona el activo (1-{len(self.mercado.activos)}): {Colors.ENDC}"))
            if opcion < 1 or opcion > len(self.mercado.activos):
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                return
            
            activo = self.mercado.activos[opcion - 1]
            cantidad = float(input(f"{Colors.BOLD}Cantidad a comprar: {Colors.ENDC}"))
            
            if cantidad <= 0:
                print(f"{Colors.RED}❌ Cantidad inválida{Colors.ENDC}")
                return
            
            success, mensaje = self.portafolio.agregar_activo(activo, cantidad)
            print(f"\n{mensaje}")
            
        except ValueError:
            print(f"{Colors.RED}❌ Entrada inválida{Colors.ENDC}")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def vender_activo(self):
        """Vende un activo del portafolio"""
        if not self.portafolio.activos:
            print(f"\n{Colors.RED}❌ No tienes activos para vender{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.RED}💸 VENDER ACTIVO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        # Mostrar activos del portafolio
        activos_lista = list(self.portafolio.activos.keys())
        for i, activo in enumerate(activos_lista, 1):
            cantidad = self.portafolio.activos[activo]
            print(f"{i}. {activo.simbolo} - Cantidad: {cantidad:.4f} - Precio: ${activo.precio_actual:.2f}")
        
        try:
            opcion = int(input(f"\n{Colors.BOLD}Selecciona el activo (1-{len(activos_lista)}): {Colors.ENDC}"))
            if opcion < 1 or opcion > len(activos_lista):
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                return
            
            activo = activos_lista[opcion - 1]
            cantidad_max = self.portafolio.activos[activo]
            
            respuesta = input(f"{Colors.BOLD}Cantidad a vender (Enter para vender todo): {Colors.ENDC}").strip()
            if respuesta == "":
                cantidad = None
            else:
                cantidad = float(respuesta)
                if cantidad <= 0:
                    print(f"{Colors.RED}❌ Cantidad inválida{Colors.ENDC}")
                    return
            
            success, mensaje = self.portafolio.vender_activo(activo, cantidad)
            print(f"\n{mensaje}")
            
        except ValueError:
            print(f"{Colors.RED}❌ Entrada inválida{Colors.ENDC}")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def iniciar_simulacion_automatica(self):
        """Inicia la simulación automática del mercado"""
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}🚀 SIMULACIÓN AUTOMÁTICA{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.ENDC}")
        
        try:
            pasos_input = input(f"{Colors.BOLD}Número de actualizaciones (0 = infinito): {Colors.ENDC}")
            pasos = int(pasos_input) if pasos_input else 0
        except:
            pasos = 0
        
        try:
            velocidad_input = input(f"{Colors.BOLD}Velocidad (segundos entre actualizaciones, default=1): {Colors.ENDC}")
            if velocidad_input and float(velocidad_input) > 0:
                self.mercado.velocidad_simulacion = float(velocidad_input)
        except:
            pass
        
        self.mercado.iniciar_simulacion(self.portafolio, pasos)
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ver_historial(self):
        """Muestra el historial de rendimiento del portafolio"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}📈 HISTORIAL DE RENDIMIENTO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        if len(self.portafolio.historial_valor) <= 1:
            print(f"{Colors.YELLOW}No hay suficiente historial aún. Realiza más transacciones o simulaciones.{Colors.ENDC}")
        else:
            print(f"\n{Colors.BOLD}Evolución del valor del portafolio:{Colors.ENDC}")
            # Mostrar últimos 10 registros
            inicio = max(0, len(self.portafolio.historial_valor) - 20)
            for i in range(inicio, len(self.portafolio.historial_valor)):
                valor = self.portafolio.historial_valor[i]
                tiempo = self.portafolio.historial_tiempos[i]
                cambio = ((valor - self.portafolio.historial_valor[0]) / self.portafolio.historial_valor[0]) * 100
                if cambio >= 0:
                    cambio_color = Colors.GREEN
                else:
                    cambio_color = Colors.RED
                print(f"  {tiempo.strftime('%H:%M:%S')} - Valor: ${valor:.2f} | Rendimiento: {cambio_color}{cambio:+.2f}%{Colors.ENDC}")
            
            # Mostrar estadísticas
            max_valor = max(self.portafolio.historial_valor)
            min_valor = min(self.portafolio.historial_valor)
            print(f"\n{Colors.BOLD}📊 Estadísticas:{Colors.ENDC}")
            print(f"  Valor Máximo: ${max_valor:.2f}")
            print(f"  Valor Mínimo: ${min_valor:.2f}")
            print(f"  Rendimiento Total: {self.portafolio.get_rendimiento():+.2f}%")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ejecutar(self):
        """Ejecuta el simulador"""
        self.inicializar_mercado()
        self.crear_usuario()
        
        while True:
            self.mostrar_menu()
            opcion = input(f"{Colors.BOLD}Selecciona una opción: {Colors.ENDC}").strip()
            
            if opcion == "1":
                self.ver_mercado()
            elif opcion == "2":
                self.ver_portafolio()
            elif opcion == "3":
                self.comprar_activo()
            elif opcion == "4":
                self.vender_activo()
            elif opcion == "5":
                self.iniciar_simulacion_automatica()
            elif opcion == "6":
                self.ver_historial()
            elif opcion == "0":
                print(f"\n{Colors.GREEN}✅ ¡Gracias por usar el simulador!{Colors.ENDC}")
                print(f"💰 Valor final del portafolio: ${self.portafolio.valor_total:.2f}")
                print(f"📈 Rendimiento total: {self.portafolio.get_rendimiento():+.2f}%")
                break
            else:
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                time.sleep(1)


# ====================== EJECUCIÓN PRINCIPAL ======================

if __name__ == "__main__":
    try:
        simulador = SimuladorMercado()
        simulador.ejecutar()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}Error inesperado: {e}{Colors.ENDC}")