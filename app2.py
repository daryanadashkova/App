import random
import time
import os
import json
import hashlib
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

# ====================== SISTEMA DE USUARIOS ======================

class Usuario:
    """Clase que maneja usuarios y autenticación"""
    
    ARCHIVO_USUARIOS = "usuarios.json"
    
    def __init__(self, nombre: str, contraseña: str, capital_inicial: float = 10000):
        self.nombre = nombre
        self.contraseña_hash = self._hash_contraseña(contraseña)
        self.capital_inicial = capital_inicial
        self.fecha_creacion = datetime.now().isoformat()
        self.historial_inversiones = []
    
    def _hash_contraseña(self, contraseña: str) -> str:
        """Crea un hash de la contraseña para almacenamiento seguro"""
        return hashlib.sha256(contraseña.encode()).hexdigest()
    
    def verificar_contraseña(self, contraseña: str) -> bool:
        """Verifica si la contraseña es correcta"""
        return self.contraseña_hash == self._hash_contraseña(contraseña)
    
    def to_dict(self) -> dict:
        """Convierte el usuario a diccionario para almacenamiento"""
        return {
            "nombre": self.nombre,
            "contraseña_hash": self.contraseña_hash,
            "capital_inicial": self.capital_inicial,
            "fecha_creacion": self.fecha_creacion,
            "historial_inversiones": self.historial_inversiones
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Crea un usuario desde un diccionario"""
        usuario = cls(data["nombre"], "", data["capital_inicial"])
        usuario.contraseña_hash = data["contraseña_hash"]
        usuario.fecha_creacion = data["fecha_creacion"]
        usuario.historial_inversiones = data.get("historial_inversiones", [])
        return usuario


class GestorUsuarios:
    """Gestiona todos los usuarios del sistema"""
    
    def __init__(self):
        self.usuarios: Dict[str, Usuario] = {}
        self.usuario_actual: Optional[Usuario] = None
        self._cargar_usuarios()
    
    def _cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON"""
        if os.path.exists(Usuario.ARCHIVO_USUARIOS):
            try:
                with open(Usuario.ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for nombre, datos in data.items():
                        self.usuarios[nombre] = Usuario.from_dict(datos)
            except Exception as e:
                print(f"Error al cargar usuarios: {e}")
    
    def _guardar_usuarios(self):
        """Guarda los usuarios en el archivo JSON"""
        data = {nombre: usuario.to_dict() for nombre, usuario in self.usuarios.items()}
        with open(Usuario.ARCHIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def registrar_usuario(self, nombre: str, contraseña: str, capital: float = 10000) -> tuple:
        """Registra un nuevo usuario"""
        if nombre in self.usuarios:
            return False, "❌ El nombre de usuario ya existe"
        
        if len(contraseña) < 4:
            return False, "❌ La contraseña debe tener al menos 4 caracteres"
        
        usuario = Usuario(nombre, contraseña, capital)
        self.usuarios[nombre] = usuario
        self._guardar_usuarios()
        return True, f"✅ Usuario '{nombre}' registrado exitosamente"
    
    def iniciar_sesion(self, nombre: str, contraseña: str) -> tuple:
        """Inicia sesión de un usuario"""
        if nombre not in self.usuarios:
            return False, "❌ Usuario no encontrado"
        
        if self.usuarios[nombre].verificar_contraseña(contraseña):
            self.usuario_actual = self.usuarios[nombre]
            return True, f"✅ Bienvenido {nombre}!"
        else:
            return False, "❌ Contraseña incorrecta"
    
    def cambiar_contraseña(self, nombre: str, contraseña_actual: str, contraseña_nueva: str) -> tuple:
        """Cambia la contraseña de un usuario"""
        if nombre not in self.usuarios:
            return False, "❌ Usuario no encontrado"
        
        if not self.usuarios[nombre].verificar_contraseña(contraseña_actual):
            return False, "❌ Contraseña actual incorrecta"
        
        if len(contraseña_nueva) < 4:
            return False, "❌ La nueva contraseña debe tener al menos 4 caracteres"
        
        self.usuarios[nombre].contraseña_hash = self.usuarios[nombre]._hash_contraseña(contraseña_nueva)
        self._guardar_usuarios()
        return True, "✅ Contraseña cambiada exitosamente"
    
    def cerrar_sesion(self):
        """Cierra la sesión actual"""
        self.usuario_actual = None
    
    def esta_autenticado(self) -> bool:
        """Verifica si hay un usuario autenticado"""
        return self.usuario_actual is not None

# ====================== ACTIVOS FINANCIEROS ======================

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
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        
        evento = random.random()
        if evento < 0.05:
            if random.random() < 0.5:
                cambio_pct += 0.03
                self._mostrar_noticia(f"📈 NOTICIA POSITIVA: {self.nombre} sube por buenos resultados")
            else:
                cambio_pct -= 0.03
                self._mostrar_noticia(f"📉 NOTICIA NEGATIVA: {self.nombre} cae por malas expectativas")
        
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.85)
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.15)
        self.precio_actual = nuevo_precio
    
    def _mostrar_noticia(self, mensaje: str):
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.ENDC}")
        print(f"{Colors.CYAN}{mensaje}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.ENDC}\n")


