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
from pyqtgraph.Qt import QtCore, QtWidgets
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
        self.volatilidad = 0.02
        
    def actualizar_precio(self):
        """Actualiza el precio de la acción con movimiento aleatorio"""
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.85)
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.15)
        self.precio_actual = nuevo_precio


class Criptomoneda(Activo):
    """Clase para criptomonedas (más volátiles)"""
    
    def __init__(self, simbolo: str, nombre: str, precio_inicial: float):
        super().__init__(simbolo, nombre, precio_inicial)
        self.volatilidad = 0.05
        
    def actualizar_precio(self):
        """Actualiza el precio de la criptomoneda con alta volatilidad"""
        cambio_pct = random.gauss(mu=0, sigma=self.volatilidad)
        nuevo_precio = self.precio_actual * (1 + cambio_pct)
        nuevo_precio = max(nuevo_precio, self.precio_actual * 0.6)
        nuevo_precio = min(nuevo_precio, self.precio_actual * 1.4)
        self.precio_actual = nuevo_precio

# ====================== PORTAFOLIO ======================

class Portafolio:
    """Clase que gestiona las inversiones"""
    
    def __init__(self, inversor_nombre: str, capital_inicial: float = 10000):
        self.inversor_nombre = inversor_nombre
        self.activos: Dict[Activo, float] = {}
        self.valor_total = capital_inicial
        self.efectivo = capital_inicial
        self.historial_valor = [capital_inicial]
        self.historial_tiempos = [datetime.now()]
        
    def agregar_activo(self, activo: Activo, cantidad: float) -> tuple:
        """Agrega un activo al portafolio"""
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
        if capital_inicial == 0:
            return 0
        return ((self.valor_total - capital_inicial) / capital_inicial) * 100

# ====================== MERCADO ======================

