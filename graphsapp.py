import random
import time
import os
import json
import hashlib
import sys
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

# Importar PyQtGraph y PyQt5
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Configurar PyQtGraph
pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

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
        return hashlib.sha256(contraseña.encode()).hexdigest()
    
    def verificar_contraseña(self, contraseña: str) -> bool:
        return self.contraseña_hash == self._hash_contraseña(contraseña)
    
    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "contraseña_hash": self.contraseña_hash,
            "capital_inicial": self.capital_inicial,
            "fecha_creacion": self.fecha_creacion,
            "historial_inversiones": self.historial_inversiones
        }
    
    @classmethod
    def from_dict(cls, data: dict):
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
        if os.path.exists(Usuario.ARCHIVO_USUARIOS):
            try:
                with open(Usuario.ARCHIVO_USUARIOS, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for nombre, datos in data.items():
                        self.usuarios[nombre] = Usuario.from_dict(datos)
            except Exception as e:
                print(f"Error al cargar usuarios: {e}")
    
    def _guardar_usuarios(self):
        data = {nombre: usuario.to_dict() for nombre, usuario in self.usuarios.items()}
        with open(Usuario.ARCHIVO_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def registrar_usuario(self, nombre: str, contraseña: str, capital: float = 10000) -> tuple:
        if nombre in self.usuarios:
            return False, "❌ El nombre de usuario ya existe"
        if len(contraseña) < 4:
            return False, "❌ La contraseña debe tener al menos 4 caracteres"
        usuario = Usuario(nombre, contraseña, capital)
        self.usuarios[nombre] = usuario
        self._guardar_usuarios()
        return True, f"✅ Usuario '{nombre}' registrado exitosamente"
    
    def iniciar_sesion(self, nombre: str, contraseña: str) -> tuple:
        if nombre not in self.usuarios:
            return False, "❌ Usuario no encontrado"
        if self.usuarios[nombre].verificar_contraseña(contraseña):
            self.usuario_actual = self.usuarios[nombre]
            return True, f"✅ Bienvenido {nombre}!"
        return False, "❌ Contraseña incorrecta"
    
    def cambiar_contraseña(self, nombre: str, contraseña_actual: str, contraseña_nueva: str) -> tuple:
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
        self.usuario_actual = None

# ====================== ACTIVOS FINANCIEROS ======================

class Activo(ABC):
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float):
        self.simbolo = simbolo
        self.nombre = nombre
        self._precio_actual = precio_inicial
        self.precio_anterior = precio_inicial
        self.historial_precios = [precio_inicial]
        self._observers = []
        
    @abstractmethod
    def actualizar_precio(self):
        pass
    
    @property
    def precio_actual(self):
        return self._precio_actual
    
    @precio_actual.setter
    def precio_actual(self, nuevo_precio):
        if nuevo_precio != self._precio_actual:
            self.precio_anterior = self._precio_actual
            self._precio_actual = nuevo_precio
            self.historial_precios.append(nuevo_precio)
            for observer in self._observers:
                observer.actualizar(self)
    
    def agregar_observador(self, observer):
        self._observers.append(observer)
    
    def get_cambio_porcentual(self) -> float:
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
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float, sector: str):
        super().__init__(simbolo, nombre, precio_inicial)
        self.sector = sector
        self.volatilidad = 0.02
        
    def actualizar_precio(self):
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.85)
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.15)
        self.precio_actual = nuevo_precio


class Criptomoneda(Activo):
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float):
        super().__init__(simbolo, nombre, precio_inicial)
        self.volatilidad = 0.05
        
    def actualizar_precio(self):
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.6)
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.4)
        self.precio_actual = nuevo_precio

# ====================== PORTAFOLIO ======================

class Portafolio:
    def __init__(self, inversor_nombre: str, capital_inicial: float = 10000):
        self.inversor_nombre = inversor_nombre
        self.activos: Dict[Activo, float] = {}
        self.valor_total = capital_inicial
        self.efectivo = capital_inicial
        self.historial_valor = [capital_inicial]
        self.historial_tiempos = [datetime.now()]
        
    def agregar_activo(self, activo: Activo, cantidad: float) -> tuple:
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
        self.actualizar_valor_total()
    
    def actualizar_valor_total(self):
        valor_inversiones = sum(cantidad * activo.precio_actual for activo, cantidad in self.activos.items())
        nuevo_valor_total = valor_inversiones + self.efectivo
        self.valor_total = nuevo_valor_total
        self.historial_valor.append(nuevo_valor_total)
        self.historial_tiempos.append(datetime.now())
    
    def get_rendimiento(self) -> float:
        capital_inicial = self.historial_valor[0]
        if capital_inicial == 0:
            return 0
        return ((self.valor_total - capital_inicial) / capital_inicial) * 100

