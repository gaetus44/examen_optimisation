# 🧬 AI Platformer - Genetic Algorithm

Un projet d'intelligence artificielle qui apprend à résoudre un niveau de jeu de plateforme par évolution, sans aucune intervention humaine.

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)
![Pygame](https://img.shields.io/badge/Library-Pygame-yellow?style=flat&logo=pygame)

## 📝 Description

Ce projet simule l'évolution d'une population d'agents autonomes. Au départ, les agents bougent de manière totalement aléatoire. Génération après génération, grâce aux principes de la sélection naturelle (sélection, croisement, mutation), ils apprennent à sauter, éviter les obstacles et atteindre la zone rouge le plus vite possible.

Le moteur physique est codé "from scratch" et l'IA utilise un algorithme génétique optimisé pour les séquences temporelles.

## 🚀 Fonctionnalités Clés

### 🧠 Algorithme Génétique Avancé
Ce n'est pas un simple "brute force". L'algorithme utilise des techniques spécifiques pour converger rapidement :
* **Sélection par Roulette Exponentielle** : Les meilleurs agents ont une probabilité quadratique ($fitness^2$) d'être choisis, favorisant l'élite tout en gardant une diversité.
* **Mutation "Shift" (Temporelle)** : Une mutation intelligente capable de décaler les séquences d'actions (agir une frame plus tôt ou plus tard) pour affiner le timing des sauts.
* **Élitisme** : Les meilleurs champions sont clonés directement dans la génération suivante pour éviter la régression.

### 🕹️ Moteur Physique (Custom)
* Gestion de l'inertie et de la gravité.
* Collisions précises avec les tuiles.
* Système de "Ticks" fixe pour garantir le déterminisme de l'IA.

## 🛠️ Installation

1. **Cloner le projet**
   ```bash
   git clone [https://github.com/ton-pseudo/nom-du-repo.git](https://github.com/ton-pseudo/nom-du-repo.git)
   cd nom-du-repo