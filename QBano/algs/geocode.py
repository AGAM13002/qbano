# -*- coding: utf-8 -*-
"""
Algorithme Processing « Géocodage » : adresse -> point, via la BAN.

L'adresse à géocoder est fournie par une expression (colonne ou concaténation
de colonnes). Il est possible de restreindre la recherche à un code INSEE.
"""
__author__ = 'JB Desbas - Quartier libre'
__date__ = '2018-08-27'
__copyright__ = '(C) 2018 by JB Desbas - Quartier libre'

from time import sleep

from qgis.PyQt.QtCore import QCoreApplication, QMetaType
from qgis.core import (QgsCoordinateReferenceSystem, QgsExpression,
                       QgsFeatureSink, QgsField, QgsGeometry, QgsPointXY,
                       QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource, QgsWkbTypes)

from .. import ban

PAUSE = 0.05  # secondes entre deux requêtes (quota de l'API)


class Geocode(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    INSEE_COM = 'INSEE_COM'
    ADRESSE = 'ADRESSE'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Geocode()

    def name(self):
        return 'geocode'

    def displayName(self):
        return self.tr('Géocodage')

    def group(self):
        return self.tr('Géocodage')

    def groupId(self):
        return 'geocode'

    def shortHelpString(self):
        return self.tr(
            """Récupérer les coordonnées géographiques d'une adresse depuis la BAN grâce à l'API de géocodage de la Géoplateforme.
        <p>Il est possible de spécifier le code INSEE de l'adresse.
        <dl><h3>Champs retournés</h3>
        <dt>ban_label</dt>
        <dd>Adresse trouvée dans la BAN</dd>
        <dt>ban_citycode</dt>
        <dd>Code INSEE de la commune</dd>
        <dt>ban_score</dt>
        <dd>Le score de correspondance (0 à 1)</dd>
        <dt>ban_type</dt>
        <dd>La précision du point (housenumber > street > municipality)</dd>
        </dl>
        <p>La géométrie de sortie est en Lambert-93 (EPSG:2154).
        """)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT, self.tr('Couche en entrée'), [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterExpression(
            self.ADRESSE, self.tr('Adresse'), defaultValue='NULL',
            parentLayerParameterName=self.INPUT, optional=False))
        self.addParameter(QgsProcessingParameterExpression(
            self.INSEE_COM, self.tr('Code INSEE'), defaultValue='NULL',
            parentLayerParameterName=self.INPUT, optional=True))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, self.tr('Géocodage'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        fields = source.fields()
        for nom, type_, kwargs in (
                ('ban_label', QMetaType.Type.QString, {'len': 255}),
                ('ban_citycode', QMetaType.Type.QString, {'len': 10}),
                ('ban_score', QMetaType.Type.Double, {'len': 10, 'prec': 5}),
                ('ban_type', QMetaType.Type.QString, {'len': 20})):
            if not fields.append(QgsField(nom, type_, **kwargs)):
                feedback.reportError(
                    "Le champ {} existe déjà, son contenu sera remplacé".format(nom))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields,
            QgsWkbTypes.Point, QgsCoordinateReferenceSystem('EPSG:2154'))
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        adresse_expr = QgsExpression(self.parameterAsExpression(parameters, self.ADRESSE, context))
        citycode_expr = QgsExpression(self.parameterAsExpression(parameters, self.INSEE_COM, context))
        expr_context = self.createExpressionContext(parameters, context, source)
        adresse_expr.prepare(expr_context)
        citycode_expr.prepare(expr_context)

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        for current, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            expr_context.setFeature(feature)
            adresse = adresse_expr.evaluate(expr_context)
            citycode = citycode_expr.evaluate(expr_context)

            attr = feature.attributes()
            attr += [None] * (fields.count() - len(attr))
            feature.setFields(fields)
            feature.setAttributes(attr)

            if adresse:
                try:
                    reponse = ban.search(str(adresse),
                                         citycode=str(citycode) if citycode else None)
                except ban.ErreurReseau as e:
                    raise QgsProcessingException('Erreur de connexion à la BAN : {}'.format(e))
                if reponse:
                    props = reponse['properties']
                    feature.setAttribute('ban_label', props.get('label', ''))
                    feature.setAttribute('ban_citycode', props.get('citycode', ''))
                    feature.setAttribute('ban_score', props.get('score'))
                    feature.setAttribute('ban_type', props.get('type', ''))
                    feature.setGeometry(QgsGeometry.fromPointXY(
                        QgsPointXY(props.get('x'), props.get('y'))))
                sleep(PAUSE)

            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}
