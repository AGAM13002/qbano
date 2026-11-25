# -*- coding: utf-8 -*-
"""
QBano - boîte de dialogue de géocodage avec la Base Adresse Nationale (BAN).

Licence : GNU GPL v2 ou ultérieure.
"""
import os
import re
import unicodedata

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import QMetaType
from qgis.core import (
    NULL,
    Qgis,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)

from . import ban
from .documentation import DOCUMENTATION_HTML

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QBano_dialog_base.ui'))

CARACTERES_A_REMPLACER = re.compile(r'[\"\'\\.,:;]')


def _texte(valeur):
    """Convertit une valeur d'attribut en texte nettoyé ('' si vide ou NULL)."""
    if valeur is None or valeur == NULL:
        return ''
    if isinstance(valeur, float) and valeur.is_integer():
        valeur = int(valeur)
    texte = str(valeur)
    # "13001.0" (nombre lu comme décimal) -> "13001"
    texte = re.sub(r'^(\d+)\.0+$', r'\1', texte.strip())
    texte = CARACTERES_A_REMPLACER.sub(' ', texte)
    return ' '.join(texte.split())


def _sans_accents(texte):
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('ascii')


class QBanoDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._charger.clicked.connect(self.chercherCouches)
        self._listecouches.currentIndexChanged.connect(self.remplirChampAdresse)
        self._geocoder.clicked.connect(self.geocoder)
        self._documentation.setHtml(DOCUMENTATION_HTML)

    # ------------------------------------------------------------------ couches
    def chercherCouches(self):
        """Liste les couches vectorielles (avec ou sans géométrie) du projet."""
        self._listecouches.blockSignals(True)
        self._listecouches.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self._listecouches.addItem(layer.name(), layer.id())
        self._listecouches.blockSignals(False)
        self.remplirChampAdresse()

    def _couche_courante(self):
        layer_id = self._listecouches.currentData()
        if layer_id is None:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    def remplirChampAdresse(self, *_):
        """Remplit les listes de champs avec ceux de la couche choisie."""
        for combo in (self._champadresse, self._champcp,
                      self._champinsee, self._champville):
            combo.clear()
        layer = self._couche_courante()
        if layer is None:
            return
        for combo in (self._champcp, self._champinsee, self._champville):
            combo.addItem('')
        for field in layer.fields():
            for combo in (self._champadresse, self._champcp,
                          self._champinsee, self._champville):
                combo.addItem(field.name())

    # ---------------------------------------------------------------- géocodage
    def deboguer(self, texte):
        QgsMessageLog.logMessage(str(texte), tag='QBano_AGAM', level=Qgis.Info)

    @staticmethod
    def _nom_libre(nom, existants):
        """Évite un doublon avec un champ déjà présent dans la couche source."""
        candidat, n = nom, 2
        while candidat in existants:
            candidat = '{}_{}'.format(nom, n)
            n += 1
        return candidat

    def geocoder(self):
        layer = self._couche_courante()
        if layer is None:
            QtWidgets.QMessageBox.warning(
                self, 'QBano_AGAM', 'Aucune couche sélectionnée.')
            return

        champadresse = self._champadresse.currentText()
        champcp = self._champcp.currentText()
        champinsee = self._champinsee.currentText()
        champville = self._champville.currentText()
        if not champadresse:
            QtWidgets.QMessageBox.warning(
                self, 'QBano_AGAM', "Choisissez le champ contenant l'adresse.")
            return

        # Couche de sortie : champs d'origine + 3 champs BAN
        existants = {f.name() for f in layer.fields()}
        noms_ban = [self._nom_libre(n, existants)
                    for n in ('adresse_trouvee', 'score', 'type')]
        champs = [QgsField(f) for f in layer.fields()]
        champs.append(QgsField(noms_ban[0], QMetaType.Type.QString))
        champs.append(QgsField(noms_ban[1], QMetaType.Type.Double))
        champs.append(QgsField(noms_ban[2], QMetaType.Type.QString))

        vl = QgsVectorLayer('Point?crs=EPSG:4326', 'temporary_points', 'memory')
        pr = vl.dataProvider()
        pr.addAttributes(champs)
        vl.updateFields()

        self._progression.setMinimum(0)
        self._progression.setMaximum(max(layer.featureCount(), 1))
        self._progression.setValue(0)
        self._geocoder.setEnabled(False)
        self._statut.setText('Géocodage en cours…')

        nouvelles = []
        localisees = 0
        try:
            for j, src in enumerate(layer.getFeatures(), start=1):
                self._progression.setValue(j)
                QtWidgets.QApplication.processEvents()

                adresse = _texte(src[champadresse])
                trouve = {}
                if adresse:
                    trouve = self.coordonnees(
                        adresse,
                        _texte(src[champcp]) if champcp else '',
                        _texte(src[champinsee]) if champinsee else '',
                        _texte(src[champville]) if champville else '')

                fet = QgsFeature(vl.fields())
                attributs = list(src.attributes())
                if trouve:
                    localisees += 1
                    fet.setGeometry(QgsGeometry.fromPointXY(
                        QgsPointXY(trouve['lon'], trouve['lat'])))
                    attributs += [trouve['adresse'], trouve['score'], trouve['type']]
                else:
                    attributs += ['', 0.0, 'empty' if not adresse else 'notfound']
                fet.setAttributes(attributs)
                nouvelles.append(fet)
        except ban.ErreurReseau as e:
            self._statut.setText('Géocodage interrompu : erreur de connexion.')
            QtWidgets.QMessageBox.critical(
                self, 'QBano_AGAM', 'Erreur de connexion internet : {}'.format(e))
            return
        finally:
            self._geocoder.setEnabled(True)

        pr.addFeatures(nouvelles)
        vl.updateExtents()
        QgsProject.instance().addMapLayer(vl)
        self._statut.setText(
            '{} adresse(s) localisée(s) sur {}. Couche « {} » ajoutée au projet.'.format(
                localisees, len(nouvelles), vl.name()))

    def coordonnees(self, adresse, cp, insee, ville):
        """Interroge la BAN. Retourne {} si aucune adresse n'est trouvée."""
        feature = ban.search(_sans_accents(adresse), postcode=cp,
                             citycode=insee, city=ville)
        if feature is None:
            return {}
        props = feature['properties']
        lon, lat = feature['geometry']['coordinates'][:2]
        return {
            'adresse': props.get('label', ''),
            'lon': lon,
            'lat': lat,
            'score': float(props.get('score', 0)),
            'type': props.get('type', ''),
        }
