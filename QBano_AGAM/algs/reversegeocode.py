# -*- coding: utf-8 -*-
"""Algorithme Processing « Géocodage inverse » : point -> adresse, via la BAN."""
__author__ = 'JB Desbas - Quartier libre'
__date__ = '2018-08-27'
__copyright__ = '(C) 2018 by JB Desbas - Quartier libre'

from time import sleep

from qgis.PyQt.QtCore import QCoreApplication, QMetaType
from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsFeatureSink, QgsField, QgsProcessing,
                       QgsProcessingAlgorithm, QgsProcessingException,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource)

from .. import ban

PAUSE = 0.05  # secondes entre deux requêtes (quota de l'API)


class ReverseGeocode(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ReverseGeocode()

    def name(self):
        return 'reversegeocode'

    def displayName(self):
        return self.tr('Géocodage inverse')

    def group(self):
        return self.tr('Géocodage')

    def groupId(self):
        return 'geocode'

    def shortHelpString(self):
        return self.tr(
            "Retrouver l'adresse d'un point depuis la BAN grâce à l'API de géocodage de la Géoplateforme."
            "<p>Si aucune adresse n'est trouvée, seule la commune est renseignée.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT, self.tr('Couche en entrée'), [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, self.tr('Géocodage inverse'), QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        fields = source.fields()
        n_source = fields.count()
        fields.append(QgsField('com_insee', QMetaType.Type.QString, len=6))
        fields.append(QgsField('com_name', QMetaType.Type.QString, len=100))
        fields.append(QgsField('street', QMetaType.Type.QString, len=100))
        fields.append(QgsField('housenumber', QMetaType.Type.QString, len=10))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields,
            source.wkbType(), source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(source.sourceCrs(), wgs84, context.transformContext())

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        for current, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            attr = feature.attributes()[:n_source]
            attr += [None] * (fields.count() - n_source)
            geom = feature.geometry()
            if not geom.isNull() and not geom.isEmpty():
                point = transform.transform(geom.asPoint())
                try:
                    reponse = ban.reverse(point.x(), point.y())
                    commune = None if reponse else ban.commune(point.x(), point.y())
                except ban.ErreurReseau as e:
                    raise QgsProcessingException('Erreur de connexion à la BAN : {}'.format(e))
                if reponse:
                    props = reponse['properties']
                    attr[n_source:] = [props.get('citycode', ''), props.get('city', ''),
                                       props.get('street', ''), props.get('housenumber', '')]
                elif commune:  # pas d'adresse : on se replie sur la commune
                    attr[n_source:] = [commune.get('code', ''), commune.get('nom', ''), '', '']
                sleep(PAUSE)

            feature.setFields(fields)
            feature.setAttributes(attr)
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}