# ====================== MERCADO ======================

class Mercado:
    def __init__(self):
        self.activos: List[Activo] = []
        
    def agregar_activo(self, activo: Activo):
        self.activos.append(activo)
    
    def actualizar_mercado(self):
        for activo in self.activos:
            activo.actualizar_precio()
    
    def inicializar_activos_predeterminados(self):
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

# ====================== INTERFAZ GRÁFICA CON PYQTGRAPH ======================

class VentanaSimulacion(QMainWindow):
    def __init__(self, mercado, portafolio):
        super().__init__()
        self.mercado = mercado
        self.portafolio = portafolio
        self.simulando = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_simulacion)
        self.paso_actual = 0
        self.colores = [
            (255, 99, 132), (54, 162, 235), (255, 206, 86),
            (75, 192, 192), (153, 102, 255), (255, 159, 64),
            (199, 0, 57), (0, 150, 136), (244, 67, 54)
        ]
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Simulador de Mercado - Visualización en Tiempo Real')
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        graphics_layout = QHBoxLayout()
        
        # Widget de gráficos
        left_widget = pg.GraphicsLayoutWidget()
        left_widget.setBackground('w')
        
        # Gráfico de precios
        self.plot_precios = left_widget.addPlot(title="Evolución de Precios de Activos")
        self.plot_precios.setLabel('left', 'Precio', units='$')
        self.plot_precios.setLabel('bottom', 'Tiempo', units='pasos')
        self.plot_precios.showGrid(x=True, y=True, alpha=0.3)
        self.plot_precios.addLegend()
        
        self.curvas = {}
        for i, activo in enumerate(self.mercado.activos):
            pen = pg.mkPen(color=self.colores[i % len(self.colores)], width=2)
            curva = self.plot_precios.plot(pen=pen, name=activo.simbolo)
            self.curvas[activo.simbolo] = {'curva': curva, 'datos': []}
        
        # Gráfico del portafolio
        self.plot_portafolio = left_widget.addPlot(title="Rendimiento del Portafolio", row=1, col=0)
        self.plot_portafolio.setLabel('left', 'Valor', units='$')
        self.plot_portafolio.setLabel('bottom', 'Tiempo', units='pasos')
        self.plot_portafolio.showGrid(x=True, y=True, alpha=0.3)
        
        pen_portafolio = pg.mkPen(color=(255, 87, 34), width=3)
        self.curva_portafolio = self.plot_portafolio.plot(pen=pen_portafolio, name='Valor del Portafolio')
        pen_inicial = pg.mkPen(color=(128, 128, 128), width=1, style=QtCore.Qt.DashLine)
        self.linea_inicial = self.plot_portafolio.plot(pen=pen_inicial, name='Valor Inicial')
        
        # Panel derecho
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.tabla_activos = QTableWidget()
        self.tabla_activos.setColumnCount(5)
        self.tabla_activos.setHorizontalHeaderLabels(['Símbolo', 'Nombre', 'Precio', 'Cambio %', 'Mi Cantidad'])
        right_layout.addWidget(QLabel("<b>📊 MERCADO ACTUAL</b>"))
        right_layout.addWidget(self.tabla_activos)
        
        self.texto_portafolio = QTextEdit()
        self.texto_portafolio.setMaximumHeight(200)
        self.texto_portafolio.setReadOnly(True)
        right_layout.addWidget(QLabel("<b>💰 MI PORTAFOLIO</b>"))
        right_layout.addWidget(self.texto_portafolio)
        
        # Controles
        control_group = QGroupBox("Controles")
        control_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_iniciar = QPushButton("▶ Iniciar")
        self.btn_iniciar.clicked.connect(self.iniciar_simulacion)
        self.btn_iniciar.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.btn_detener = QPushButton("⏸ Detener")
        self.btn_detener.clicked.connect(self.detener_simulacion)
        self.btn_detener.setEnabled(False)
        self.btn_detener.setStyleSheet("background-color: #f44336; color: white;")
        
        btn_layout.addWidget(self.btn_iniciar)
        btn_layout.addWidget(self.btn_detener)
        control_layout.addLayout(btn_layout)
        
        # Velocidad
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Velocidad:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(500)
        self.speed_slider.valueChanged.connect(self.cambiar_velocidad)
        self.speed_label = QLabel("500 ms")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        control_layout.addLayout(speed_layout)
        
        control_group.setLayout(control_layout)
        right_layout.addWidget(control_group)
        
        # Botón para cerrar
        btn_cerrar = QPushButton("❌ Cerrar y Volver al Menú")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        right_layout.addWidget(btn_cerrar)
        
        right_layout.addStretch()
        
        graphics_layout.addWidget(left_widget, stretch=2)
        graphics_layout.addWidget(right_widget, stretch=1)
        main_layout.addLayout(graphics_layout)
        
        self.actualizar_tabla()
        self.actualizar_portafolio()
        
    def actualizar_tabla(self):
        self.tabla_activos.setRowCount(len(self.mercado.activos))
        for i, activo in enumerate(self.mercado.activos):
            self.tabla_activos.setItem(i, 0, QTableWidgetItem(activo.simbolo))
            self.tabla_activos.setItem(i, 1, QTableWidgetItem(activo.nombre))
            self.tabla_activos.setItem(i, 2, QTableWidgetItem(f"${activo.precio_actual:.2f}"))
            cambio = activo.get_cambio_porcentual()
            cambio_item = QTableWidgetItem(f"{cambio:+.2f}%")
            cambio_item.setForeground(QBrush(QColor(76, 175, 80) if cambio >= 0 else QColor(244, 67, 54)))
            self.tabla_activos.setItem(i, 3, cambio_item)
            if activo in self.portafolio.activos:
                self.tabla_activos.setItem(i, 4, QTableWidgetItem(f"{self.portafolio.activos[activo]:.4f}"))
            else:
                self.tabla_activos.setItem(i, 4, QTableWidgetItem("-"))
        self.tabla_activos.resizeColumnsToContents()
    
    def actualizar_portafolio(self):
        texto = "<table width='100%'>"
        if not self.portafolio.activos:
            texto += "<td><td colspan='2'><i>No tienes activos</i></td></tr>"
        else:
            for activo, cantidad in self.portafolio.activos.items():
                valor = cantidad * activo.precio_actual
                texto += f"<tr><td><b>{activo.simbolo}</b></td><td align='right'>{cantidad:.4f}</td><td align='right'>${valor:.2f}</td></tr>"
        texto += "</table>"
        self.texto_portafolio.setHtml(texto)
    
    def actualizar_graficos(self):
        for activo in self.mercado.activos:
            datos = self.curvas[activo.simbolo]['datos']
            datos.append(activo.precio_actual)
            if len(datos) > 100:
                datos.pop(0)
            self.curvas[activo.simbolo]['curva'].setData(list(range(len(datos))), datos)
        
        x_data = list(range(len(self.portafolio.historial_valor)))
        y_data = self.portafolio.historial_valor
        self.curva_portafolio.setData(x_data, y_data)
        if len(y_data) > 0:
            self.linea_inicial.setData([0, len(y_data)], [y_data[0], y_data[0]])
        
    def actualizar_simulacion(self):
        self.mercado.actualizar_mercado()
        self.paso_actual += 1
        self.actualizar_tabla()
        self.actualizar_portafolio()
        self.actualizar_graficos()
        self.setWindowTitle(f"Simulación - Paso {self.paso_actual} - Valor: ${self.portafolio.valor_total:.2f}")
    
    def iniciar_simulacion(self):
        if not self.simulando:
            self.simulando = True
            self.btn_iniciar.setEnabled(False)
            self.btn_detener.setEnabled(True)
            self.timer.start(self.speed_slider.value())
    
    def detener_simulacion(self):
        if self.simulando:
            self.simulando = False
            self.timer.stop()
            self.btn_iniciar.setEnabled(True)
            self.btn_detener.setEnabled(False)
    
    def cambiar_velocidad(self):
        velocidad = self.speed_slider.value()
        self.speed_label.setText(f"{velocidad} ms")
        if self.simulando:
            self.timer.setInterval(velocidad)
    
    def closeEvent(self, event):
        self.detener_simulacion()
        event.accept()

