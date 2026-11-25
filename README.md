# QBano_AGAM

QBano_AGAM permet de géolocaliser vos adresses issues d'un fichier excel ou CSV. Il se sert de la base BAN (Base Adresse Nationale).

QBano_AGAM est un fork du plugin QBan(o) de CREASIG, distribué sous la même licence (GPL v2 ou ultérieure).

Nécessite QGIS 3.44 ou supérieur. Le fichier des adresses doit être ouvert dans QGIS. L'adresse doit être contenue dans une seule colonne (numero, rue, code postal, ville). Une fois la géolocalisation effectuée, une colonne "score" permet de connaitre la fiabilité de l'adresse, 1 étant la meilleure note (à partir de 0,5, la localisation est fiable).

V 2.0 - Nouvelle adresse de l'API : https://data.geopf.fr/geocodage (l'ancienne api-adresse.data.gouv.fr est dépréciée), requêtes via le réseau de QGIS (proxy pris en compte), algorithmes Processing Géocodage et Géocodage inverse enregistrés. Compatibilité QGIS 3.44 et versions suivantes (API `qgis.PyQt`, `QMetaType`), suppression des dépendances externes (simplejson, requests), nettoyage du projet. Une adresse vide ne génère plus de point en (0,0) : la géométrie reste vide et le type vaut `empty` (`notfound` si la BAN ne trouve rien).

V 1.1 - Suppression automatique des guillemets, virgule, point virgule point et double point dans le champ adresse.

V 1.0 - Modification de la requête auprès de l'API BAN.

V 0.3 – Ajout de la colonne de la précision de l’adresse (colonne type); Indication lorsque la connexion internet n'existe pas; Pas de message d'erreur quand le champ adresse est vide, tout le traitement est effectué.

V 0.2 –  Ajout de la colonne score.
