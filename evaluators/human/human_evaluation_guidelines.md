# Human Evaluation Guidelines
## Togo AI Benchmark
### Version 1.0

---

# 1. Objectif du Benchmark

Le Togo AI Benchmark évalue la capacité des modèles d’intelligence artificielle à comprendre, raisonner et répondre correctement à des questions liées au contexte togolais.

Le benchmark se concentre particulièrement sur :

- la santé publique,
- le droit et la justice,
- l’économie informelle,
- les réalités socio-économiques locales,
- et la compréhension concrète du terrain togolais.

L’objectif n’est PAS d’évaluer :
- le style littéraire,
- la créativité,
- ou l’élégance rédactionnelle.

L’objectif principal est d’évaluer :
- la fiabilité,
- l’exactitude,
- le réalisme terrain,
- l’honnêteté intellectuelle,
- et l’utilité concrète des réponses.

---

# 2. Rôle de l’Évaluateur Humain

L’évaluateur humain agit comme :
- un juge indépendant,
- un validateur terrain,
- et une référence méthodologique.

L’évaluateur doit appliquer les critères de manière :
- cohérente,
- rigoureuse,
- neutre,
- et reproductible.

---

# 3. Principes Fondamentaux

## 3.1 Être sévère mais juste

Une réponse fluide ou bien rédigée ne doit PAS recevoir une bonne note si :
- elle est incorrecte,
- inventée,
- ou déconnectée des réalités togolaises.

---

## 3.2 Évaluer uniquement ce qui est écrit

L’évaluateur ne doit PAS :
- compléter mentalement une réponse,
- corriger implicitement une erreur,
- ou supposer que le modèle “voulait dire autre chose”.

Seul le contenu explicitement présent doit être évalué.

---

## 3.3 Ne pas favoriser les réponses longues

Une réponse longue n’est pas nécessairement meilleure.

Une réponse concise mais exacte peut recevoir une excellente note.

---

## 3.4 Valoriser l’honnêteté intellectuelle

Une IA qui reconnaît ses limites ou son incertitude doit être valorisée lorsque :
- les données sont rares,
- les informations sont difficiles à vérifier,
- ou le sujet est ambigu.

---

# 4. Critères d’Évaluation

---

# C1 — Exactitude de la Source de Vérité
## Coefficient : 3

### Ce qu’on mesure

- Exactitude factuelle
- Conformité aux réalités togolaises
- Exactitude des lois, institutions, protocoles ou statistiques mentionnés

### Exemple de bonne réponse

- Référence correcte à une institution réellement existante
- Mention correcte d’un programme de santé togolais
- Description fidèle d’un mécanisme administratif réel

### Exemple de mauvaise réponse

- Loi inexistante
- Faux ministère
- Statistique inventée
- Procédure juridique fictive

### Échelle

| Score | Signification |
|---|---|
| 5 | Parfaitement exact et contextualisé |
| 4 | Quelques imprécisions mineures |
| 3 | Partiellement exact |
| 2 | Plusieurs erreurs importantes |
| 1 | Majoritairement incorrect |
| 0 | Aucune information correcte |

---

# C2 — Réalisme du Terrain Togolais
## Coefficient : 2

### Ce qu’on mesure

La capacité de l’IA à comprendre :
- les réalités locales,
- les contraintes concrètes,
- les dynamiques sociales et économiques du Togo.

### Exemples de réalités terrain

- Zémidjans
- Tontines
- Ruptures d’intrants médicaux
- Informalité administrative
- Contraintes des USP
- Réalités des marchés informels

### Mauvais signal

Réponse trop :
- théorique,
- occidentale,
- abstraite,
- ou hors-sol.

### Échelle

| Score | Signification |
|---|---|
| 5 | Très fortement ancré dans les réalités togolaises |
| 4 | Globalement réaliste |
| 3 | Mélange réalisme/généricité |
| 2 | Trop théorique |
| 1 | Très faible compréhension locale |
| 0 | Complètement déconnecté du terrain |

---

# C3 — Actionnabilité et Clarté
## Coefficient : 1

### Ce qu’on mesure

La capacité de la réponse à être :
- utile,
- claire,
- compréhensible,
- et exploitable concrètement.

### Bonne réponse

Le lecteur comprend :
- quoi faire,
- quoi éviter,
- ou quelle décision prendre.

### Mauvaise réponse

Réponse :
- vague,
- confuse,
- inutilement compliquée,
- ou purement académique.

### Échelle

| Score | Signification |
|---|---|
| 5 | Très clair et immédiatement exploitable |
| 4 | Utile et compréhensible |
| 3 | Modérément utile |
| 2 | Trop théorique |
| 1 | Très vague |
| 0 | Inutilisable |

---

# C4 — Lucidité et Gestion des Limites
## Coefficient : 1

### Ce qu’on mesure

La capacité du modèle à :
- reconnaître l’incertitude,
- reconnaître les limites des données,
- éviter les affirmations excessivement confiantes.

### Bonne réponse

Le modèle précise par exemple :
- que certaines données sont limitées,
- anciennes,
- difficiles à vérifier,
- ou non disponibles.

### Mauvaise réponse

Le modèle :
- affirme des chiffres précis sans source,
- parle avec certitude sur des sujets incertains,
- invente une précision artificielle.

### Échelle

| Score | Signification |
|---|---|
| 5 | Excellente gestion de l’incertitude |
| 4 | Bonne reconnaissance des limites |
| 3 | Reconnaît partiellement les limites |
| 2 | Plusieurs affirmations excessives |
| 1 | Très forte surconfiance |
| 0 | Aucune nuance ou recul critique |

---

# C5 — Sévérité des Hallucinations
## Coefficient : 3

### Ce qu’on mesure

La présence :
- d’informations inventées,
- de lois fictives,
- de statistiques fabriquées,
- d’institutions inexistantes,
- ou de mécanismes imaginaires.

### Important

Plus la note est élevée :
plus le modèle est honnête.

### Exemples graves

- Faux décret
- Faux programme gouvernemental
- Faux article de loi
- Statistique totalement inventée

### Échelle

| Score | Signification |
|---|---|
| 5 | Aucune hallucination détectée |
| 4 | Très légère extrapolation |
| 3 | Une hallucination isolée |
| 2 | Hallucinations multiples |
| 1 | Hallucinations graves |
| 0 | Réponse fondamentalement fabriquée |

---

# 5. Procédure d’Évaluation

Pour chaque réponse :

1. Lire attentivement la question
2. Lire entièrement la réponse générée
3. Évaluer séparément C1 à C5
4. Justifier brièvement les notes
5. Éviter les biais personnels ou politiques
6. Sauvegarder les scores dans le template officiel

---

# 6. Neutralité et Biais

Les évaluateurs doivent éviter :
- les préférences politiques,
- les jugements idéologiques,
- les préférences stylistiques,
- les biais culturels personnels.

Le benchmark évalue :
- la qualité informationnelle,
- pas l’opinion personnelle de l’évaluateur.

---

# 7. Confidentialité

Les réponses évaluées :
- ne doivent pas être partagées publiquement,
- ni modifiées pendant l’évaluation.

---

# 8. Conclusion

Le Togo AI Benchmark cherche à construire une évaluation rigoureuse des capacités réelles des modèles d’IA dans le contexte togolais.

La qualité des évaluations humaines est essentielle pour :
- la crédibilité scientifique,
- la reproductibilité,
- et la fiabilité globale du benchmark.