# ====================== INTERFAZ DE CONSOLA ======================

class SimuladorMercado:
    def __init__(self):
        self.mercado = Mercado()
        self.portafolio = None
        self.gestor_usuarios = GestorUsuarios()
        
    def limpiar_pantalla(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def mostrar_menu_principal(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}🎯 SIMULADOR DE MERCADO DE VALORES{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"\n1. {Colors.GREEN}Iniciar Sesión{Colors.ENDC}")
        print(f"2. {Colors.BLUE}Registrar Usuario{Colors.ENDC}")
        print(f"3. {Colors.YELLOW}Cambiar Contraseña{Colors.ENDC}")
        print(f"0. {Colors.RED}Salir{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    
    def mostrar_menu_inversor(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📋 MENÚ PRINCIPAL{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"1. {Colors.GREEN}📊 Ver Mercado{Colors.ENDC}")
        print(f"2. {Colors.BLUE}💰 Ver Mi Portafolio{Colors.ENDC}")
        print(f"3. {Colors.GREEN}🛒 Comprar Activo{Colors.ENDC}")
        print(f"4. {Colors.RED}💸 Vender Activo{Colors.ENDC}")
        print(f"5. {Colors.MAGENTA}🎨 Simulación con Gráficos{Colors.ENDC}")
        print(f"6. {Colors.YELLOW}📈 Ver Rendimiento{Colors.ENDC}")
        print(f"9. {Colors.RED}❌ Cerrar Sesión{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    
    def iniciar_sesion(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}🔐 INICIAR SESIÓN{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña = input(f"{Colors.BOLD}Contraseña: {Colors.ENDC}")
        success, mensaje = self.gestor_usuarios.iniciar_sesion(nombre, contraseña)
        print(f"\n{mensaje}")
        if success:
            self.portafolio = Portafolio(nombre, self.gestor_usuarios.usuario_actual.capital_inicial)
            input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
            return True
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
        return False
    
    def registrar_usuario(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}📝 REGISTRAR USUARIO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña = input(f"{Colors.BOLD}Contraseña (mínimo 4): {Colors.ENDC}")
        confirmar = input(f"{Colors.BOLD}Confirmar: {Colors.ENDC}")
        if contraseña != confirmar:
            print(f"\n{Colors.RED}❌ No coinciden{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
            return
        capital_input = input(f"{Colors.BOLD}Capital inicial (default $10,000): {Colors.ENDC}").strip()
        capital = float(capital_input) if capital_input else 10000
        success, mensaje = self.gestor_usuarios.registrar_usuario(nombre, contraseña, capital)
        print(f"\n{mensaje}")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def cambiar_contraseña(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}🔑 CAMBIAR CONTRASEÑA{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        actual = input(f"{Colors.BOLD}Contraseña actual: {Colors.ENDC}")
        nueva = input(f"{Colors.BOLD}Contraseña nueva: {Colors.ENDC}")
        confirmar = input(f"{Colors.BOLD}Confirmar: {Colors.ENDC}")
        if nueva != confirmar:
            print(f"\n{Colors.RED}❌ No coinciden{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
            return
        success, mensaje = self.gestor_usuarios.cambiar_contraseña(nombre, actual, nueva)
        print(f"\n{mensaje}")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def ver_mercado(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📈 MERCADO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        for activo in self.mercado.activos:
            print(f"  {activo}")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def ver_portafolio(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}💰 PORTAFOLIO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Efectivo: ${self.portafolio.efectivo:.2f}{Colors.ENDC}")
        print(f"{Colors.BOLD}Rendimiento: {self.portafolio.get_rendimiento():+.2f}%{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Activos:{Colors.ENDC}")
        if not self.portafolio.activos:
            print(f"  {Colors.YELLOW}No tienes activos{Colors.ENDC}")
        else:
            for activo, cantidad in self.portafolio.activos.items():
                valor = cantidad * activo.precio_actual
                print(f"  {activo.simbolo}: {cantidad:.4f} - ${valor:.2f}")
        print(f"\n{Colors.BOLD}Valor Total: ${self.portafolio.valor_total:.2f}{Colors.ENDC}")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def comprar_activo(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}🛒 COMPRAR{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        for i, activo in enumerate(self.mercado.activos, 1):
            print(f"{i}. {activo}")
        try:
            opcion = int(input(f"\n{Colors.BOLD}Opción: {Colors.ENDC}"))
            if 1 <= opcion <= len(self.mercado.activos):
                activo = self.mercado.activos[opcion - 1]
                cantidad = float(input(f"{Colors.BOLD}Cantidad: {Colors.ENDC}"))
                if cantidad > 0:
                    success, msg = self.portafolio.agregar_activo(activo, cantidad)
                    print(f"\n{msg}")
        except:
            print(f"\n{Colors.RED}❌ Error{Colors.ENDC}")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def vender_activo(self):
        if not self.portafolio.activos:
            print(f"\n{Colors.RED}❌ No tienes activos{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
            return
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.RED}💸 VENDER{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        activos_lista = list(self.portafolio.activos.keys())
        for i, activo in enumerate(activos_lista, 1):
            print(f"{i}. {activo.simbolo} - {self.portafolio.activos[activo]:.4f}")
        try:
            opcion = int(input(f"\n{Colors.BOLD}Opción: {Colors.ENDC}"))
            if 1 <= opcion <= len(activos_lista):
                activo = activos_lista[opcion - 1]
                respuesta = input(f"{Colors.BOLD}Cantidad (Enter=todo): {Colors.ENDC}").strip()
                cantidad = None if respuesta == "" else float(respuesta)
                success, msg = self.portafolio.vender_activo(activo, cantidad)
                print(f"\n{msg}")
        except:
            print(f"\n{Colors.RED}❌ Error{Colors.ENDC}")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def iniciar_simulacion_grafica(self):
        """Inicia la simulación gráfica - AL CERRAR LA VENTANA VUELVE AL MENÚ"""
        try:
            # Crear aplicación Qt
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Crear y mostrar ventana
            ventana = VentanaSimulacion(self.mercado, self.portafolio)
            ventana.show()
            
            # Ejecutar aplicación - Esto se queda aquí hasta que cierres la ventana
            app.exec_()
            
            # Cuando se cierra la ventana, continúa aquí
            print(f"\n{Colors.GREEN}✅ Ventana cerrada. Volviendo al menú...{Colors.ENDC}")
            time.sleep(1)
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.ENDC}")
            print(f"{Colors.YELLOW}Instala: pip install pyqt5 pyqtgraph numpy{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def ver_rendimiento(self):
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}📈 RENDIMIENTO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        if len(self.portafolio.historial_valor) <= 1:
            print(f"{Colors.YELLOW}No hay datos{Colors.ENDC}")
        else:
            print(f"\n{Colors.BOLD}Últimos valores:{Colors.ENDC}")
            inicio = max(0, len(self.portafolio.historial_valor) - 10)
            for i in range(inicio, len(self.portafolio.historial_valor)):
                valor = self.portafolio.historial_valor[i]
                cambio = ((valor - self.portafolio.historial_valor[0]) / self.portafolio.historial_valor[0]) * 100
                print(f"  Paso {i}: ${valor:.2f} ({cambio:+.2f}%)")
        input(f"\n{Colors.YELLOW}Presiona Enter...{Colors.ENDC}")
    
    def ejecutar_sesion_inversor(self):
        while True:
            self.mostrar_menu_inversor()
            opcion = input(f"{Colors.BOLD}Opción: {Colors.ENDC}").strip()
            if opcion == "1":
                self.ver_mercado()
            elif opcion == "2":
                self.ver_portafolio()
            elif opcion == "3":
                self.comprar_activo()
            elif opcion == "4":
                self.vender_activo()
            elif opcion == "5":
                self.iniciar_simulacion_grafica()
            elif opcion == "6":
                self.ver_rendimiento()
            elif opcion == "9":
                print(f"\n{Colors.GREEN}✅ Sesión cerrada{Colors.ENDC}")
                time.sleep(1)
                break
            else:
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                time.sleep(1)
    
    def ejecutar(self):
        self.mercado.inicializar_activos_predeterminados()
        while True:
            self.mostrar_menu_principal()
            opcion = input(f"{Colors.BOLD}Opción: {Colors.ENDC}").strip()
            if opcion == "1":
                if self.iniciar_sesion():
                    self.ejecutar_sesion_inversor()
            elif opcion == "2":
                self.registrar_usuario()
            elif opcion == "3":
                self.cambiar_contraseña()
            elif opcion == "0":
                print(f"\n{Colors.GREEN}✅ ¡Gracias!{Colors.ENDC}")
                break
            else:
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                time.sleep(1)

# ====================== EJECUCIÓN ======================

if __name__ == "__main__":
    try:
        simulador = SimuladorMercado()
        simulador.ejecutar()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 ¡Hasta luego!{Colors.ENDC}")