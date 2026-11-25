# -*- coding: utf-8 -*-
"""
QBano - contenu de l'onglet « Documentation » de la boîte de dialogue.

Licence : GNU GPL v2 ou ultérieure.
"""

DOCUMENTATION_HTML = """
<h2>QBano - géocodage avec la Base Adresse Nationale</h2>
<p>QBano transforme des adresses (fichier CSV, Excel ou table de couche) en points
sur la carte, grâce au service de géocodage de la Géoplateforme (BAN).
Une connexion internet est nécessaire.</p>

<h3>Utilisation pas à pas</h3>
<ol>
  <li>Ouvrez votre fichier d'adresses dans QGIS (par exemple via
      <i>Couche &gt; Ajouter une couche &gt; Ajouter une couche de texte
      délimité</i>, en choisissant « Aucune géométrie »).</li>
  <li>Dans l'onglet <b>Géocodage</b>, cliquez sur <b>Recharger les couches du
      projet</b>, puis choisissez la couche à géocoder.</li>
  <li>Choisissez le <b>champ adresse</b>. L'adresse doit être contenue dans une
      seule colonne (numéro, rue, code postal, ville).</li>
  <li>Facultatif : indiquez les champs <b>code postal</b>, <b>code INSEE</b>
      ou <b>ville</b> si ces informations sont dans des colonnes séparées.
      Elles servent à affiner la recherche.</li>
  <li>Cliquez sur <b>Géocoder</b>. Une couche de points temporaire est ajoutée
      au projet.</li>
</ol>

<h3>Couche obtenue</h3>
<p>La couche de points temporaire est en WGS84 (EPSG:4326). Elle reprend tous
les champs de la couche d'origine et ajoute trois colonnes :</p>
<table border="1" cellpadding="4" cellspacing="0">
  <tr><th>Colonne</th><th>Contenu</th></tr>
  <tr><td><code>adresse_trouvee</code></td><td>Adresse telle qu'elle figure dans la BAN</td></tr>
  <tr><td><code>score</code></td><td>Fiabilité de la correspondance, de 0 à 1 (1 = meilleure note)</td></tr>
  <tr><td><code>type</code></td><td>Précision du résultat renvoyée par la BAN (<code>housenumber</code> &gt; <code>street</code> &gt; <code>municipality</code>), ou <code>empty</code> / <code>notfound</code> (voir ci-dessous)</td></tr>
</table>
<p>Si un champ de même nom existe déjà dans votre couche, un numéro est ajouté
(par exemple <code>score_2</code>) pour ne rien écraser.</p>

<h3>Interpréter le score</h3>
<p>À partir de <b>0,5</b>, la localisation est généralement fiable. En dessous,
vérifiez l'adresse trouvée avant de l'utiliser.</p>

<h3>Cas particuliers</h3>
<ul>
  <li><b>Adresse vide</b> : aucun point n'est créé, <code>type</code> vaut
      <code>empty</code>.</li>
  <li><b>Adresse introuvable</b> : aucun point n'est créé, <code>type</code> vaut
      <code>notfound</code>, <code>score</code> vaut 0.</li>
  <li><b>Erreur de connexion</b> : un message s'affiche et le géocodage
      s'arrête, sans ajouter de couche.</li>
  <li>Les accents et la ponctuation de l'adresse sont nettoyés avant l'envoi.</li>
</ul>

<h3>Algorithmes de la boîte à outils Processing</h3>
<p>QBano ajoute deux algorithmes dans le groupe <b>Géocodage</b> de la boîte à
outils Processing, utilisables dans le modeleur graphique et par lots :</p>
<ul>
  <li><b>Géocodage</b> : l'adresse est fournie par une expression (une colonne
      ou une concaténation de colonnes), avec un code INSEE facultatif. Il ajoute
      les champs <code>ban_label</code>, <code>ban_citycode</code>,
      <code>ban_score</code> et <code>ban_type</code>. La sortie est en
      Lambert-93 (EPSG:2154).</li>
  <li><b>Géocodage inverse</b> : retrouve l'adresse la plus proche d'un point.</li>
</ul>

<h3>Bon à savoir</h3>
<ul>
  <li>Les requêtes passent par le réseau de QGIS : le proxy configuré dans QGIS
      est respecté.</li>
  <li>En cas de dépassement de quota du service, QBano patiente et réessaie
      jusqu'à trois fois.</li>
  <li>Le résultat dépend de la qualité de vos adresses : vérifiez toujours les
      scores faibles.</li>
</ul>

<h3>À propos</h3>
<p>Source, signalement d'anomalies et suggestions :
<a href="https://github.com/AGAM13002/qbano">github.com/AGAM13002/qbano</a>
(onglet <i>Issues</i>).<br/>
Licence : GNU GPL v2 ou ultérieure.</p>
"""
