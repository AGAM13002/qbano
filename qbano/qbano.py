# -*- coding: utf-8 -*-
"""
QBan(o) - géocodage d'adresses avec la Base Adresse Nationale (BAN).

Ce module contient la classe du plugin chargée par QGIS (barre d'outils et menu).
Licence : GNU GPL v2 ou ultérieure.
"""
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

from .qbano_dialog import QbanoDialog
from .qbano_provider import QbanoProvider


class Qbano:
    """Implémentation du plugin QGIS."""

    MENU = '&QBan(o)'

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dlg = None
        self.provider = None

    def initProcessing(self):
        """Enregistre les algorithmes Géocodage / Géocodage inverse."""
        self.provider = QbanoProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Crée l'entrée de menu et le bouton de la barre d'outils."""
        self.initProcessing()
        icon = QIcon(os.path.join(self.plugin_dir, 'icon.png'))
        self.action = QAction(icon, 'QBan(o)', self.iface.mainWindow())
        self.action.setToolTip('Géocoder des adresses avec la BAN')
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.MENU, self.action)

    def unload(self):
        """Retire l'entrée de menu et le bouton de la barre d'outils."""
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
        if self.action is not None:
            self.iface.removePluginMenu(self.MENU, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.deleteLater()
            self.action = None
        if self.dlg is not None:
            self.dlg.deleteLater()
            self.dlg = None

    def run(self):
        """Affiche la boîte de dialogue."""
        if self.dlg is None:
            self.dlg = QbanoDialog(self.iface.mainWindow())
        self.dlg.chercherCouches()
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()