class Criptomoneda(Activo):
    """Clase para criptomonedas (más volátiles)"""
    
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float):
        super().__init__(simbolo, nombre, precio_inicial)
        self.volatilidad = 0.05  # 5% de volatilidad
        
    def actualizar_precio(self):
        """Actualiza el precio de la criptomoneda con alta volatilidad"""
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        
        evento = random.random()
        if evento < 0.03:
            if random.random() < 0.5:
                cambio_pct += 0.15
                self._mostrar_evento(f"🚀 ¡{self.nombre} se va a la LUNA! +15% 🚀")
            else:
                cambio_pct -= 0.15
                self._mostrar_evento(f"💥 ¡CRASH de {self.nombre}! -15% 💥")
        
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.6)
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.4)
        self.precio_actual = nuevo_precio
    
    def _mostrar_evento(self, mensaje: str):
        print(f"\n{Colors.MAGENTA}{'='*60}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{mensaje}{Colors.ENDC}")
        print(f"{Colors.MAGENTA}{'='*60}{Colors.ENDC}\n")

# ====================== PORTAFOLIO ======================

class Portafolio:
    """Clase que gestiona las inversiones y actualiza su valor automáticamente"""
    
    def __init__(self, inversor_nombre: str, capital_inicial: float = 10000):
        self.inversor_nombre = inversor_nombre
        self.activos: Dict[Activo, float] = {}
        self.valor_total = capital_inicial
        self.efectivo = capital_inicial
        self.historial_valor = [capital_inicial]
        self.historial_tiempos = [datetime.now()]
        self.historial_precios_activos: Dict[str, list] = {}
        
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
            if activo.simbolo not in self.historial_precios_activos:
                self.historial_precios_activos[activo.simbolo] = []
        
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
        if activo.simbolo in self.historial_precios_activos:
            self.historial_precios_activos[activo.simbolo].append(activo.precio_actual)
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
        if capital_inicial == 0:
            return 0
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
    
    def generar_diagrama_lineal(self, ancho: int = 50, alto: int = 10):
        """Genera un diagrama lineal ASCII del rendimiento del portafolio"""
        if len(self.historial_valor) < 2:
            return "No hay suficientes datos para generar el diagrama."
        
        valores = self.historial_valor[-ancho:] if len(self.historial_valor) > ancho else self.historial_valor
        max_valor = max(valores)
        min_valor = min(valores)
        rango = max_valor - min_valor if max_valor != min_valor else 1
        
        diagrama = []
        diagrama.append(f"\n{Colors.BOLD}{Colors.CYAN}📈 DIAGRAMA DE RENDIMIENTO DEL PORTAFOLIO{Colors.ENDC}")
        diagrama.append(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        
        for fila in range(alto, -1, -1):
            y_valor = min_valor + (rango * fila / alto)
            linea = f"{Colors.GREEN}{y_valor:8.0f}{Colors.ENDC} │"
            
            for i, valor in enumerate(valores):
                altura_punto = int(((valor - min_valor) / rango) * alto)
                if altura_punto >= fila:
                    linea += "█"
                else:
                    linea += " "
            
            diagrama.append(linea)
        
        diagrama.append(f"{Colors.GREEN}{' ' * 9}{Colors.ENDC}{'─' * len(valores)}")
        
        tiempo_str = "          "
        for i in range(0, len(valores), max(1, len(valores)//5)):
            if i < len(valores):
                tiempo_str += "↓"
            else:
                tiempo_str += " "
        diagrama.append(tiempo_str)
        
        diagrama.append(f"\n{Colors.BOLD}📊 Estadísticas:{Colors.ENDC}")
        diagrama.append(f"  Valor Inicial: ${self.historial_valor[0]:.2f}")
        diagrama.append(f"  Valor Actual: ${self.valor_total:.2f}")
        diagrama.append(f"  Máximo: ${max_valor:.2f}")
        diagrama.append(f"  Mínimo: ${min_valor:.2f}")
        diagrama.append(f"  Rendimiento: {self.get_rendimiento():+.2f}%")
        
        return "\n".join(diagrama)

# ====================== MERCADO ======================

class Mercado:
    """Clase que maneja el mercado y la simulación"""
    
    def __init__(self):
        self.activos: List[Activo] = []
        self.simulando = False
        self.velocidad_simulacion = 1
        self.ultima_actualizacion = None
        
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
    
    def iniciar_simulacion(self, portafolio: Portafolio, pasos: int = 0, mostrar_diagrama: bool = True):
        """Inicia la simulación del mercado con diagrama lineal"""
        self.simulando = True
        contador = 0
        
        print(f"\n{Colors.GREEN}🎬 INICIANDO SIMULACIÓN DE MERCADO...{Colors.ENDC}")
        print(f"Presiona Ctrl+C para detener la simulación\n")
        
        try:
            while self.simulando and (pasos == 0 or contador < pasos):
                os.system('cls' if os.name == 'nt' else 'clear')
                
                self.actualizar_mercado()
                
                self.mostrar_mercado()
                portafolio.mostrar_resumen()
                
                if mostrar_diagrama and contador > 0:
                    print(portafolio.generar_diagrama_lineal())
                
                print(f"\n{Colors.BOLD}⏰ Actualización {contador + 1}{Colors.ENDC}")
                
                contador += 1
                if pasos > 0 and contador >= pasos:
                    break
                
                time.sleep(self.velocidad_simulacion)
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⏸️ Simulación detenida por el usuario{Colors.ENDC}")
        
        print(f"\n{Colors.GREEN}🏁 SIMULACIÓN FINALIZADA{Colors.ENDC}")
    
    def inicializar_activos_predeterminados(self):
        """Inicializa el mercado con activos predefinidos"""
        print(f"{Colors.CYAN}Inicializando mercado...{Colors.ENDC}")
        
        acciones = [
            Accion("AAPL", "Apple Inc.", 150.00, "Tecnología"),
            Accion("GOOGL", "Alphabet Inc.", 2800.00, "Tecnología"),
            Accion("AMZN", "Amazon.com Inc.", 3300.00, "Comercio Electrónico"),
            Accion("TSLA", "Tesla Inc.", 250.00, "Automotriz"),
            Accion("MSFT", "Microsoft Corp.", 330.00, "Tecnología"),
            Accion("NFLX", "Netflix Inc.", 450.00, "Entretenimiento"),
        ]
        
        criptos = [
            Criptomoneda("BTC", "Bitcoin", 45000.00),
            Criptomoneda("ETH", "Ethereum", 3000.00),
            Criptomoneda("ADA", "Cardano", 0.50),
            Criptomoneda("SOL", "Solana", 100.00),
            Criptomoneda("DOGE", "Dogecoin", 0.08),
        ]
        
        for accion in acciones:
            self.agregar_activo(accion)
        
        for cripto in criptos:
            self.agregar_activo(cripto)
        
        print(f"{Colors.GREEN}✓ Mercado inicializado con {len(self.activos)} activos{Colors.ENDC}\n")

# ====================== INTERFAZ PRINCIPAL ======================

class SimuladorMercado:
    """Clase principal del simulador con interfaz de usuario"""
    
    def __init__(self):
        self.mercado = Mercado()
        self.portafolio = None
        self.gestor_usuarios = GestorUsuarios()
        self.mostrar_diagrama = True
        
    def mostrar_menu_principal(self):
        """Muestra el menú principal de autenticación"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}🎯 SIMULADOR DE MERCADO DE VALORES{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"\n1. {Colors.GREEN}Iniciar Sesión{Colors.ENDC}")
        print(f"2. {Colors.BLUE}Registrar Usuario{Colors.ENDC}")
        print(f"3. {Colors.YELLOW}Cambiar Contraseña{Colors.ENDC}")
        print(f"0. {Colors.RED}Salir{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    
    def iniciar_sesion(self):
        """Maneja el inicio de sesión"""
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}🔐 INICIAR SESIÓN{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña = input(f"{Colors.BOLD}Contraseña: {Colors.ENDC}")
        
        success, mensaje = self.gestor_usuarios.iniciar_sesion(nombre, contraseña)
        print(f"\n{mensaje}")
        
        if success:
            self.portafolio = Portafolio(nombre, self.gestor_usuarios.usuario_actual.capital_inicial)
            return True
        return False
    
    def registrar_usuario(self):
        """Maneja el registro de nuevos usuarios"""
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}📝 REGISTRAR NUEVO USUARIO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña = input(f"{Colors.BOLD}Contraseña (mínimo 4 caracteres): {Colors.ENDC}")
        confirmar = input(f"{Colors.BOLD}Confirmar contraseña: {Colors.ENDC}")
        
        if contraseña != confirmar:
            print(f"\n{Colors.RED}❌ Las contraseñas no coinciden{Colors.ENDC}")
            return False
        
        capital_input = input(f"{Colors.BOLD}Capital inicial (default: $10,000): {Colors.ENDC}").strip()
        try:
            capital = float(capital_input) if capital_input and float(capital_input) > 0 else 10000
        except:
            capital = 10000
        
        success, mensaje = self.gestor_usuarios.registrar_usuario(nombre, contraseña, capital)
        print(f"\n{mensaje}")
        return success
    
    def cambiar_contraseña(self):
        """Maneja el cambio de contraseña"""
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}🔑 CAMBIAR CONTRASEÑA{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña_actual = input(f"{Colors.BOLD}Contraseña actual: {Colors.ENDC}")
        contraseña_nueva = input(f"{Colors.BOLD}Contraseña nueva (mínimo 4 caracteres): {Colors.ENDC}")
        confirmar = input(f"{Colors.BOLD}Confirmar contraseña nueva: {Colors.ENDC}")
        
        if contraseña_nueva != confirmar:
            print(f"\n{Colors.RED}❌ Las contraseñas nuevas no coinciden{Colors.ENDC}")
            return
        
        success, mensaje = self.gestor_usuarios.cambiar_contraseña(nombre, contraseña_actual, contraseña_nueva)
        print(f"\n{mensaje}")
    
    def mostrar_menu_inversor(self):
        """Muestra el menú principal del inversor"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📋 MENÚ PRINCIPAL{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"1. {Colors.GREEN}📊 Ver Mercado{Colors.ENDC}")
        print(f"2. {Colors.BLUE}💰 Ver Mi Portafolio{Colors.ENDC}")
        print(f"3. {Colors.GREEN}🛒 Comprar Activo{Colors.ENDC}")
        print(f"4. {Colors.RED}💸 Vender Activo{Colors.ENDC}")
        print(f"5. {Colors.YELLOW}🚀 Iniciar Simulación Automática{Colors.ENDC}")
        print(f"6. {Colors.MAGENTA}📈 Ver Historial de Rendimiento{Colors.ENDC}")
        print(f"7. {Colors.CYAN}📊 Ver Diagrama Lineal{Colors.ENDC}")
        print(f"8. {Colors.YELLOW}⚙ Configuración de Simulación{Colors.ENDC}")
        print(f"0. {Colors.RED}❌ Cerrar Sesión{Colors.ENDC}")
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
        
        self.mercado.iniciar_simulacion(self.portafolio, pasos, self.mostrar_diagrama)
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
            
            max_valor = max(self.portafolio.historial_valor)
            min_valor = min(self.portafolio.historial_valor)
            print(f"\n{Colors.BOLD}📊 Estadísticas:{Colors.ENDC}")
            print(f"  Valor Máximo: ${max_valor:.2f}")
            print(f"  Valor Mínimo: ${min_valor:.2f}")
            print(f"  Rendimiento Total: {self.portafolio.get_rendimiento():+.2f}%")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ver_diagrama_lineal(self):
        """Muestra el diagrama lineal del rendimiento"""
        print(self.portafolio.generar_diagrama_lineal())
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def configuracion_simulacion(self):
        """Configuración de la simulación"""
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}⚙ CONFIGURACIÓN DE SIMULACIÓN{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.ENDC}")
        
        print(f"\n1. Mostrar diagrama lineal: {'Sí' if self.mostrar_diagrama else 'No'}")
        print(f"2. Velocidad actual: {self.mercado.velocidad_simulacion} segundos")
        
        opcion = input(f"\n{Colors.BOLD}Selecciona opción a cambiar (1-2, 0 para salir): {Colors.ENDC}")
        
        if opcion == "1":
            self.mostrar_diagrama = not self.mostrar_diagrama
            print(f"\n✅ Diagrama lineal: {'Activado' if self.mostrar_diagrama else 'Desactivado'}")
        elif opcion == "2":
            try:
                nueva_vel = float(input("Nueva velocidad (segundos): "))
                if nueva_vel > 0:
                    self.mercado.velocidad_simulacion = nueva_vel
                    print(f"✅ Velocidad actualizada a {nueva_vel} segundos")
            except:
                print("❌ Velocidad inválida")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ejecutar_sesion_inversor(self):
        """Ejecuta la sesión de un inversor autenticado"""
        while True:
            self.mostrar_menu_inversor()
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
            elif opcion == "7":
                self.ver_diagrama_lineal()
            elif opcion == "8":
                self.configuracion_simulacion()
            elif opcion == "0":
                self.gestor_usuarios.cerrar_sesion()
                print(f"\n{Colors.GREEN}✅ Sesión cerrada{Colors.ENDC}")
                break
            else:
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                time.sleep(1)
    
    def ejecutar(self):
        """Ejecuta el simulador completo"""
        self.mercado.inicializar_activos_predeterminados()
        
        while True:
            self.mostrar_menu_principal()
            opcion = input(f"{Colors.BOLD}Selecciona una opción: {Colors.ENDC}").strip()
            
            if opcion == "1":
                if self.iniciar_sesion():
                    self.ejecutar_sesion_inversor()
            elif opcion == "2":
                self.registrar_usuario()
                time.sleep(2)
            elif opcion == "3":
                self.cambiar_contraseña()
                time.sleep(2)
            elif opcion == "0":
                print(f"\n{Colors.GREEN}✅ ¡Gracias por usar el simulador!{Colors.ENDC}")
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