class Mercado:
    """Clase que maneja el mercado y la simulación"""
    
    def __init__(self):
        self.activos: List[Activo] = []
        self.simulando = False
        self.velocidad_simulacion = 1
        
    def agregar_activo(self, activo: Activo):
        """Agrega un activo al mercado"""
        self.activos.append(activo)
    
    def actualizar_mercado(self):
        """Actualiza todos los activos del mercado"""
        for activo in self.activos:
            activo.actualizar_precio()
    
    def inicializar_activos_predeterminados(self):
        """Inicializa el mercado con activos predefinidos"""
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
    """Ventana principal con gráficos PyQtGraph"""
    
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
        """Inicializa la interfaz"""
        self.setWindowTitle('Simulador de Mercado de Valores - Visualización en Tiempo Real')
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Layout horizontal para gráficos
        graphics_layout = QHBoxLayout()
        
        # === GRÁFICO 1: Precios de activos ===
        left_widget = pg.GraphicsLayoutWidget()
        left_widget.setBackground('w')
        
        # Gráfico de precios
        self.plot_precios = left_widget.addPlot(title="Evolución de Precios de Activos")
        self.plot_precios.setLabel('left', 'Precio', units='$')
        self.plot_precios.setLabel('bottom', 'Tiempo', units='pasos')
        self.plot_precios.showGrid(x=True, y=True, alpha=0.3)
        self.plot_precios.addLegend()
        
        # Diccionario para almacenar las curvas
        self.curvas = {}
        
        # Inicializar curvas para cada activo
        for i, activo in enumerate(self.mercado.activos):
            pen = pg.mkPen(color=self.colores[i % len(self.colores)], width=2)
            curva = self.plot_precios.plot(pen=pen, name=activo.simbolo)
            self.curvas[activo.simbolo] = {
                'curva': curva,
                'datos': [],
                'color': self.colores[i % len(self.colores)]
            }
        
        # === GRÁFICO 2: Rendimiento del portafolio ===
        self.plot_portafolio = left_widget.addPlot(title="Rendimiento del Portafolio", row=1, col=0)
        self.plot_portafolio.setLabel('left', 'Valor', units='$')
        self.plot_portafolio.setLabel('bottom', 'Tiempo', units='pasos')
        self.plot_portafolio.showGrid(x=True, y=True, alpha=0.3)
        
        # Curva del portafolio
        pen_portafolio = pg.mkPen(color=(255, 87, 34), width=3)
        self.curva_portafolio = self.plot_portafolio.plot(pen=pen_portafolio, name='Valor del Portafolio')
        
        # Línea del valor inicial
        pen_inicial = pg.mkPen(color=(128, 128, 128), width=1, style=QtCore.Qt.DashLine)
        self.linea_inicial = self.plot_portafolio.plot(pen=pen_inicial, name='Valor Inicial')
        
        # === Panel derecho: Información y controles ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Tabla de activos
        self.tabla_activos = QTableWidget()
        self.tabla_activos.setColumnCount(5)
        self.tabla_activos.setHorizontalHeaderLabels(['Símbolo', 'Nombre', 'Precio', 'Cambio %', 'Mi Cantidad'])
        self.tabla_activos.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(QLabel("<b>📊 MERCADO ACTUAL</b>"))
        right_layout.addWidget(self.tabla_activos)
        
        # Información del portafolio
        self.texto_portafolio = QTextEdit()
        self.texto_portafolio.setMaximumHeight(200)
        self.texto_portafolio.setReadOnly(True)
        right_layout.addWidget(QLabel("<b>💰 MI PORTAFOLIO</b>"))
        right_layout.addWidget(self.texto_portafolio)
        
        # Panel de control
        control_group = QGroupBox("Controles de Simulación")
        control_layout = QVBoxLayout()
        
        # Botones
        btn_layout = QHBoxLayout()
        self.btn_iniciar = QPushButton("▶ Iniciar")
        self.btn_iniciar.clicked.connect(self.iniciar_simulacion)
        self.btn_iniciar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.btn_detener = QPushButton("⏸ Detener")
        self.btn_detener.clicked.connect(self.detener_simulacion)
        self.btn_detener.setEnabled(False)
        self.btn_detener.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        
        self.btn_paso = QPushButton("⏩ Un Paso")
        self.btn_paso.clicked.connect(self.un_paso)
        
        btn_layout.addWidget(self.btn_iniciar)
        btn_layout.addWidget(self.btn_detener)
        btn_layout.addWidget(self.btn_paso)
        control_layout.addLayout(btn_layout)
        
        # Control de velocidad
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Velocidad (ms):"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(500)
        self.speed_slider.valueChanged.connect(self.cambiar_velocidad)
        self.speed_label = QLabel("500 ms")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        control_layout.addLayout(speed_layout)
        
        # Número de pasos
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Pasos a simular:"))
        self.steps_input = QSpinBox()
        self.steps_input.setRange(0, 1000)
        self.steps_input.setValue(0)
        self.steps_input.setSpecialValueText("∞")
        steps_layout.addWidget(self.steps_input)
        steps_layout.addStretch()
        control_layout.addLayout(steps_layout)
        
        control_group.setLayout(control_layout)
        right_layout.addWidget(control_group)
        
        # Estadísticas
        stats_group = QGroupBox("📈 Estadísticas en Vivo")
        stats_layout = QGridLayout()
        
        self.lbl_valor_actual = QLabel("$0.00")
        self.lbl_rendimiento = QLabel("0.00%")
        self.lbl_efectivo = QLabel("$0.00")
        self.lbl_inversiones = QLabel("$0.00")
        
        stats_layout.addWidget(QLabel("<b>Valor Total:</b>"), 0, 0)
        stats_layout.addWidget(self.lbl_valor_actual, 0, 1)
        stats_layout.addWidget(QLabel("<b>Rendimiento:</b>"), 1, 0)
        stats_layout.addWidget(self.lbl_rendimiento, 1, 1)
        stats_layout.addWidget(QLabel("<b>Efectivo:</b>"), 2, 0)
        stats_layout.addWidget(self.lbl_efectivo, 2, 1)
        stats_layout.addWidget(QLabel("<b>Inversiones:</b>"), 3, 0)
        stats_layout.addWidget(self.lbl_inversiones, 3, 1)
        
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        right_layout.addStretch()
        
        # Agregar widgets al layout principal
        graphics_layout.addWidget(left_widget, stretch=2)
        graphics_layout.addWidget(right_widget, stretch=1)
        main_layout.addLayout(graphics_layout)
        
        # Barra de estado
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Listo para simular - Presiona Iniciar")
        
        # Actualizar datos iniciales
        self.actualizar_tabla()
        self.actualizar_portafolio_texto()
        self.actualizar_estadisticas()
        
    def actualizar_tabla(self):
        """Actualiza la tabla de activos"""
        self.tabla_activos.setRowCount(len(self.mercado.activos))
        
        for i, activo in enumerate(self.mercado.activos):
            # Símbolo
            self.tabla_activos.setItem(i, 0, QTableWidgetItem(activo.simbolo))
            
            # Nombre
            self.tabla_activos.setItem(i, 1, QTableWidgetItem(activo.nombre))
            
            # Precio
            precio_item = QTableWidgetItem(f"${activo.precio_actual:.2f}")
            self.tabla_activos.setItem(i, 2, precio_item)
            
            # Cambio porcentual
            cambio = activo.get_cambio_porcentual()
            cambio_str = f"{cambio:+.2f}%"
            cambio_item = QTableWidgetItem(cambio_str)
            if cambio >= 0:
                cambio_item.setForeground(QBrush(QColor(76, 175, 80)))
            else:
                cambio_item.setForeground(QBrush(QColor(244, 67, 54)))
            self.tabla_activos.setItem(i, 3, cambio_item)
            
            # Cantidad en portafolio
            if activo in self.portafolio.activos:
                cantidad = self.portafolio.activos[activo]
                self.tabla_activos.setItem(i, 4, QTableWidgetItem(f"{cantidad:.4f}"))
            else:
                self.tabla_activos.setItem(i, 4, QTableWidgetItem("-"))
        
        self.tabla_activos.resizeColumnsToContents()
    
    def actualizar_portafolio_texto(self):
        """Actualiza el texto del portafolio"""
        texto = "<table width='100%'>"
        
        if not self.portafolio.activos:
            texto += "<tr><td colspan='2' align='center'><i>No tienes activos</i></td></tr>"
        else:
            texto += "<tr><th>Activo</th><th align='right'>Cantidad</th><th align='right'>Valor</th></tr>"
            for activo, cantidad in self.portafolio.activos.items():
                valor = cantidad * activo.precio_actual
                texto += f"<tr>"
                texto += f"<td><b>{activo.simbolo}</b></td>"
                texto += f"<td align='right'>{cantidad:.4f}</td>"
                texto += f"<td align='right'>${valor:.2f}</td>"
                texto += f"</tr>"
        
        texto += "</table>"
        self.texto_portafolio.setHtml(texto)
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas"""
        self.lbl_valor_actual.setText(f"${self.portafolio.valor_total:.2f}")
        
        rendimiento = self.portafolio.get_rendimiento()
        rendimiento_str = f"{rendimiento:+.2f}%"
        if rendimiento >= 0:
            self.lbl_rendimiento.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_rendimiento.setStyleSheet("color: #f44336; font-weight: bold;")
        self.lbl_rendimiento.setText(rendimiento_str)
        
        self.lbl_efectivo.setText(f"${self.portafolio.efectivo:.2f}")
        
        valor_inversiones = self.portafolio.valor_total - self.portafolio.efectivo
        self.lbl_inversiones.setText(f"${valor_inversiones:.2f}")
    
    def actualizar_graficos(self):
        """Actualiza todos los gráficos"""
        # Actualizar gráfico de precios
        for activo in self.mercado.activos:
            datos = self.curvas[activo.simbolo]['datos']
            datos.append(activo.precio_actual)
            
            # Mantener solo los últimos 100 puntos
            if len(datos) > 100:
                datos.pop(0)
            
            x_data = list(range(len(datos)))
            self.curvas[activo.simbolo]['curva'].setData(x_data, datos)
        
        # Actualizar gráfico del portafolio
        x_data = list(range(len(self.portafolio.historial_valor)))
        y_data = self.portafolio.historial_valor
        self.curva_portafolio.setData(x_data, y_data)
        
        # Actualizar línea de valor inicial
        if len(y_data) > 0:
            valor_inicial = y_data[0]
            self.linea_inicial.setData([0, len(y_data)], [valor_inicial, valor_inicial])
        
        # Auto-rango
        self.plot_precios.autoRange()
        self.plot_portafolio.autoRange()
    
    def actualizar_simulacion(self):
        """Actualiza un paso de simulación"""
        # Actualizar mercado
        self.mercado.actualizar_mercado()
        self.paso_actual += 1
        
        # Actualizar interfaz
        self.actualizar_tabla()
        self.actualizar_portafolio_texto()
        self.actualizar_estadisticas()
        self.actualizar_graficos()
        
        # Actualizar barra de estado
        self.statusBar.showMessage(f"Paso {self.paso_actual} - Valor: ${self.portafolio.valor_total:.2f}")
        
        # Verificar si se alcanzó el límite de pasos
        pasos_restantes = self.steps_input.value()
        if pasos_restantes > 0 and self.paso_actual >= pasos_restantes:
            self.detener_simulacion()
            QMessageBox.information(self, "Simulación Completa", 
                                  f"Se completaron {self.paso_actual} pasos\n"
                                  f"Rendimiento final: {self.portafolio.get_rendimiento():+.2f}%")
    
    def iniciar_simulacion(self):
        """Inicia la simulación"""
        if not self.simulando:
            self.simulando = True
            self.btn_iniciar.setEnabled(False)
            self.btn_detener.setEnabled(True)
            self.btn_paso.setEnabled(False)
            
            velocidad = self.speed_slider.value()
            self.timer.start(velocidad)
            self.statusBar.showMessage("Simulación en ejecución...")
    
    def detener_simulacion(self):
        """Detiene la simulación"""
        if self.simulando:
            self.simulando = False
            self.timer.stop()
            self.btn_iniciar.setEnabled(True)
            self.btn_detener.setEnabled(False)
            self.btn_paso.setEnabled(True)
            self.statusBar.showMessage("Simulación detenida")
    
    def un_paso(self):
        """Ejecuta un paso"""
        self.actualizar_simulacion()
    
    def cambiar_velocidad(self):
        """Cambia la velocidad de simulación"""
        velocidad = self.speed_slider.value()
        self.speed_label.setText(f"{velocidad} ms")
        if self.simulando:
            self.timer.setInterval(velocidad)
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        self.detener_simulacion()
        event.accept()

# ====================== INTERFAZ DE CONSOLA ======================

class SimuladorMercado:
    """Clase principal del simulador con interfaz de consola"""
    
    def __init__(self):
        self.mercado = Mercado()
        self.portafolio = None
        self.gestor_usuarios = GestorUsuarios()
        
    def limpiar_pantalla(self):
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def mostrar_menu_principal(self):
        """Muestra el menú principal"""
        self.limpiar_pantalla()
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
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
            return True
        else:
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
            return False
    
    def registrar_usuario(self):
        """Maneja el registro de usuarios"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}📝 REGISTRAR USUARIO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña = input(f"{Colors.BOLD}Contraseña (mínimo 4 caracteres): {Colors.ENDC}")
        confirmar = input(f"{Colors.BOLD}Confirmar contraseña: {Colors.ENDC}")
        
        if contraseña != confirmar:
            print(f"\n{Colors.RED}❌ Las contraseñas no coinciden{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        capital_input = input(f"{Colors.BOLD}Capital inicial (default: $10,000): {Colors.ENDC}").strip()
        try:
            capital = float(capital_input) if capital_input else 10000
        except:
            capital = 10000
        
        success, mensaje = self.gestor_usuarios.registrar_usuario(nombre, contraseña, capital)
        print(f"\n{mensaje}")
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def cambiar_contraseña(self):
        """Maneja el cambio de contraseña"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}🔑 CAMBIAR CONTRASEÑA{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*50}{Colors.ENDC}")
        
        nombre = input(f"\n{Colors.BOLD}Usuario: {Colors.ENDC}").strip()
        contraseña_actual = input(f"{Colors.BOLD}Contraseña actual: {Colors.ENDC}")
        contraseña_nueva = input(f"{Colors.BOLD}Contraseña nueva: {Colors.ENDC}")
        confirmar = input(f"{Colors.BOLD}Confirmar contraseña: {Colors.ENDC}")
        
        if contraseña_nueva != confirmar:
            print(f"\n{Colors.RED}❌ Las contraseñas no coinciden{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        success, mensaje = self.gestor_usuarios.cambiar_contraseña(nombre, contraseña_actual, contraseña_nueva)
        print(f"\n{mensaje}")
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def mostrar_menu_inversor(self):
        """Muestra el menú del inversor"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📋 MENÚ PRINCIPAL{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"1. {Colors.GREEN}📊 Ver Mercado{Colors.ENDC}")
        print(f"2. {Colors.BLUE}💰 Ver Mi Portafolio{Colors.ENDC}")
        print(f"3. {Colors.GREEN}🛒 Comprar Activo{Colors.ENDC}")
        print(f"4. {Colors.RED}💸 Vender Activo{Colors.ENDC}")
        print(f"5. {Colors.MAGENTA}🎨 Iniciar Simulación con Gráficos{Colors.ENDC}")
        print(f"6. {Colors.YELLOW}📈 Ver Historial{Colors.ENDC}")
        print(f"9. {Colors.RED}❌ Cerrar Sesión{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    
    def ver_mercado(self):
        """Muestra el mercado"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📈 MERCADO DE VALORES{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        
        for activo in self.mercado.activos:
            print(f"  {activo}")
        
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ver_portafolio(self):
        """Muestra el portafolio"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}📊 PORTAFOLIO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}💰 Efectivo: ${self.portafolio.efectivo:.2f}{Colors.ENDC}")
        print(f"{Colors.BOLD}📈 Rendimiento: {self.portafolio.get_rendimiento():+.2f}%{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}📦 Activos:{Colors.ENDC}")
        if not self.portafolio.activos:
            print(f"  {Colors.YELLOW}No tienes activos{Colors.ENDC}")
        else:
            for activo, cantidad in self.portafolio.activos.items():
                valor = cantidad * activo.precio_actual
                print(f"  {activo.simbolo}: {cantidad:.4f} unidades - ${valor:.2f}")
        
        print(f"\n{Colors.BOLD}💎 Valor Total: ${self.portafolio.valor_total:.2f}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def comprar_activo(self):
        """Compra un activo"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}🛒 COMPRAR ACTIVO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        for i, activo in enumerate(self.mercado.activos, 1):
            print(f"{i}. {activo}")
        
        try:
            opcion = int(input(f"\n{Colors.BOLD}Opción: {Colors.ENDC}"))
            if opcion < 1 or opcion > len(self.mercado.activos):
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
                return
            
            activo = self.mercado.activos[opcion - 1]
            cantidad = float(input(f"{Colors.BOLD}Cantidad: {Colors.ENDC}"))
            
            if cantidad <= 0:
                print(f"{Colors.RED}❌ Cantidad inválida{Colors.ENDC}")
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
                return
            
            success, mensaje = self.portafolio.agregar_activo(activo, cantidad)
            print(f"\n{mensaje}")
            
        except ValueError:
            print(f"{Colors.RED}❌ Entrada inválida{Colors.ENDC}")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def vender_activo(self):
        """Vende un activo"""
        if not self.portafolio.activos:
            self.limpiar_pantalla()
            print(f"\n{Colors.RED}❌ No tienes activos para vender{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
            return
        
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.RED}💸 VENDER ACTIVO{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        activos_lista = list(self.portafolio.activos.keys())
        for i, activo in enumerate(activos_lista, 1):
            cantidad = self.portafolio.activos[activo]
            print(f"{i}. {activo.simbolo} - Cantidad: {cantidad:.4f}")
        
        try:
            opcion = int(input(f"\n{Colors.BOLD}Opción: {Colors.ENDC}"))
            if opcion < 1 or opcion > len(activos_lista):
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
                return
            
            activo = activos_lista[opcion - 1]
            respuesta = input(f"{Colors.BOLD}Cantidad (Enter para todo): {Colors.ENDC}").strip()
            
            if respuesta == "":
                cantidad = None
            else:
                cantidad = float(respuesta)
                if cantidad <= 0:
                    print(f"{Colors.RED}❌ Cantidad inválida{Colors.ENDC}")
                    input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
                    return
            
            success, mensaje = self.portafolio.vender_activo(activo, cantidad)
            print(f"\n{mensaje}")
            
        except ValueError:
            print(f"{Colors.RED}❌ Entrada inválida{Colors.ENDC}")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def iniciar_simulacion_grafica(self):
        """Inicia la simulación con interfaz gráfica"""
        try:
            # Crear aplicación Qt
            app = QApplication(sys.argv)
            
            # Crear y mostrar ventana
            ventana = VentanaSimulacion(self.mercado, self.portafolio)
            ventana.show()
            
            # Ejecutar aplicación
            sys.exit(app.exec_())
            
        except Exception as e:
            print(f"{Colors.RED}Error al iniciar interfaz gráfica: {e}{Colors.ENDC}")
            print(f"{Colors.YELLOW}Asegúrate de tener instalado: pip install pyqt5 pyqtgraph numpy{Colors.ENDC}")
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ver_historial(self):
        """Muestra el historial"""
        self.limpiar_pantalla()
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}📈 HISTORIAL{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
        
        if len(self.portafolio.historial_valor) <= 1:
            print(f"{Colors.YELLOW}No hay historial aún{Colors.ENDC}")
        else:
            print(f"\n{Colors.BOLD}Últimos 10 valores:{Colors.ENDC}")
            inicio = max(0, len(self.portafolio.historial_valor) - 10)
            for i in range(inicio, len(self.portafolio.historial_valor)):
                valor = self.portafolio.historial_valor[i]
                cambio = ((valor - self.portafolio.historial_valor[0]) / self.portafolio.historial_valor[0]) * 100
                print(f"  Paso {i}: ${valor:.2f} ({cambio:+.2f}%)")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.ENDC}")
    
    def ejecutar_sesion_inversor(self):
        """Ejecuta la sesión del inversor"""
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
                self.iniciar_simulacion_grafica()
            elif opcion == "6":
                self.ver_historial()
            elif opcion == "9":
                print(f"\n{Colors.GREEN}✅ Sesión cerrada{Colors.ENDC}")
                time.sleep(1)
                break
            else:
                print(f"{Colors.RED}❌ Opción inválida{Colors.ENDC}")
                time.sleep(1)
    
    def ejecutar(self):
        """Ejecuta el simulador"""
        self.mercado.inicializar_activos_predeterminados()
        
        while True:
            self.mostrar_menu_principal()
            opcion = input(f"{Colors.BOLD}Selecciona una opción: {Colors.ENDC}").strip()
            
            if opcion == "1":
                if self.iniciar_sesion():
                    self.ejecutar_sesion_inversor()
            elif opcion == "2":
                self.registrar_usuario()
            elif opcion == "3":
                self.cambiar_contraseña()
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
        import traceback
        traceback.print_exc()