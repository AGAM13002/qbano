# -*- coding: utf-8 -*-
"""
Accès à l'API de géocodage de la Base Adresse Nationale (Géoplateforme IGN).

Les requêtes passent par le gestionnaire réseau de QGIS : le proxy et les
certificats configurés dans QGIS sont donc respectés.
"""
import json
import time
import urllib.parse

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import QgsBlockingNetworkRequest

# L'ancienne adresse (api-adresse.data.gouv.fr) est dépréciée.
BAN_BASE_URL = 'https://data.geopf.fr/geocodage'
BAN_SEARCH_URL = BAN_BASE_URL + '/search'
BAN_REVERSE_URL = BAN_BASE_URL + '/reverse'
GEO_COMMUNES_URL = 'https://geo.api.gouv.fr/communes'

TIMEOUT_MS = 30000
MAX_TENTATIVES = 3
USER_AGENT = b'qbano-QGIS-plugin'


class ErreurReseau(Exception):
    """L'API n'est pas joignable ou a renvoyé une erreur."""


def get_json(url, params=None):
    """GET + décodage JSON. Lève ErreurReseau en cas d'échec réseau/HTTP."""
    if params:
        url = '{}?{}'.format(url, urllib.parse.urlencode(params))
    derniere = None
    for tentative in range(MAX_TENTATIVES):
        requete = QNetworkRequest(QUrl(url))
        requete.setHeader(QNetworkRequest.UserAgentHeader, USER_AGENT)
        requete.setTransferTimeout(TIMEOUT_MS)
        bloquante = QgsBlockingNetworkRequest()
        code = bloquante.get(requete, forceRefresh=True)
        if code == QgsBlockingNetworkRequest.NoError:
            try:
                return json.loads(bytes(bloquante.reply().content()).decode('utf-8'))
            except ValueError as e:
                raise ErreurReseau('réponse illisible : {}'.format(e))
        derniere = bloquante.errorMessage()
        statut = bloquante.reply().attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if statut == 429 and tentative < MAX_TENTATIVES - 1:
            time.sleep(1.0 + tentative)  # quota dépassé : on patiente et on réessaie
            continue
        break
    raise ErreurReseau(derniere or 'erreur inconnue')


def _premiere_feature(data):
    features = (data or {}).get('features') or []
    return features[0] if features else None


def search(query, **filtres):
    """Meilleur résultat pour une adresse, ou None.

    filtres : postcode, citycode, city... (valeurs vides ignorées).
    """
    params = {'q': query, 'limit': 1}
    params.update({k: v for k, v in filtres.items() if v})
    return _premiere_feature(get_json(BAN_SEARCH_URL, params))


def reverse(lon, lat):
    """Adresse la plus proche d'un point WGS84, ou None."""
    return _premiere_feature(get_json(BAN_REVERSE_URL, {'lon': lon, 'lat': lat}))


def commune(lon, lat):
    """Commune contenant un point WGS84 (repli du géocodage inverse), ou None."""
    data = get_json(GEO_COMMUNES_URL, {'lon': lon, 'lat': lat})
    return data[0] if data else None
